/**
 * particle-reversible v1.1.0 — 可逆計算引擎 (DL580 本地版)
 *
 * L0-Trust | 怎麼過去就怎麼回來 的核心實現
 * 每個操作都有逆操作，完整軌跡，Undo/Redo/Checkpoint/Replay
 * 端點: /execute /undo /redo /replay /checkpoint /health /
 *
 * origin_signature: MrLiouWord
 */

const VERSION = "1.1.0";

const INVERSE_MAP = {
  add: "subtract", subtract: "add",
  multiply: "divide", divide: "multiply",
  push: "pop", pop: "push",
  link: "unlink", unlink: "link",
  create: "delete", delete: "create",
  set: "unset", unset: "set",
  move: "move_back", move_back: "move",
  encrypt: "decrypt", decrypt: "encrypt",
  compress: "decompress", decompress: "compress",
  encode: "decode", decode: "encode"
};

// Operation executors
const EXECUTORS = {
  add: (state, args) => ({ ...state, value: (state.value || 0) + (args.amount || 0) }),
  subtract: (state, args) => ({ ...state, value: (state.value || 0) - (args.amount || 0) }),
  multiply: (state, args) => ({ ...state, value: (state.value || 0) * (args.factor || 1) }),
  divide: (state, args) => ({ ...state, value: args.factor ? (state.value || 0) / args.factor : state.value }),
  push: (state, args) => ({ ...state, stack: [...(state.stack || []), args.item] }),
  pop: (state) => { const s = [...(state.stack || [])]; const item = s.pop(); return { ...state, stack: s, last_popped: item }; },
  set: (state, args) => ({ ...state, [args.key]: args.value, _prev: { key: args.key, value: state[args.key] } }),
  unset: (state, args) => { const s = { ...state }; delete s[args.key]; return s; },
  create: (state, args) => ({ ...state, entities: { ...(state.entities || {}), [args.id]: args.data || {} } }),
  delete: (state, args) => { const e = { ...(state.entities || {}) }; const deleted = e[args.id]; delete e[args.id]; return { ...state, entities: e, _deleted: deleted }; },
  encode: (state, args) => ({ ...state, data: Buffer.from(args.data || state.data || "", "utf8").toString("base64") }),
  decode: (state, args) => ({ ...state, data: Buffer.from(args.data || state.data || "", "base64").toString("utf8") }),
  link: (state, args) => ({ ...state, links: [...(state.links || []), { from: args.from, to: args.to }] }),
  unlink: (state, args) => ({ ...state, links: (state.links || []).filter(l => !(l.from === args.from && l.to === args.to)) }),
  move: (state, args) => ({ ...state, position: args.to, _prev_position: state.position }),
  move_back: (state, args) => ({ ...state, position: args.to || state._prev_position }),
};

// Timeline for undo/redo
class ReversibleTimeline {
  constructor() {
    this.history = [];      // executed operations
    this.redoStack = [];    // undone operations
    this.checkpoints = {};  // named snapshots
    this.state = {};
  }

  execute(operation, args = {}) {
    const prevState = JSON.parse(JSON.stringify(this.state));
    const executor = EXECUTORS[operation];

    if (executor) {
      this.state = executor(this.state, args);
    }

    const entry = {
      id: `op_${Date.now()}_${Math.random().toString(36).slice(2, 6)}`,
      operation,
      inverse: INVERSE_MAP[operation] || null,
      args,
      prevState,
      timestamp: new Date().toISOString()
    };

    this.history.push(entry);
    this.redoStack = []; // Clear redo on new operation
    return { ...entry, state: this.state };
  }

  undo() {
    if (this.history.length === 0) return { success: false, error: "Nothing to undo" };
    const last = this.history.pop();
    this.state = last.prevState;
    this.redoStack.push(last);
    return { success: true, undone: last.operation, state: this.state };
  }

  redo() {
    if (this.redoStack.length === 0) return { success: false, error: "Nothing to redo" };
    const entry = this.redoStack.pop();
    const executor = EXECUTORS[entry.operation];
    if (executor) {
      this.state = executor(this.state, entry.args);
    }
    this.history.push(entry);
    return { success: true, redone: entry.operation, state: this.state };
  }

  checkpoint(name) {
    this.checkpoints[name] = {
      state: JSON.parse(JSON.stringify(this.state)),
      historyLength: this.history.length,
      timestamp: new Date().toISOString()
    };
    return { success: true, name, historyLength: this.history.length };
  }

  replay(fromIndex = 0) {
    const steps = this.history.slice(fromIndex).map(h => ({
      operation: h.operation,
      args: h.args,
      timestamp: h.timestamp
    }));
    return { steps, total: steps.length, from: fromIndex };
  }
}

// Per-session timelines
const timelines = new Map();

function getTimeline(sessionId = "default") {
  if (!timelines.has(sessionId)) {
    timelines.set(sessionId, new ReversibleTimeline());
  }
  return timelines.get(sessionId);
}

const json = (data, status = 200) => new Response(JSON.stringify(data, null, 2), {
  status,
  headers: { "Content-Type": "application/json; charset=utf-8", "Access-Control-Allow-Origin": "*", "X-Origin-Signature": "MrLiouWord" }
});

export default {
  async fetch(request) {
    const url = new URL(request.url);
    const path = url.pathname;

    if (request.method === "OPTIONS") {
      return new Response(null, { headers: { "Access-Control-Allow-Origin": "*", "Access-Control-Allow-Methods": "*", "Access-Control-Allow-Headers": "*" } });
    }

    if (path === "/" || path === "") {
      return json({
        name: "particle-reversible", version: VERSION, layer: "L0",
        philosophy: "怎麼過去就怎麼回來",
        description: "可逆計算引擎",
        operations: Object.keys(INVERSE_MAP),
        inverse_mapping: INVERSE_MAP,
        endpoints: ["/execute", "/undo", "/redo", "/replay", "/checkpoint"],
        origin_signature: "MrLiouWord", runtime: "DL580-local"
      });
    }

    if (path === "/health") {
      return json({
        status: "healthy", name: "particle-reversible", version: VERSION,
        sessions: timelines.size, origin_signature: "MrLiouWord",
        runtime: "DL580-local", timestamp: new Date().toISOString()
      });
    }

    if (request.method !== "POST") return json({ error: "POST required" }, 405);

    let body;
    try { body = await request.json(); } catch { return json({ error: "invalid JSON" }, 400); }

    const session = body.session || "default";
    const tl = getTimeline(session);

    if (path === "/execute") {
      if (!body.operation) return json({ success: false, error: "operation required" }, 400);
      if (!INVERSE_MAP[body.operation] && !EXECUTORS[body.operation]) {
        return json({ success: false, error: `Unknown operation: ${body.operation}`, available: Object.keys(INVERSE_MAP) }, 400);
      }
      const result = tl.execute(body.operation, body.args || body.data || {});
      return json({ success: true, ...result, reversible: !!INVERSE_MAP[body.operation], origin_signature: "MrLiouWord" });
    }

    if (path === "/undo") return json(tl.undo());
    if (path === "/redo") return json(tl.redo());

    if (path === "/checkpoint") {
      const name = body.name || `cp_${Date.now()}`;
      return json(tl.checkpoint(name));
    }

    if (path === "/replay") {
      return json({ success: true, ...tl.replay(body.from || 0), origin_signature: "MrLiouWord" });
    }

    return json({ error: "route not found", path }, 404);
  }
};
