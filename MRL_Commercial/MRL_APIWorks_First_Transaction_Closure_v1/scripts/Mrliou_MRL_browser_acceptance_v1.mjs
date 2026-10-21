#!/usr/bin/env node
/**
 * Render and independently verify desktop/mobile APIWorks evidence-entry proof.
 *
 * origin_signature: MrLiouWord
 * Implementation assistance: OpenAI Codex, directed by Mrliou.
 */

import { createHash } from "node:crypto";
import {
  existsSync,
  mkdirSync,
  readFileSync,
  readdirSync,
  statSync,
  writeFileSync,
} from "node:fs";
import { isAbsolute, relative, resolve } from "node:path";
import { pathToFileURL } from "node:url";

const EXPECTED = [
  "BROWSER_ACCEPTANCE.json",
  "Expected_File_List.txt",
  "SHA256SUMS.txt",
  "desktop.html",
  "desktop.png",
  "mobile.html",
  "mobile.png",
];
const PROFILES = [
  { name: "desktop", width: 1365, height: 980, isMobile: false },
  { name: "mobile", width: 390, height: 844, isMobile: true },
];
const REQUIRED_TEXT = [
  "MRL APIWorks｜可驗證入口",
  "這個產品實際交付什麼",
  "內容交叉比對",
  "五層證據與邊界",
  "自行重跑",
  "尚待真實輸入",
];

function sha256(data) {
  return createHash("sha256").update(data).digest("hex");
}

function filesUnder(root) {
  const found = [];
  function visit(directory) {
    for (const name of readdirSync(directory).sort()) {
      const path = resolve(directory, name);
      const info = statSync(path);
      if (info.isDirectory()) visit(path);
      else if (info.isFile()) found.push(relative(root, path).replaceAll("\\", "/"));
      else throw new Error(`unsupported browser-evidence entry: ${path}`);
    }
  }
  visit(root);
  return found;
}

function pngDimensions(path) {
  const data = readFileSync(path);
  const signature = "89504e470d0a1a0a";
  if (data.length < 24 || data.subarray(0, 8).toString("hex") !== signature) {
    throw new Error(`invalid PNG: ${path}`);
  }
  return { width: data.readUInt32BE(16), height: data.readUInt32BE(20) };
}

function safeLocalLinks(input, hrefs) {
  const root = resolve(input);
  const missing = [];
  const unsafe = [];
  for (const href of hrefs) {
    if (/^[a-z]+:/i.test(href) || href.startsWith("#")) {
      unsafe.push(href);
      continue;
    }
    const target = resolve(root, href);
    if (target !== root && !target.startsWith(root + "/")) unsafe.push(href);
    else if (!existsSync(target) || !statSync(target).isFile()) missing.push(href);
  }
  return { missing, unsafe };
}

function verify(output) {
  const root = resolve(output);
  const actual = filesUnder(root);
  const expectedText = readFileSync(resolve(root, "Expected_File_List.txt"), "utf8")
    .split(/\r?\n/)
    .filter(Boolean);
  const missing = expectedText.filter((name) => !actual.includes(name));
  const extra = actual.filter((name) => !expectedText.includes(name));
  const empty = expectedText.filter((name) => statSync(resolve(root, name)).size === 0);
  const rows = new Map(
    readFileSync(resolve(root, "SHA256SUMS.txt"), "utf8")
      .split(/\r?\n/)
      .filter(Boolean)
      .map((line) => {
        const match = line.match(/^([0-9a-f]{64})  (.+)$/);
        if (!match) throw new Error(`invalid checksum row: ${line}`);
        return [match[2], match[1]];
      }),
  );
  const checksumExpected = expectedText.filter((name) => name !== "SHA256SUMS.txt");
  const checksumMissing = checksumExpected.filter((name) => !rows.has(name));
  const checksumExtra = [...rows.keys()].filter((name) => !checksumExpected.includes(name));
  const mismatch = checksumExpected.filter(
    (name) => rows.has(name) && sha256(readFileSync(resolve(root, name))) !== rows.get(name),
  );
  const receipt = JSON.parse(readFileSync(resolve(root, "BROWSER_ACCEPTANCE.json"), "utf8"));
  const semanticFailures = [];
  if (receipt.browser_gate !== "BROWSER_ACCEPTANCE_PASS") semanticFailures.push("receipt.gate");
  if (receipt.origin_signature !== "MrLiouWord") semanticFailures.push("receipt.origin");
  for (const profile of PROFILES) {
    const record = receipt.profiles?.find((item) => item.name === profile.name);
    if (!record) {
      semanticFailures.push(`profile.${profile.name}.missing`);
      continue;
    }
    const png = resolve(root, `${profile.name}.png`);
    const dom = resolve(root, `${profile.name}.html`);
    const dimensions = pngDimensions(png);
    if (dimensions.width !== profile.width || dimensions.height < profile.height) {
      semanticFailures.push(`profile.${profile.name}.dimensions`);
    }
    if (record.screenshot_sha256 !== sha256(readFileSync(png))) {
      semanticFailures.push(`profile.${profile.name}.screenshot_hash`);
    }
    if (record.dom_sha256 !== sha256(readFileSync(dom))) {
      semanticFailures.push(`profile.${profile.name}.dom_hash`);
    }
    const markup = readFileSync(dom, "utf8");
    for (const value of REQUIRED_TEXT) {
      if (!markup.includes(value)) semanticFailures.push(`profile.${profile.name}.text:${value}`);
    }
  }
  const failures = { missing, extra, empty, checksumMissing, checksumExtra, mismatch, semanticFailures };
  const passed = Object.values(failures).every((items) => items.length === 0);
  const result = {
    expected_count: expectedText.length,
    actual_count: actual.length,
    ...failures,
    browser_evidence_gate: passed ? "PASS" : "FAIL",
  };
  process.stdout.write(JSON.stringify(result, null, 2) + "\n");
  if (!passed) throw new Error("browser evidence verification failed");
  return result;
}

async function generate(input, output) {
  const source = resolve(input);
  const destination = resolve(output);
  if (!existsSync(resolve(source, "index.html"))) throw new Error("input index.html is missing");
  if (existsSync(destination)) throw new Error("output already exists");
  mkdirSync(destination, { recursive: false });
  const { default: puppeteer } = await import("puppeteer");
  const browser = await puppeteer.launch({ headless: true, args: ["--no-sandbox"] });
  const records = [];
  try {
    for (const profile of PROFILES) {
      const page = await browser.newPage();
      const errors = [];
      page.on("console", (message) => {
        if (message.type() === "error") errors.push(`console: ${message.text()}`);
      });
      page.on("pageerror", (error) => errors.push(`pageerror: ${error.message}`));
      await page.setViewport({
        width: profile.width,
        height: profile.height,
        isMobile: profile.isMobile,
        deviceScaleFactor: 1,
      });
      await page.goto(pathToFileURL(resolve(source, "index.html")).href, { waitUntil: "load" });
      const state = await page.evaluate(() => ({
        title: document.title,
        heading: document.querySelector("h1")?.textContent?.trim() ?? "",
        sectionCount: document.querySelectorAll("section").length,
        tableCount: document.querySelectorAll("table").length,
        hrefs: [...document.querySelectorAll("a")].map((item) => item.getAttribute("href") ?? ""),
        text: document.body.innerText,
        viewportWidth: window.innerWidth,
        documentWidth: document.documentElement.scrollWidth,
        cjkFontReady: document.fonts.check('16px "Noto Sans CJK TC"', "可驗證入口"),
        bodyFontFamily: getComputedStyle(document.body).fontFamily,
      }));
      const links = safeLocalLinks(source, state.hrefs);
      const requiredMissing = REQUIRED_TEXT.filter((value) => !state.text.includes(value));
      if (
        state.title !== "MRL APIWorks｜可驗證入口" ||
        state.heading !== "MRL APIWorks｜可驗證入口" ||
        state.sectionCount !== 5 ||
        state.tableCount !== 1 ||
        state.documentWidth > state.viewportWidth ||
        !state.cjkFontReady ||
        !state.bodyFontFamily.includes("Noto Sans CJK TC") ||
        errors.length ||
        links.missing.length ||
        links.unsafe.length ||
        requiredMissing.length
      ) {
        throw new Error(
          JSON.stringify({ profile: profile.name, state, errors, links, requiredMissing }),
        );
      }
      const png = resolve(destination, `${profile.name}.png`);
      const dom = resolve(destination, `${profile.name}.html`);
      await page.screenshot({ path: png, fullPage: true });
      writeFileSync(dom, await page.content(), "utf8");
      const dimensions = pngDimensions(png);
      records.push({
        name: profile.name,
        viewport: { width: profile.width, height: profile.height },
        screenshot: `${profile.name}.png`,
        screenshot_size_bytes: statSync(png).size,
        screenshot_sha256: sha256(readFileSync(png)),
        rendered_dom: `${profile.name}.html`,
        dom_size_bytes: statSync(dom).size,
        dom_sha256: sha256(readFileSync(dom)),
        rendered_dimensions: dimensions,
        section_count: state.sectionCount,
        table_count: state.tableCount,
        local_link_count: state.hrefs.length,
        missing_links: links.missing,
        unsafe_links: links.unsafe,
        console_errors: errors,
        horizontal_overflow_pixels: Math.max(0, state.documentWidth - state.viewportWidth),
        cjk_font_ready: state.cjkFontReady,
        body_font_family: state.bodyFontFamily,
      });
      await page.close();
    }
  } finally {
    await browser.close();
  }
  const receipt = {
    schema: "Mrliou_MRL_APIWorks_Browser_Acceptance_v1",
    canonical_id: "MRL_APIWorks_BYOH_Deployment_Product_v1",
    origin_signature: "MrLiouWord",
    input_index_sha256: sha256(readFileSync(resolve(source, "index.html"))),
    browser: "Chromium via locked Puppeteer dependency",
    profiles: records,
    customer_model_acceptance: "NOT_ASSERTED",
    public_deployment_acceptance: "NOT_ASSERTED",
    transaction_acceptance: "NOT_ASSERTED",
    browser_gate: "BROWSER_ACCEPTANCE_PASS",
  };
  writeFileSync(
    resolve(destination, "BROWSER_ACCEPTANCE.json"),
    JSON.stringify(receipt, null, 2) + "\n",
    "utf8",
  );
  writeFileSync(resolve(destination, "Expected_File_List.txt"), EXPECTED.join("\n") + "\n", "utf8");
  const checksumLines = EXPECTED.filter((name) => name !== "SHA256SUMS.txt").map(
    (name) => `${sha256(readFileSync(resolve(destination, name)))}  ${name}`,
  );
  writeFileSync(resolve(destination, "SHA256SUMS.txt"), checksumLines.join("\n") + "\n", "utf8");
  return verify(destination);
}

function option(name) {
  const index = process.argv.indexOf(name);
  return index >= 0 ? process.argv[index + 1] : undefined;
}

async function main() {
  const verifyOnly = option("--verify-only");
  if (verifyOnly) {
    verify(verifyOnly);
    return;
  }
  const input = option("--input");
  const output = option("--output");
  if (!input || !output || !isAbsolute(input) || !isAbsolute(output)) {
    throw new Error("use absolute --input and --output paths, or --verify-only PATH");
  }
  await generate(input, output);
}

main().catch((error) => {
  process.stderr.write(`BROWSER_ACCEPTANCE_FAIL: ${error.stack ?? error}\n`);
  process.exitCode = 1;
});
