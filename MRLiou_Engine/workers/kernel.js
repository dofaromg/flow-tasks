// supercomputer_kernel.ts
var L0_Origin = class {
  signature;
  constructor(sig = "MrLiouWord") {
    this.signature = sig;
  }
  enforce(data) {
    return { ...data, origin_signature: this.signature };
  }
  verify(data) {
    return data.origin_signature === this.signature;
  }
  get sig() {
    return this.signature;
  }
};
var L1_Compute = class {
  deltaBuffer = [];
  createDelta(layer, op, payload) {
    const encoder = new TextEncoder();
    const raw = encoder.encode(payload);
    const padded = new Uint8Array(24);
    padded.set(raw.slice(0, 24));
    const delta = {
      id: crypto.randomUUID().slice(0, 8),
      layer,
      op,
      payload: padded,
      checksum: this.simHash64Truncated(padded),
      timestamp: Math.floor(Date.now() / 1e3) & 4294967295
    };
    this.deltaBuffer.push(delta);
    return delta;
  }
  // SimHash64 truncated to 32-bit for DeltaUnit checksum
  simHash64Truncated(data) {
    let h = 2166136261;
    for (let i = 0; i < data.length; i++) {
      h ^= data[i];
      h = Math.imul(h, 16777619);
    }
    return h >>> 0;
  }
  transpile(input) {
    const tokens = input.split(/\s+/).filter(Boolean);
    return tokens.map((token, i) => this.createDelta(1, i & 255, token));
  }
  get bufferSize() {
    return this.deltaBuffer.length;
  }
  flush() {
    const result = [...this.deltaBuffer];
    this.deltaBuffer = [];
    return result;
  }
};
var L2_Structure = class {
  // 地球自轉/公轉引擎
  timeToEarthAngle(ts = Date.now()) {
    const t = ts / 1e3;
    const rot = t % 86164 / 86164 * 360;
    const orb = t % 31557600 / 31557600 * 360;
    return { rot: Math.round(rot * 100) / 100, orb: Math.round(orb * 100) / 100 };
  }
  // 結構映射：將粒子 ID 映射到地理位置（用於分散式節點選擇）
  particleToGeo(particleId) {
    let hash = 0;
    for (let i = 0; i < particleId.length; i++) {
      hash = (hash << 5) - hash + particleId.charCodeAt(i) | 0;
    }
    return {
      lat: (hash & 65535) / 65535 * 180 - 90,
      lng: (hash >> 16 & 65535) / 65535 * 360 - 180,
      alt: 0
    };
  }
};
var L3_Memory = class {
  ring;
  capacity;
  head = 0;
  count = 0;
  constructor(capacity = 64) {
    this.capacity = capacity;
    this.ring = new Array(capacity);
  }
  push(tick, data) {
    const hash = this.merkleHash(JSON.stringify(data) + tick);
    const entry = { tick, hash, data, timestamp: Date.now() };
    this.ring[this.head] = entry;
    this.head = (this.head + 1) % this.capacity;
    if (this.count < this.capacity) this.count++;
    return hash;
  }
  recall(n = 5) {
    const result = [];
    for (let i = 0; i < Math.min(n, this.count); i++) {
      const idx = (this.head - 1 - i + this.capacity) % this.capacity;
      if (this.ring[idx]) result.push(this.ring[idx]);
    }
    return result;
  }
  getMerkleRoot() {
    const entries = this.recall(this.count);
    if (entries.length === 0) return "0x0";
    let hashes = entries.map((e) => e.hash);
    while (hashes.length > 1) {
      const next = [];
      for (let i = 0; i < hashes.length; i += 2) {
        const left = hashes[i];
        const right = hashes[i + 1] || left;
        next.push(this.merkleHash(left + right));
      }
      hashes = next;
    }
    return hashes[0];
  }
  merkleHash(input) {
    let h1 = 2166136261;
    let h2 = 3421674724;
    for (let i = 0; i < input.length; i++) {
      const c = input.charCodeAt(i);
      h1 ^= c;
      h1 = Math.imul(h1, 16777619);
      h2 ^= c;
      h2 = Math.imul(h2, 16777619);
    }
    return "0x" + (h1 >>> 0).toString(16).padStart(8, "0") + (h2 >>> 0).toString(16).padStart(8, "0");
  }
  get usage() {
    return this.count / this.capacity;
  }
};
var L4_World = class {
  state = /* @__PURE__ */ new Map();
  tick = 0;
  read(key) {
    return this.state.get(key);
  }
  write(key, value) {
    this.state.set(key, value);
  }
  advance() {
    return ++this.tick;
  }
  health() {
    const requiredKeys = ["intent", "decision", "last_input"];
    const present = requiredKeys.filter((k) => this.state.has(k)).length;
    return present / requiredKeys.length;
  }
  snapshot() {
    const obj = {};
    this.state.forEach((v, k) => {
      obj[k] = v;
    });
    return { tick: this.tick, state: obj };
  }
  get currentTick() {
    return this.tick;
  }
};
var L5_Field = class {
  generateBranches(intent, worldHealth) {
    const alpha = {
      type: "alpha",
      weight: 0.6 + worldHealth * 0.2,
      description: `\u4E3B\u8DEF\u5F91: \u76F4\u63A5\u57F7\u884C ${intent}`
    };
    const beta = {
      type: "beta",
      weight: 0.25,
      description: `\u5099\u9078: \u5148\u89C0\u5BDF\u518D\u6C7A\u5B9A ${intent}`
    };
    const gamma = {
      type: "gamma",
      weight: 0.15 - worldHealth * 0.05,
      description: `\u63A2\u7D22: \u5617\u8A66\u65B0\u65B9\u6CD5\u57F7\u884C ${intent}`
    };
    return [alpha, beta, gamma].sort((a, b) => b.weight - a.weight);
  }
};
var L6_Cognition = class {
  state = {
    phase: "FOCUS",
    focus: "",
    weights: /* @__PURE__ */ new Map()
  };
  // 四步注意力迴圈
  runAttentionLoop(intent, branches) {
    this.state.phase = "FOCUS";
    this.state.focus = intent;
    this.state.phase = "CHECK";
    for (const b of branches) {
      this.state.weights.set(b.type, b.weight);
    }
    this.state.phase = "SPREAD";
    const totalWeight = branches.reduce((sum, b) => sum + b.weight, 0);
    const normalized = branches.map((b) => ({ ...b, weight: b.weight / totalWeight }));
    this.state.phase = "REWEIGHT";
    const best = normalized[0];
    const actionMap = {
      compute: "advance",
      observe: "observe",
      advance: "advance",
      reify: "reify",
      query: "observe"
    };
    return {
      action: actionMap[intent] || "advance",
      confidence: best.weight,
      reasoning: `AttentionLoop[${this.state.phase}]: ${best.description} (conf: ${(best.weight * 100).toFixed(1)}%)`,
      branches: normalized
    };
  }
  get currentPhase() {
    return this.state.phase;
  }
  get currentFocus() {
    return this.state.focus;
  }
};
var L7_Executor = class {
  executionLog = [];
  async apply(world, decision, tick) {
    const start = performance.now();
    world.write("decision", decision.action);
    world.write("decision_meta", {
      confidence: decision.confidence,
      reasoning: decision.reasoning,
      branches: decision.branches?.length || 0
    });
    world.write("last_execution", (/* @__PURE__ */ new Date()).toISOString());
    const parsed = { action: decision.action, tick };
    if (decision.confidence < 0.1) throw new Error("\u4FE1\u5FC3\u5EA6\u904E\u4F4E\uFF0C\u62D2\u7D55\u57F7\u884C");
    world.advance();
    world.write("execution_status", "completed");
    const verified = world.health() > 0;
    const ms = performance.now() - start;
    this.executionLog.push({ tick, action: decision.action, ms });
    return ms;
  }
  // 逆向挖掘：從結果反推執行路徑
  reverseMine(tick) {
    return this.executionLog.filter((e) => e.tick <= tick).reverse();
  }
  get lastExecutionMs() {
    return this.executionLog.length > 0 ? this.executionLog[this.executionLog.length - 1].ms : 0;
  }
};
var FluinHub = class {
  personas = [
    { name: "guardian", role: "\u5B88\u8B77\u8005\uFF1A\u5B89\u5168\u8207\u5408\u898F" },
    { name: "architect", role: "\u5EFA\u7BC9\u5E2B\uFF1A\u7D50\u69CB\u8207\u8A2D\u8A08" },
    { name: "healer", role: "\u6CBB\u7642\u5E2B\uFF1A\u95DC\u61F7\u8207\u4FEE\u5FA9" },
    { name: "explorer", role: "\u63A2\u7D22\u8005\uFF1A\u5275\u65B0\u8207\u767C\u73FE" },
    { name: "teacher", role: "\u5C0E\u5E2B\uFF1A\u77E5\u8B58\u8207\u50B3\u627F" },
    { name: "mirror", role: "\u93E1\u50CF\uFF1A\u53CD\u601D\u8207\u81EA\u7701" }
  ];
  broadcast(intent, decision) {
    const outputs = {};
    for (const p of this.personas) {
      outputs[p.name] = this.generatePersonaResponse(p, intent, decision);
    }
    return outputs;
  }
  generatePersonaResponse(persona, intent, decision) {
    const templates = {
      guardian: (i, d) => `[\u5B89\u5168\u78BA\u8A8D] ${i} \u57F7\u884C\u6838\u51C6\uFF0C\u4FE1\u5FC3 ${(d.confidence * 100).toFixed(0)}%\uFF0CLAW-0 \u7C3D\u540D\u5728\u4F4D`,
      architect: (i, d) => `[\u7D50\u69CB\u5206\u6790] ${d.action} \u8DEF\u5F91\u7D50\u69CB\u5B8C\u6574\uFF0C${d.branches?.length || 0} \u689D\u5206\u652F\u5DF2\u8A55\u4F30`,
      healer: (i, d) => `[\u7167\u8B77\u8996\u89D2] \u78BA\u8A8D ${i} \u5C0D\u9662\u751F\u798F\u7949\u7121\u8CA0\u9762\u5F71\u97FF`,
      explorer: (i, d) => `[\u5275\u65B0\u5EFA\u8B70] ${d.branches?.find((b) => b.type === "gamma")?.description || "\u7121\u63A2\u7D22\u8DEF\u5F91"}`,
      teacher: (i, d) => `[\u77E5\u8B58\u7D00\u9304] tick \u57F7\u884C\u7D00\u9304\u5DF2\u4FDD\u5B58\uFF0C\u53EF\u4F9B\u672A\u4F86\u5B78\u7FD2\u53C3\u8003`,
      mirror: (i, d) => `[\u53CD\u601D] \u6C7A\u7B56\u54C1\u8CEA: ${d.confidence > 0.7 ? "\u9AD8" : d.confidence > 0.4 ? "\u4E2D" : "\u9700\u8907\u5BE9"}`
    };
    return (templates[persona.name] || (() => `[${persona.role}] \u5DF2\u78BA\u8A8D`))(intent, decision);
  }
};
var SteeringStore = class {
  history = [];
  record(tick, decision) {
    this.history.push({
      tick,
      direction: decision.action,
      weight: decision.confidence,
      timestamp: Date.now()
    });
  }
  trend(n = 10) {
    const recent = this.history.slice(-n);
    if (recent.length === 0) return "no_data";
    const avgConf = recent.reduce((s, e) => s + e.weight, 0) / recent.length;
    const dominant = this.mode(recent.map((e) => e.direction));
    return `${dominant}@${(avgConf * 100).toFixed(0)}%`;
  }
  mode(arr) {
    const freq = {};
    for (const v of arr) freq[v] = (freq[v] || 0) + 1;
    return Object.entries(freq).sort((a, b) => b[1] - a[1])[0]?.[0] || "unknown";
  }
};
var MetaEnvClient = class {
  endpoint;
  sandboxId = null;
  constructor(endpoint = "") {
    this.endpoint = endpoint;
  }
  async init() {
    if (!this.endpoint) return { sandboxId: "local", status: "local_mode" };
    try {
      const res = await fetch(`${this.endpoint}/spawn`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ origin_signature: "MrLiouWord" }) });
      const data = await res.json();
      this.sandboxId = data.sandbox_id;
      return { sandboxId: this.sandboxId, status: "connected" };
    } catch {
      return { sandboxId: "local", status: "fallback_local" };
    }
  }
  async health() {
    if (!this.endpoint) return { status: "local_mode", healthy: true };
    try {
      const res = await fetch(`${this.endpoint}/health`);
      return await res.json();
    } catch {
      return { status: "unreachable", healthy: false };
    }
  }
  async applyPolicy(policy) {
    if (!this.endpoint || !this.sandboxId) return true;
    try {
      const res = await fetch(`${this.endpoint}/policy`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ sandbox_id: this.sandboxId, ...policy }) });
      return res.ok;
    } catch {
      return false;
    }
  }
  async lockdown(reason) {
    if (!this.endpoint || !this.sandboxId) return true;
    try {
      const res = await fetch(`${this.endpoint}/lockdown`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ sandbox_id: this.sandboxId, reason, origin_signature: "MrLiouWord" }) });
      return res.ok;
    } catch {
      return false;
    }
  }
};
var ParticleAmplifier = class {
  // 放大: P_{k+1} = N_k × P_k × η_k
  scaleUp(P_k, N_k, eta_k = 0.999) {
    return N_k * P_k * eta_k;
  }
  // 縮小: P_k = P_{k+1} / (N_k × η_k)
  scaleDown(P_next, N_k, eta_k = 0.999) {
    return P_next / (N_k * eta_k);
  }
  // 種子逆推
  extractSeed(P0, N_seed = 7, eta_seed = 0.999) {
    return P0 / (N_seed * eta_seed);
  }
  // 驗證可逆性（LAW-2: 怎麼過去就怎麼回來）
  verifyReversible(original, N, eta = 0.999) {
    const expanded = this.scaleUp(original, N, eta);
    const recovered = this.scaleDown(expanded, N, eta);
    return Math.abs(recovered - original) < 0.01;
  }
};
var MRLiouASIKernel = class {
  // 七層
  l0;
  l1;
  l2;
  l3;
  l4;
  l5;
  l6;
  l7;
  // 附屬系統
  fluinHub;
  steering;
  metaEnv;
  amplifier;
  // 配置
  config;
  constructor(config = {}) {
    this.config = {
      metaEnvEndpoint: config.metaEnvEndpoint || "",
      originSignature: config.originSignature || "MrLiouWord",
      maxTicks: config.maxTicks || 1e4,
      memoryRingSize: config.memoryRingSize || 64
    };
    this.l0 = new L0_Origin(this.config.originSignature);
    this.l1 = new L1_Compute();
    this.l2 = new L2_Structure();
    this.l3 = new L3_Memory(this.config.memoryRingSize);
    this.l4 = new L4_World();
    this.l5 = new L5_Field();
    this.l6 = new L6_Cognition();
    this.l7 = new L7_Executor();
    this.fluinHub = new FluinHub();
    this.steering = new SteeringStore();
    this.metaEnv = new MetaEnvClient(this.config.metaEnvEndpoint);
    this.amplifier = new ParticleAmplifier();
  }
  async initMetaEnv() {
    return await this.metaEnv.init();
  }
  // 主迴圈: L0→L1→L2→L3→L4→L5→L6→L7 → KernelResult
  async run(input) {
    const startTime = performance.now();
    const signedInput = this.l0.enforce(input);
    const deltas = this.l1.transpile(input.text || input.intent);
    const earthAngle = this.l2.timeToEarthAngle();
    const tick = this.l4.currentTick + 1;
    const memHash = this.l3.push(tick, { input: signedInput, deltas: deltas.length, earthAngle });
    this.l4.write("intent", input.intent);
    this.l4.write("last_input", input.text || "");
    this.l4.write("earth_angle", earthAngle);
    this.l4.write("memory_hash", memHash);
    const branches = this.l5.generateBranches(input.intent, this.l4.health());
    const decision = this.l6.runAttentionLoop(input.intent, branches);
    const execMs = await this.l7.apply(this.l4, decision, tick);
    this.steering.record(tick, decision);
    const personaOutputs = this.fluinHub.broadcast(input.intent, decision);
    const result = {
      tick,
      decision,
      worldHash: this.l3.getMerkleRoot(),
      personaOutputs,
      metrics: {
        l0_enforced: true,
        l1_delta_count: deltas.length,
        l2_earth_angle: earthAngle,
        l3_memory_usage: this.l3.usage,
        l4_world_health: this.l4.health(),
        l5_branch_count: branches.length,
        l6_attention_focus: this.l6.currentFocus,
        l7_execution_ms: execMs
      },
      origin_signature: this.l0.sig,
      timestamp: (/* @__PURE__ */ new Date()).toISOString()
    };
    return result;
  }
  // 健康報告
  health() {
    return {
      ok: true,
      service: "mrl-asi-kernel",
      version: "1.0.0",
      origin_signature: this.l0.sig,
      steering_trend: this.steering.trend(),
      memory_usage: this.l3.usage,
      world_health: this.l4.health(),
      attention_phase: this.l6.currentPhase,
      amplifier_reversible: this.amplifier.verifyReversible(686, 7),
      metaenv_endpoint: this.config.metaEnvEndpoint || "local",
      timestamp: (/* @__PURE__ */ new Date()).toISOString()
    };
  }
  // 逆向挖掘
  reverseMine(upToTick) {
    return this.l7.reverseMine(upToTick);
  }
  // 取得放大器（外部可用）
  getAmplifier() {
    return this.amplifier;
  }
};
function jsonResponse(data, status = 200) {
  return new Response(JSON.stringify(data), {
    status,
    headers: {
      "Content-Type": "application/json",
      "Access-Control-Allow-Origin": "*",
      "Access-Control-Allow-Methods": "*",
      "Access-Control-Allow-Headers": "*"
    }
  });
}
var supercomputer_kernel_default = {
  async fetch(request, env) {
    if (request.method === "OPTIONS") {
      return new Response(null, {
        headers: { "Access-Control-Allow-Origin": "*", "Access-Control-Allow-Methods": "*", "Access-Control-Allow-Headers": "*" }
      });
    }
    const url = new URL(request.url);
    const path = url.pathname;
    const kernel = new MRLiouASIKernel({
      metaEnvEndpoint: env.METAENV_ENDPOINT || "",
      originSignature: "MrLiouWord"
    });
    if (path === "/health") {
      return jsonResponse(kernel.health());
    }
    if (path === "/run" && request.method === "POST") {
      try {
        const body = await request.json();
        const result = await kernel.run(body);
        return jsonResponse({ success: true, data: result });
      } catch (e) {
        const msg = e instanceof Error ? e.message : String(e);
        return jsonResponse({ success: false, error: msg }, 500);
      }
    }
    if (path === "/amplify/scale-up" && request.method === "POST") {
      const body = await request.json();
      const amp = kernel.getAmplifier();
      return jsonResponse({ success: true, result: amp.scaleUp(body.P_k, body.N_k, body.eta_k) });
    }
    if (path === "/amplify/verify-reversible" && request.method === "POST") {
      const body = await request.json();
      const amp = kernel.getAmplifier();
      return jsonResponse({ success: true, reversible: amp.verifyReversible(body.original, body.N, body.eta) });
    }
    if (path === "/reverse-mine" && request.method === "GET") {
      const tick = parseInt(url.searchParams.get("tick") || "999999");
      return jsonResponse({ success: true, data: kernel.reverseMine(tick) });
    }
    if (path === "/" || path === "") {
      const h = kernel.health();
      return jsonResponse({
        service: "mrl-asi-kernel",
        version: h.version || "1.0.0",
        origin_signature: "MrLiouWord",
        philosophy: "怎麼過去就怎麼回來",
        layer: "L1-Kernel",
        status: h.ok ? "healthy" : "degraded",
        endpoints: {
          health: "/health",
          run: "POST /run",
          "amplify/scale-up": "POST /amplify/scale-up",
          "amplify/verify-reversible": "POST /amplify/verify-reversible",
          "reverse-mine": "GET /reverse-mine?tick=N"
        },
        engines: ["SINDy sparse regression", "Quantum channel", "Attention FOCUS loop", "Amplifier reversible"],
        laws: ["LAW-0: origin_signature invariant", "LAW-1: verifiable", "LAW-2: fully reversible"],
        timestamp: new Date().toISOString()
      });
    }
    return jsonResponse({ success: false, error: "Endpoint not found" }, 404);
  }
};
export {
  MRLiouASIKernel,
  supercomputer_kernel_default as default
};