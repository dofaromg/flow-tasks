import { createHmac, timingSafeEqual } from "node:crypto";

function asBuffer(value) {
  return Buffer.isBuffer(value) ? value : Buffer.from(String(value), "utf8");
}

export function signHmacBase64(rawBody, secret) {
  return createHmac("sha256", asBuffer(secret)).update(asBuffer(rawBody)).digest("base64");
}

export function signHmacHex(rawBody, secret) {
  return createHmac("sha256", asBuffer(secret)).update(asBuffer(rawBody)).digest("hex");
}

export function safeEqual(left, right) {
  const a = asBuffer(left);
  const b = asBuffer(right);
  return a.length === b.length && timingSafeEqual(a, b);
}

export function verifyLineSignature(rawBody, signature, channelSecret) {
  if (!channelSecret || !signature) return false;
  return safeEqual(signHmacBase64(rawBody, channelSecret), signature.trim());
}

export function verifyDeviceSignature(rawBody, signature, sharedSecret) {
  if (!sharedSecret || !signature) return false;
  const supplied = signature.trim();
  const expectedBase64 = signHmacBase64(rawBody, sharedSecret);
  const expectedHex = signHmacHex(rawBody, sharedSecret);
  return safeEqual(expectedBase64, supplied) || safeEqual(expectedHex, supplied.toLowerCase());
}
