import test from "node:test";
import assert from "node:assert/strict";
import { mkdtemp, rm } from "node:fs/promises";
import { join } from "node:path";
import { tmpdir } from "node:os";
import { buildRuntime, createHttpServer } from "../src/server.js";
import { signHmacBase64 } from "../src/security.js";

async function startFixture(t) {
  const dir = await mkdtemp(join(tmpdir(), "z8-server-test-"));
  const config = {
    host: "127.0.0.1",
    port: 0,
    mode: "dry-run",
    engine: "qwen-main",
    voiceMode: "chatgpt",
    ledgerPath: join(dir, "ledger.jsonl"),
    controlToken: "control-secret",
    deviceSharedSecret: "device-secret",
    lineChannelSecret: "line-secret",
    lineChannelAccessToken: "",
    lineApiBase: "https://api.line.me",
    qwenEndpoint: "",
    qwenModel: "qwen-main",
    museEndpoint: "",
    museModel: "meta/muse-glimmer",
    sttEndpoint: "",
    chatgptVoiceEndpoint: "",
    lineVoiceEndpoint: "",
  };
  const runtime = buildRuntime(config);
  const server = createHttpServer({ config, runtime, logger: { error() {} } });
  await new Promise((resolve, reject) => {
    server.once("error", reject);
    server.listen(0, "127.0.0.1", resolve);
  });
  const { port } = server.address();
  t.after(async () => {
    await new Promise((resolve) => server.close(resolve));
    await rm(dir, { recursive: true, force: true });
  });
  return { base: `http://127.0.0.1:${port}`, runtime };
}

test("health exposes state and dependency readiness without secret values", async (t) => {
  const { base } = await startFixture(t);
  const response = await fetch(`${base}/health`);
  const body = await response.json();
  assert.equal(response.status, 200);
  assert.equal(body.mode, "dry-run");
  assert.equal(body.dependencies.device_hmac, true);
  assert.equal(JSON.stringify(body).includes("device-secret"), false);
});

test("signed Z8 request is accepted and an invalid HMAC is rejected", async (t) => {
  const { base } = await startFixture(t);
  const raw = JSON.stringify({
    event_id: "server-wl-001",
    source: "weiliao",
    kind: "text",
    text: "server test",
    target: { type: "user", id: "U_TEST" },
  });
  const accepted = await fetch(`${base}/v1/z8/events`, {
    method: "POST",
    headers: {
      "content-type": "application/json",
      "x-mrl-signature": signHmacBase64(raw, "device-secret"),
    },
    body: raw,
  });
  assert.equal(accepted.status, 202);
  assert.equal((await accepted.json()).status, "dry-run");

  const rejected = await fetch(`${base}/v1/z8/events`, {
    method: "POST",
    headers: { "content-type": "application/json", "x-mrl-signature": "bad" },
    body: raw,
  });
  assert.equal(rejected.status, 401);
});

test("control route requires token and changes only the branch runtime", async (t) => {
  const { base, runtime } = await startFixture(t);
  const denied = await fetch(`${base}/v1/control/voice`, {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify({ voice_mode: "line" }),
  });
  assert.equal(denied.status, 401);

  const accepted = await fetch(`${base}/v1/control/voice`, {
    method: "POST",
    headers: {
      "content-type": "application/json",
      authorization: "Bearer control-secret",
    },
    body: JSON.stringify({ voice_mode: "line" }),
  });
  assert.equal(accepted.status, 200);
  assert.equal(runtime.state().voice_mode, "line");
});
