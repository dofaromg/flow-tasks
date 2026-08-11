import test from "node:test";
import assert from "node:assert/strict";
import { mapLineWebhookEvent, mapZ8Event } from "../src/mapping.js";

const fixedNow = () => "2026-08-11T00:00:00.000Z";

test("maps 小智 voice to z8.xiaozhi.voice without replacing the source entry", () => {
  const particle = mapZ8Event(
    {
      event_id: "xz-001",
      source: "xiaozhi",
      kind: "voice",
      device_id: "owned-z8",
      occurred_at: "2026-08-10T23:59:58.000Z",
      audio: {
        ref: "local://capture/xz-001.amr",
        codec: "amr-nb",
        mime_type: "audio/amr",
        duration_ms: 1200,
      },
    },
    { now: fixedNow },
  );

  assert.equal(particle.particle_type, "z8.xiaozhi.voice");
  assert.equal(particle.source.entry, "xiaozhi");
  assert.equal(particle.direction, "outbound");
  assert.deepEqual(particle.runtime_path, ["Perception", "Fluin", "Runtime", "Action"]);
  assert.equal(particle.origin_signature, "MrLiouWord");
});

test("maps 微聊 UI text to z8.line.text and retains the LINE target", () => {
  const particle = mapZ8Event(
    {
      event_id: "wl-001",
      source: "weiliao",
      kind: "text",
      text: "回家吃飯",
      target: { type: "user", id: "U_TEST" },
    },
    { now: fixedNow },
  );

  assert.equal(particle.particle_type, "z8.line.text");
  assert.equal(particle.source.entry, "weiliao");
  assert.equal(particle.payload.text, "回家吃飯");
  assert.deepEqual(particle.target, { type: "user", id: "U_TEST" });
});

test("maps a LINE text webhook into the same particle with inbound direction", () => {
  const particle = mapLineWebhookEvent(
    {
      webhookEventId: "line-001",
      type: "message",
      timestamp: Date.parse("2026-08-11T00:00:00.000Z"),
      source: { type: "user", userId: "U_TEST" },
      message: { id: "m-001", type: "text", text: "收到" },
      replyToken: "reply-token",
    },
    { now: fixedNow },
  );

  assert.equal(particle.particle_type, "z8.line.text");
  assert.equal(particle.direction, "inbound");
  assert.equal(particle.source.entry, "line");
});

test("rejects unsupported source/kind combinations", () => {
  assert.throws(
    () => mapZ8Event({ source: "weiliao", kind: "voice", audio: { ref: "x" } }),
    (error) => error.code === "UNSUPPORTED_MAPPING",
  );
});

test("content-derived event and particle ids are deterministic", () => {
  const input = {
    source: "weiliao",
    kind: "text",
    occurred_at: "2026-08-11T00:00:00.000Z",
    text: "same",
  };
  const a = mapZ8Event(input, { now: fixedNow });
  const b = mapZ8Event(input, { now: fixedNow });
  assert.equal(a.event_id, b.event_id);
  assert.equal(a.particle_id, b.particle_id);
  assert.equal(a.integrity.value, b.integrity.value);
});
