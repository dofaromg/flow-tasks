import test from "node:test";
import assert from "node:assert/strict";
import {
  safeEqual,
  signHmacBase64,
  signHmacHex,
  verifyDeviceSignature,
  verifyLineSignature,
} from "../src/security.js";

test("verifies LINE raw-body HMAC-SHA256 base64", () => {
  const raw = Buffer.from('{"events":[]}');
  const signature = signHmacBase64(raw, "line-secret");
  assert.equal(verifyLineSignature(raw, signature, "line-secret"), true);
  assert.equal(verifyLineSignature(Buffer.from('{"events":[1]}'), signature, "line-secret"), false);
});

test("device signature accepts base64 and hex encodings", () => {
  const raw = Buffer.from('{"source":"weiliao"}');
  assert.equal(verifyDeviceSignature(raw, signHmacBase64(raw, "device-secret"), "device-secret"), true);
  assert.equal(verifyDeviceSignature(raw, signHmacHex(raw, "device-secret"), "device-secret"), true);
  assert.equal(verifyDeviceSignature(raw, "bad", "device-secret"), false);
});

test("safeEqual handles unequal lengths without throwing", () => {
  assert.equal(safeEqual("a", "different"), false);
  assert.equal(safeEqual("same", "same"), true);
});
