import { createHash } from "node:crypto";
import { readdir, readFile, stat } from "node:fs/promises";
import { dirname, join, relative, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const root = resolve(dirname(fileURLToPath(import.meta.url)), "..");
const excludedDirectories = new Set([".git", "artifacts", "data", "dist", "logs", "node_modules"]);
const excludedFiles = new Set([".env"]);
const required = [
  "package.json",
  "MODULE.bazel",
  "BUILD.bazel",
  "config/branch-lock.json",
  "config/channel-map.json",
  "src/server.js",
  "src/runtime.js",
  "src/mapping.js",
  "src/security.js",
  "scripts/Install-Z8ParticleBridge.ps1",
  "scripts/Start-Z8ParticleBridge.ps1",
  "scripts/Test-Z8ParticleBridge.ps1",
  "scripts/Collect-Z8Evidence.ps1",
  "scripts/Build-Z8AndroidAdapter.ps1",
  "scripts/Invoke-Z8Event.ps1",
  "scripts/Set-Z8BridgeMode.ps1",
  "scripts/Set-Z8Runtime.ps1",
  "scripts/Package-Z8ParticleBridge.ps1",
  "android/evidence-contract.json",
  "android/app/src/main/AndroidManifest.xml",
  "android/app/src/main/java/com/mrliou/z8bridge/Z8EventReceiver.java",
  "docs/MRL_Z8_ParticleBridge_v0.4_Combined_Delivery_Report.md",
  "docs/DELIVERY_AUDIT.json",
];

async function walk(directory) {
  const results = [];
  for (const entry of await readdir(directory, { withFileTypes: true })) {
    if (entry.isDirectory() && excludedDirectories.has(entry.name)) continue;
    if (entry.isFile() && excludedFiles.has(entry.name)) continue;
    const path = join(directory, entry.name);
    if (entry.isDirectory()) results.push(...(await walk(path)));
    if (entry.isFile()) results.push(path);
  }
  return results;
}

function hash(content) {
  return createHash("sha256").update(content).digest("hex");
}

const files = (await walk(root)).sort();
const relFiles = files.map((path) => relative(root, path).replaceAll("\\", "/"));
const sourcePayloadFiles = relFiles.filter((path) => path !== "MANIFEST.sha256");
const packageManifestPresent = relFiles.includes("MANIFEST.sha256");
const missing = required.filter((path) => !relFiles.includes(path));
const empty = [];
const placeholders = [];
const secretCandidates = [];
const manifest = [];

for (const path of files) {
  const info = await stat(path);
  const rel = relative(root, path).replaceAll("\\", "/");
  if (info.size === 0) empty.push(rel);
  const content = await readFile(path);
  const text = content.toString("utf8");
  if (rel !== "scripts/audit.mjs" && /\b(?:TODO|TBD|FIXME)\b|<PLACEHOLDER>/i.test(text)) placeholders.push(rel);
  if (/Bearer[ \t]+[A-Za-z0-9._-]{24,}|(?:secret|token)[A-Za-z0-9_-]*[ \t]*[=:][ \t]*["'][A-Za-z0-9._-]{24,}["']/i.test(text)) {
    secretCandidates.push(rel);
  }
  manifest.push({ path: rel, bytes: info.size, sha256: hash(content) });
}

const packageJson = JSON.parse(await readFile(join(root, "package.json"), "utf8"));
const deliveryAudit = JSON.parse(await readFile(join(root, "docs", "DELIVERY_AUDIT.json"), "utf8"));
const expectedFiles = [...deliveryAudit.file_list].sort();
const missingExpected = expectedFiles.filter((path) => !sourcePayloadFiles.includes(path));
const unexpectedExpected = sourcePayloadFiles.filter((path) => !expectedFiles.includes(path));
const duplicateExpected = expectedFiles.filter((path, index) => expectedFiles.indexOf(path) !== index);
const mappingSource = [
  await readFile(join(root, "src", "mapping.js"), "utf8"),
  await readFile(join(root, "src", "constants.js"), "utf8"),
  await readFile(join(root, "config", "channel-map.json"), "utf8"),
].join("\n");
const scope = JSON.parse(await readFile(join(root, "config", "branch-lock.json"), "utf8"));
const assertions = {
  no_runtime_dependencies: !packageJson.dependencies && !packageJson.devDependencies,
  xiaozhi_mapping_present: mappingSource.includes("z8.xiaozhi.voice") || mappingSource.includes("PARTICLE_TYPES.XIAOZHI_VOICE"),
  weiliao_mapping_present: mappingSource.includes("z8.line.text") || mappingSource.includes("PARTICLE_TYPES.LINE_TEXT"),
  additive_only: scope.policy === "additive-only",
  default_dry_run: scope.runtime?.mode_default === "dry-run",
  no_missing_files: missing.length === 0,
  no_empty_files: empty.length === 0,
  no_placeholders: placeholders.length === 0,
  no_secret_candidates: secretCandidates.length === 0,
  expected_file_count_matches: sourcePayloadFiles.length === deliveryAudit.expected.source_files,
  expected_file_list_matches:
    missingExpected.length === 0 && unexpectedExpected.length === 0 && duplicateExpected.length === 0,
};

const failed = Object.entries(assertions).filter(([, passed]) => !passed).map(([name]) => name);
const aggregate = hash(manifest.map((entry) => `${entry.sha256}  ${entry.path}`).join("\n"));
const report = {
  project: "MRL_Z8_ParticleBridge",
  version: packageJson.version,
  files: manifest.length,
  source_payload_files: sourcePayloadFiles.length,
  package_manifest_present: packageManifestPresent,
  aggregate_sha256: aggregate,
  assertions,
  missing,
  empty,
  placeholders,
  secret_candidates: secretCandidates,
  requested_vs_generated: {
    expected_files: expectedFiles.length,
    generated_files: sourcePayloadFiles.length,
    missing_files: missingExpected,
    unexpected_files: unexpectedExpected,
    duplicate_expected_files: duplicateExpected,
    coverage_percent: expectedFiles.length === 0
      ? 0
      : Number((((expectedFiles.length - missingExpected.length) / expectedFiles.length) * 100).toFixed(2)),
  },
};

console.log(JSON.stringify(report, null, 2));
if (failed.length > 0) {
  console.error(`Audit failed: ${failed.join(", ")}`);
  process.exitCode = 1;
}
