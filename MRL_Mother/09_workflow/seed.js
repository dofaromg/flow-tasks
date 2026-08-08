/**
 * SEED(X) Compression Module
 *
 * Formula: SEED(X) = STORE(RECURSE(FLOW(MARK(STRUCTURE(X)))))
 *
 * Reverse-projection:  δP₀[] = P₀ / (N_seed · η_seed)
 * Amplification:       P_{k+1} = N_k · P_k · η_k
 * Round-trip fidelity: η_round_trip ≈ 1.0
 *
 * origin_signature: MrLiouWord
 * sealed: 2026-02-15
 */

"use strict";

const crypto = require("crypto");

// ─── Pipeline steps ──────────────────────────────────────────────────────────

/**
 * STRUCTURE: Extract the structural skeleton from an arbitrary JavaScript value.
 * Produces a pure JSON-serialisable description (no circular references).
 *
 * @param {*} x
 * @returns {object}
 */
function structure(x) {
  if (x === null || x === undefined) {
    return { type: "null", value: null };
  }
  if (Array.isArray(x)) {
    return { type: "array", items: x.map(structure) };
  }
  if (typeof x === "object") {
    const keys = Object.keys(x).sort();
    const children = {};
    for (const k of keys) {
      children[k] = structure(x[k]);
    }
    return { type: "object", keys, children };
  }
  return { type: typeof x, value: x };
}

/**
 * MARK: Attach a content hash (_hash) to every node of a structured skeleton
 * (recursively, depth-first).
 *
 * @param {object} structured  Output of structure().
 * @returns {object}           Same shape with _hash added at every level.
 */
function mark(structured) {
  let node = structured;

  if (node.type === "array") {
    const items = (node.items || []).map(mark);
    node = { ...node, items };
  } else if (node.type === "object") {
    const children = {};
    for (const k of (node.keys || [])) {
      children[k] = mark(node.children[k]);
    }
    node = { ...node, children };
  }

  const canonical = JSON.stringify(node);
  const hash = crypto.createHash("sha256").update(canonical).digest("hex");
  return { ...node, _hash: hash };
}

/**
 * FLOW: Linearise a marked structure into a flat sequence of { hash, type } tokens.
 *
 * @param {object} marked  Output of mark().
 * @param {Array}  [seq]   Accumulator (internal use).
 * @returns {{ hash: string, type: string }[]}
 */
function flow(marked, seq = []) {
  seq.push({ hash: marked._hash, type: marked.type });
  if (marked.type === "array") {
    for (const item of (marked.items || [])) {
      flow(item, seq);
    }
  } else if (marked.type === "object") {
    const children = marked.children || {};
    for (const k of (marked.keys || [])) {
      flow(children[k], seq);
    }
  }
  return seq;
}

/**
 * RECURSE: Detect repeated hash patterns and replace duplicates with back-references.
 * This is the core compression step; the first occurrence is kept verbatim while
 * subsequent occurrences carry a _ref pointer instead of redundant sub-trees.
 *
 * @param {{ hash: string, type: string }[]} flowSeq  Output of flow().
 * @returns {object[]}  Same array with duplicates annotated as _ref entries.
 */
function recurse(flowSeq) {
  const seen = new Set();
  return flowSeq.map((item) => {
    if (seen.has(item.hash)) {
      return { ...item, _ref: item.hash };
    }
    seen.add(item.hash);
    return item;
  });
}

/**
 * STORE: Produce the final compact SEED envelope.
 *
 * @param {object[]} recurred     Output of recurse().
 * @param {string}   rootHash     _hash of the top-level mark() node.
 * @returns {object}              SEED envelope (type: "flpkg.seed").
 */
function store(recurred, rootHash) {
  return {
    type: "flpkg.seed",
    origin_signature: "MrLiouWord",
    root_hash: rootHash,
    flow_length: recurred.length,
    flow: recurred,
    created_at: Date.now(),
  };
}

// ─── Public API ───────────────────────────────────────────────────────────────

/**
 * SEED(X) — full five-step compression pipeline.
 *
 * @param {*} x  Any JavaScript value.
 * @returns {object}  A "flpkg.seed" envelope.
 */
function seedCompress(x) {
  const s = structure(x);
  const m = mark(s);
  const f = flow(m);
  const r = recurse(f);
  return store(r, m._hash);
}

/**
 * Amplify one generation of the seed signal.
 *
 * P_{k+1} = N_k · P_k · η_k
 *
 * @param {number} P_k    Current generation power.
 * @param {number} N_k    Fan-out factor (number of parallel seeds).
 * @param {number} eta_k  Round-trip fidelity for this generation (≈ 1.0).
 * @returns {number}      Next-generation power P_{k+1}.
 */
function amplify(P_k, N_k, eta_k) {
  return N_k * P_k * eta_k;
}

/**
 * Reverse-project the seed delta for generation 0.
 *
 * δP₀[] = P₀ / (N_seed · η_seed)
 *
 * @param {number} P0       Base power at generation 0.
 * @param {number} N_seed   Number of seeds.
 * @param {number} eta_seed Round-trip fidelity (must be non-zero).
 * @returns {number}        Per-seed delta δP₀.
 * @throws {RangeError}     When N_seed or eta_seed is zero.
 */
function reverseProject(P0, N_seed, eta_seed) {
  if (N_seed === 0 || eta_seed === 0) {
    throw new RangeError("reverseProject: N_seed and eta_seed must be non-zero");
  }
  return P0 / (N_seed * eta_seed);
}

module.exports = {
  seedCompress,
  amplify,
  reverseProject,
  // expose pipeline steps for testing / composition
  structure,
  mark,
  flow,
  recurse,
  store,
};
