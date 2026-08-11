import test from "node:test";
import assert from "node:assert/strict";
import { LineMessagingClient } from "../src/line.js";
import { LocalModelClient, LocalVoiceClient } from "../src/model.js";

test("LINE push uses the actual Messaging API path and bearer token", async () => {
  const calls = [];
  const client = new LineMessagingClient({
    accessToken: "test-token",
    fetchImpl: async (url, options) => {
      calls.push({ url, options });
      return new Response("{}", { status: 200, headers: { "content-type": "application/json" } });
    },
  });
  await client.push("U_TEST", [{ type: "text", text: "hello" }]);
  assert.equal(calls[0].url, "https://api.line.me/v2/bot/message/push");
  assert.equal(calls[0].options.headers.authorization, "Bearer test-token");
  assert.deepEqual(JSON.parse(calls[0].options.body), {
    to: "U_TEST",
    messages: [{ type: "text", text: "hello" }],
  });
});

test("LINE apply fails closed when its access token is absent", async () => {
  const client = new LineMessagingClient({ accessToken: "" });
  await assert.rejects(
    () => client.push("U_TEST", [{ type: "text", text: "hello" }]),
    (error) => error.code === "DEPENDENCY_MISSING",
  );
});

test("local model client parses an OpenAI-compatible qwen response", async () => {
  const client = new LocalModelClient({
    qwenEndpoint: "http://127.0.0.1:1234/v1/chat/completions",
    qwenModel: "qwen-main",
    fetchImpl: async () => new Response(JSON.stringify({
      choices: [{ message: { content: "本地答覆" } }],
    }), { status: 200, headers: { "content-type": "application/json" } }),
  });
  const result = await client.complete("問題", { engine: "qwen-main" });
  assert.equal(result.text, "本地答覆");
  assert.equal(result.model, "qwen-main");
});

test("LINE voice adapter requires a public HTTPS audio asset and duration", async () => {
  const valid = new LocalVoiceClient({
    lineVoiceEndpoint: "http://127.0.0.1:9003/v1/speech",
    fetchImpl: async () => new Response(JSON.stringify({
      audio_url: "https://audio.example/voice.m4a",
      duration_ms: 1200,
    }), { status: 200, headers: { "content-type": "application/json" } }),
  });
  assert.deepEqual(await valid.synthesizeLine("答覆"), {
    audio_url: "https://audio.example/voice.m4a",
    duration_ms: 1200,
  });

  const invalid = new LocalVoiceClient({
    lineVoiceEndpoint: "http://127.0.0.1:9003/v1/speech",
    fetchImpl: async () => new Response(JSON.stringify({
      audio_url: "http://local-only/voice.m4a",
      duration_ms: 0,
    }), { status: 200, headers: { "content-type": "application/json" } }),
  });
  await assert.rejects(
    () => invalid.synthesizeLine("答覆"),
    (error) => error.code === "LINE_VOICE_RESPONSE_INVALID",
  );
});
