import test from "node:test";
import assert from "node:assert/strict";
import { mkdtemp, rm } from "node:fs/promises";
import { join } from "node:path";
import { tmpdir } from "node:os";
import { JsonlLedger } from "../src/ledger.js";
import { Z8BridgeRuntime } from "../src/runtime.js";

const fixedNow = () => "2026-08-11T00:00:00.000Z";

async function fixture(t, mode = "dry-run") {
  const dir = await mkdtemp(join(tmpdir(), "z8-runtime-test-"));
  t.after(() => rm(dir, { recursive: true, force: true }));
  const calls = { push: [], reply: [], complete: [], transcribe: [], synthesize: [], synthesizeLine: [] };
  const lineClient = {
    async push(to, messages) {
      calls.push.push({ to, messages });
      return { sent: true };
    },
    async reply(replyToken, messages) {
      calls.reply.push({ replyToken, messages });
      return { replied: true };
    },
  };
  const modelClient = {
    async complete(text, options) {
      calls.complete.push({ text, options });
      return { text: `答覆:${text}`, engine: options.engine, model: "test-model" };
    },
  };
  const voiceClient = {
    async transcribe(audio) {
      calls.transcribe.push(audio);
      return { text: "語音內容" };
    },
    async synthesize(text) {
      calls.synthesize.push(text);
      return { audio_url: "https://audio.example/result.mp3", duration_ms: 1000 };
    },
    async synthesizeLine(text) {
      calls.synthesizeLine.push(text);
      return { audio_url: "https://audio.example/line-result.m4a", duration_ms: 1100 };
    },
  };
  const config = { mode, engine: "qwen-main", voiceMode: "chatgpt" };
  const ledger = new JsonlLedger(join(dir, "ledger.jsonl"), { now: fixedNow });
  const runtime = new Z8BridgeRuntime({
    config,
    ledger,
    lineClient,
    modelClient,
    voiceClient,
    now: fixedNow,
  });
  return { runtime, ledger, calls };
}

function weiliaoEvent(eventId = "wl-001") {
  return {
    event_id: eventId,
    source: "weiliao",
    kind: "text",
    text: "測試 LINE",
    target: { type: "user", id: "U_TEST" },
  };
}

function xiaozhiEvent(eventId = "xz-001", target) {
  return {
    event_id: eventId,
    source: "xiaozhi",
    kind: "voice",
    audio: { ref: `local://${eventId}.amr`, codec: "amr-nb", duration_ms: 900 },
    target,
  };
}

test("dry-run maps 微聊 but performs no LINE network action", async (t) => {
  const { runtime, ledger, calls } = await fixture(t);
  const result = await runtime.ingestZ8Event(weiliaoEvent());
  assert.equal(result.status, "dry-run");
  assert.equal(calls.push.length, 0);
  assert.deepEqual((await ledger.snapshot()).map((record) => record.stage), ["mapped", "dry-run"]);
});

test("apply sends 微聊 text through LINE push", async (t) => {
  const { runtime, calls } = await fixture(t, "apply");
  const result = await runtime.ingestZ8Event(weiliaoEvent());
  assert.equal(result.status, "applied");
  assert.deepEqual(calls.push[0], {
    to: "U_TEST",
    messages: [{ type: "text", text: "測試 LINE" }],
  });
});

test("dedupe prevents the same event from being sent twice", async (t) => {
  const { runtime, calls } = await fixture(t, "apply");
  await runtime.ingestZ8Event(weiliaoEvent());
  const second = await runtime.ingestZ8Event(weiliaoEvent());
  assert.equal(second.status, "duplicate");
  assert.equal(calls.push.length, 1);
});

test("chatgpt voice mode runs STT, qwen and voice output", async (t) => {
  const { runtime, calls } = await fixture(t, "apply");
  const result = await runtime.ingestZ8Event(xiaozhiEvent());
  assert.equal(result.status, "applied");
  assert.equal(calls.transcribe.length, 1);
  assert.equal(calls.complete[0].options.engine, "qwen-main");
  assert.deepEqual(calls.synthesize, ["答覆:語音內容"]);
  assert.equal(calls.push.length, 0);
});

test("line voice mode routes the local voice response to LINE", async (t) => {
  const { runtime, calls } = await fixture(t, "apply");
  await runtime.setVoiceMode("line");
  const result = await runtime.ingestZ8Event(
    xiaozhiEvent("xz-line-001", { type: "user", id: "U_TEST" }),
  );
  assert.equal(result.status, "applied");
  assert.equal(calls.synthesize.length, 0);
  assert.deepEqual(calls.synthesizeLine, ["答覆:語音內容"]);
  assert.deepEqual(calls.push[0], {
    to: "U_TEST",
    messages: [{
      type: "audio",
      originalContentUrl: "https://audio.example/line-result.m4a",
      duration: 1100,
    }],
  });
});

test("LINE inbound apply invokes local model and official reply adapter", async (t) => {
  const { runtime, calls } = await fixture(t, "apply");
  const results = await runtime.ingestLineWebhook({
    events: [
      {
        webhookEventId: "line-001",
        type: "message",
        timestamp: Date.parse("2026-08-11T00:00:00.000Z"),
        source: { type: "user", userId: "U_TEST" },
        message: { id: "m-001", type: "text", text: "你好" },
        replyToken: "reply-token",
      },
    ],
  });
  assert.equal(results[0].status, "applied");
  assert.deepEqual(calls.reply[0], {
    replyToken: "reply-token",
    messages: [{ type: "text", text: "答覆:你好" }],
  });
});

test("runtime switches are explicit and revert records do not claim to unsend LINE", async (t) => {
  const { runtime } = await fixture(t);
  await runtime.ingestZ8Event(weiliaoEvent("wl-revert"));
  await runtime.setEngine("muse-agent");
  await runtime.setVoiceMode("line");
  await runtime.setMode("apply");
  const reverted = await runtime.revert("wl-revert", "mapping rejected by operator");
  assert.deepEqual(runtime.state(), { mode: "apply", engine: "muse-agent", voice_mode: "line" });
  assert.equal(reverted.record.external_effect_recalled, false);
});
