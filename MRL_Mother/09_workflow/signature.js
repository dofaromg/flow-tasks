/**
 * LAW-0 Signature Law — embedSignature / extractSignature / verifySignature
 *
 * Formula: T(e) = e'  ⟹  signature(e) = signature(e')
 *
 * Any transformation of a sealed object must preserve its embedded signature.
 * Use these three interfaces to attach, read, and verify the MrLiouWord
 * origin signature across all L0-L7 layers.
 *
 * origin_signature: MrLiouWord
 * sealed: 2026-02-15
 */

"use strict";

const crypto = require("crypto");

const ORIGIN_SIGNATURE = "MrLiouWord";

/**
 * Embed the canonical signature into a plain object (non-mutating).
 *
 * Adds two fields to a shallow copy of `obj`:
 *   _signature  — the signer identity string
 *   _sig_hash   — sha256(signature + ":" + JSON(obj)) for tamper detection
 *
 * @param {object} obj   Plain object to sign.
 * @param {string} [sig] Signer identity; defaults to ORIGIN_SIGNATURE.
 * @returns {object}     A new object with _signature and _sig_hash appended.
 */
function embedSignature(obj, sig = ORIGIN_SIGNATURE) {
  if (!obj || typeof obj !== "object" || Array.isArray(obj)) {
    throw new TypeError("embedSignature: obj must be a plain (non-array) object");
  }
  const base = JSON.stringify(obj);
  const sig_hash = crypto
    .createHash("sha256")
    .update(sig + ":" + base)
    .digest("hex");
  return { ...obj, _signature: sig, _sig_hash: sig_hash };
}

/**
 * Extract the embedded signature info from a previously signed object.
 *
 * @param {object} obj
 * @returns {{ signature: string, sig_hash: string } | null}
 *   Returns null when no embedded signature is found.
 */
function extractSignature(obj) {
  if (!obj || typeof obj !== "object") return null;
  const { _signature, _sig_hash } = obj;
  if (!_signature) return null;
  return { signature: _signature, sig_hash: _sig_hash || null };
}

/**
 * Verify the embedded signature against the object's current content.
 *
 * The function strips _signature and _sig_hash, re-hashes the remainder,
 * and compares against the stored _sig_hash.
 *
 * @param {object} obj
 * @param {string} [expectedSig]  Expected signer identity; defaults to ORIGIN_SIGNATURE.
 * @returns {boolean}  true when the signature is present, matches expectedSig, and the hash verifies.
 */
function verifySignature(obj, expectedSig = ORIGIN_SIGNATURE) {
  if (!obj || typeof obj !== "object") return false;
  const { _signature, _sig_hash, ...rest } = obj;
  if (!_signature || !_sig_hash) return false;
  if (_signature !== expectedSig) return false;
  const base = JSON.stringify(rest);
  const computed = crypto
    .createHash("sha256")
    .update(_signature + ":" + base)
    .digest("hex");
  return computed === _sig_hash;
}

module.exports = {
  ORIGIN_SIGNATURE,
  embedSignature,
  extractSignature,
  verifySignature,
};
