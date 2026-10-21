/**
 * MRLIOU ASI MVP — L0-L7 Layer Stack
 * origin_signature: MrLiouWord
 * canon: HCRA  (Observe → Resolve → Mirror → Verify → Loop)
 * version: 1.3
 * sealed: 2026-02-15
 *
 * Layer responsibilities
 *   L0  ROOT     — signature + canon constants; never deleted
 *   L1  SEED     — exec gateway; initial constraint enforcement
 *   L2  PARTICLE — intent mapper (intent / payload / context_ok)
 *   L3  LAW      — ring buffer with fixed limit 32
 *   L4  WORLD    — key-value store + snapshot
 *   L5  MIRROR   — branch α / β
 *   L6  REFLECT  — choose(decision, world_hash)
 *   L7  LOOP     — pack(trace) → leaf / root; fold
 */

"use strict";

const crypto = require("crypto");

// ─── L0: ROOT ────────────────────────────────────────────────────────────────

const L0 = Object.freeze({
  signature: "MrLiouWord",
  canon: "HCRA",
  version: "1.3",

  /** Return true when sig matches the canonical origin signature. */
  verifySignature(sig) {
    return sig === this.signature;
  },
});

// ─── L1: SEED — exec gateway ─────────────────────────────────────────────────

class L1 {
  constructor(l0) {
    this._l0 = l0;
    this._log = [];
  }

  /**
   * Execute a named task, recording it with the origin signature.
   * @param {string} task
   * @param {*} payload
   * @returns {{ task, payload, timestamp, signature }}
   */
  exec(task, payload) {
    if (!task || typeof task !== "string") {
      throw new TypeError("L1.exec: task must be a non-empty string");
    }
    const entry = {
      task,
      payload: payload !== undefined ? payload : null,
      timestamp: Date.now(),
      signature: this._l0.signature,
    };
    this._log.push(entry);
    return entry;
  }

  /** Read all recorded exec entries (defensive copy). */
  readLog() {
    return [...this._log];
  }
}

// ─── L2: PARTICLE — intent mapper ────────────────────────────────────────────

class L2 {
  constructor(l0) {
    this._l0 = l0;
  }

  /**
   * Map an L1 exec entry to { intent, payload, context_ok }.
   * context_ok is true only when the entry carries the canonical signature.
   * @param {{ task, payload, signature }} entry
   * @returns {{ intent, payload, context_ok }}
   */
  map(entry) {
    return {
      intent: entry.task,
      payload: entry.payload,
      context_ok: this._l0.verifySignature(entry.signature),
    };
  }
}

// ─── L3: LAW — ring buffer (limit 32) ────────────────────────────────────────

class L3 {
  /**
   * @param {number} limit  Maximum entries retained (default 32, per spec).
   */
  constructor(limit = 32) {
    this._limit = limit;
    this._buffer = [];
  }

  /**
   * Push an item; evicts oldest entry when the buffer is full.
   * @returns {number} Current buffer length.
   */
  push(item) {
    this._buffer.push(item);
    if (this._buffer.length > this._limit) {
      this._buffer.shift();
    }
    return this._buffer.length;
  }

  /** Return a defensive copy of the current buffer. */
  read() {
    return [...this._buffer];
  }
}

// ─── L4: WORLD — key-value store + snapshot ──────────────────────────────────

class L4 {
  constructor() {
    this._store = {};
    this._snapshots = [];
  }

  /**
   * Write a key-value pair.
   * @param {string} k
   * @param {*} v
   */
  write(k, v) {
    if (typeof k !== "string" || k.length === 0) {
      throw new TypeError("L4.write: key must be a non-empty string");
    }
    this._store[k] = v;
  }

  /**
   * Snapshot the current store state.
   * @returns {{ timestamp: number, data: object }}
   */
  snapshot() {
    const snap = { timestamp: Date.now(), data: { ...this._store } };
    this._snapshots.push(snap);
    return snap;
  }

  /** Return a defensive copy of the store. */
  read() {
    return { ...this._store };
  }
}

// ─── L5: MIRROR — branch α / β ───────────────────────────────────────────────

class L5 {
  constructor() {
    this._alpha = [];
    this._beta = [];
  }

  /**
   * Route an item to branch α (default, trusted) or β (untrusted / divergent).
   * @param {*} item
   * @param {"α"|"β"|"alpha"|"beta"} side
   * @returns {{ alpha: number, beta: number }}
   */
  branch(item, side = "α") {
    if (side === "α" || side === "alpha") {
      this._alpha.push(item);
    } else {
      this._beta.push(item);
    }
    return { alpha: this._alpha.length, beta: this._beta.length };
  }

  readAlpha() { return [...this._alpha]; }
  readBeta()  { return [...this._beta];  }
}

// ─── L6: REFLECT — choose with world hash ────────────────────────────────────

class L6 {
  /**
   * Record a decision together with a deterministic hash of the world state.
   * @param {string} decision
   * @param {*} world_state   Any JSON-serialisable value.
   * @returns {{ decision, world_hash, timestamp }}
   */
  choose(decision, world_state) {
    const world_hash = crypto
      .createHash("sha256")
      .update(JSON.stringify(world_state !== undefined ? world_state : null))
      .digest("hex");
    return { decision, world_hash, timestamp: Date.now() };
  }
}

// ─── L7: LOOP — pack trace + fold ────────────────────────────────────────────

class L7 {
  /**
   * Pack a trace object into a { leaf, root, trace } envelope.
   * leaf = sha256(trace)
   * root = sha256(leaf + prev_root)
   * @param {{ prev_root?: string }} trace
   * @returns {{ leaf, root, trace }}
   */
  pack(trace) {
    const leaf = crypto
      .createHash("sha256")
      .update(JSON.stringify(trace))
      .digest("hex");
    const root = crypto
      .createHash("sha256")
      .update(leaf + (trace.prev_root || ""))
      .digest("hex");
    return { leaf, root, trace };
  }

  /**
   * Fold a list of items into a cumulative Merkle leaf.
   * Returns null for an empty list.
   * @param {any[]} items
   * @returns {{ leaf: string, root: string } | null}
   */
  fold(items) {
    if (!items || items.length === 0) return null;
    const ZERO = "0".repeat(64);
    return items.reduce(
      (acc, cur) => ({
        leaf: crypto
          .createHash("sha256")
          .update(acc.leaf + JSON.stringify(cur))
          .digest("hex"),
        root: acc.root,
      }),
      { leaf: ZERO, root: ZERO }
    );
  }
}

// ─── MRLiouASI — unified runtime stack ───────────────────────────────────────

class MRLiouASI {
  constructor() {
    this.l0 = L0;
    this.l1 = new L1(this.l0);
    this.l2 = new L2(this.l0);
    this.l3 = new L3(32);
    this.l4 = new L4();
    this.l5 = new L5();
    this.l6 = new L6();
    this.l7 = new L7();
  }

  /**
   * Single HCRA loop step:
   *   Observe (L1 exec) → Resolve (L2 map) → Mirror (L3 + L5) → Verify (L6) → [Loop]
   *
   * @param {string} task
   * @param {*} payload
   * @returns {{ entry, mapped, decision, packed }}
   */
  step(task, payload) {
    // Observe
    const entry = this.l1.exec(task, payload);

    // Resolve
    const mapped = this.l2.map(entry);

    // Mirror — store in ring buffer; route to α when context is verified
    this.l3.push(mapped);
    this.l5.branch(mapped, mapped.context_ok ? "α" : "β");

    // Verify
    const decision = this.l6.choose(task, { entry, mapped });

    // Loop (pack current state for the next iteration)
    const packed = this.l7.pack({ entry, mapped, decision });

    return { entry, mapped, decision, packed };
  }
}

module.exports = { MRLiouASI, L0, L1, L2, L3, L4, L5, L6, L7 };
