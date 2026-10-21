/**
 * particle-attention v1.1.0 — MR.liou 注意力機制 (DL580 本地版)
 *
 * L6-Flow | FOCUS→CHECK_HANDSHAKE→SPREAD→REWEIGHT 迴圈
 * 端點: /focus /spread /reweight /check /loop /health /
 *
 * vs Transformer: Q·K·V 固定一次算完 → MR.liou 循環直到 handshake=true
 *
 * origin_signature: MrLiouWord
 * 怎麼過去就怎麼回來
 */

const VERSION = "1.1.0";

const STRATEGIES = {
  normalize: (weights) => {
    const sum = weights.reduce((a, b) => a + b, 0);
    return sum > 0 ? weights.map(w => w / sum) : weights.map(() => 1 / weights.length);
  },
  softmax: (weights) => {
    const max = Math.max(...weights);
    const exps = weights.map(w => Math.exp(w - max));
    const sum = exps.reduce((a, b) => a + b, 0);
    return exps.map(e => e / sum);
  },
  uniform: (weights) => weights.map(() => 1 / weights.length),
  random: (weights) => {
    const raw = weights.map(() => Math.random());
    const sum = raw.reduce((a, b) => a + b, 0);
    return raw.map(r => r / sum);
  },
  boost: (weights) => {
    const boosted = weights.map(w => w * w);
    const sum = boosted.reduce((a, b) => a + b, 0);
    return sum > 0 ? boosted.map(b => b / sum) : weights.map(() => 1 / weights.length);
  }
};

function focus(particles, target) {
  // Focus attention on target or highest-weight particle
  const targetId = target || null;
  return particles.map(p => ({
    ...p,
    focused: targetId ? p.id === targetId : false,
    weight: targetId && p.id === targetId ? Math.min(p.weight * 1.5, 1.0) : p.weight
  }));
}

function checkHandshake(particles, threshold = 0.7) {
  // Check if attention has converged
  const weights = particles.map(p => p.weight || 0);
  const max = Math.max(...weights);
  const sum = weights.reduce((a, b) => a + b, 0);
  const confidence = sum > 0 ? max / sum : 0;
  return { handshake: confidence >= threshold, confidence: Math.round(confidence * 10000) / 10000 };
}

function spread(particles, strategy = "normalize") {
  const fn = STRATEGIES[strategy] || STRATEGIES.normalize;
  const weights = fn(particles.map(p => p.weight || 0));
  return particles.map((p, i) => ({ ...p, weight: Math.round(weights[i] * 10000) / 10000 }));
}

function reweight(particles, adjustments = {}) {
  return particles.map(p => {
    const adj = adjustments[p.id] || 0;
    return { ...p, weight: Math.max(0, Math.min(1, (p.weight || 0) + adj)) };
  });
}

function attentionLoop(particles, maxCycles = 10, strategy = "normalize", threshold = 0.7) {
  let current = particles.map(p => ({ id: p.id, weight: p.weight || 1.0 / particles.length, ...p }));
  const history = [];

  for (let cycle = 0; cycle < maxCycles; cycle++) {
    // FOCUS
    const maxW = Math.max(...current.map(p => p.weight));
    const focusTarget = current.find(p => p.weight === maxW)?.id;
    current = focus(current, focusTarget);

    // CHECK_HANDSHAKE
    const check = checkHandshake(current, threshold);
    history.push({ cycle, phase: "CHECK", ...check, top: focusTarget });

    if (check.handshake) {
      return {
        converged: true,
        cycles: cycle + 1,
        result: current,
        winner: focusTarget,
        confidence: check.confidence,
        history
      };
    }

    // SPREAD
    current = spread(current, strategy);

    // REWEIGHT (slight random perturbation to avoid stuck)
    current = current.map(p => ({
      ...p,
      weight: Math.max(0.01, p.weight + (Math.random() - 0.5) * 0.1)
    }));
  }

  const finalCheck = checkHandshake(current, threshold);
  return {
    converged: false,
    cycles: maxCycles,
    result: current,
    confidence: finalCheck.confidence,
    history
  };
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
        name: "particle-attention", version: VERSION, layer: "L5",
        description: "MR.liou 注意力機制", philosophy: "怎麼過去就怎麼回來",
        vs_transformer: { traditional: "Q·K·V 固定一次算完靜態權重", mrliou: "FOCUS→CHECK→SPREAD→REWEIGHT 迴圈直到 handshake" },
        cycle: ["FOCUS", "CHECK_HANDSHAKE", "SPREAD", "REWEIGHT"],
        strategies: Object.keys(STRATEGIES),
        endpoints: ["/focus", "/spread", "/reweight", "/check", "/loop"],
        origin_signature: "MrLiouWord", runtime: "DL580-local"
      });
    }

    if (path === "/health") {
      return json({ status: "healthy", name: "particle-attention", version: VERSION, origin_signature: "MrLiouWord", runtime: "DL580-local", timestamp: new Date().toISOString() });
    }

    if (request.method !== "POST") return json({ error: "POST required" }, 405);

    let body;
    try { body = await request.json(); } catch { return json({ error: "invalid JSON" }, 400); }

    const particles = body.particles || [{ id: "default", weight: 1 }];

    if (path === "/focus") {
      return json({ success: true, result: focus(particles, body.target), origin_signature: "MrLiouWord" });
    }
    if (path === "/check") {
      return json({ success: true, result: checkHandshake(particles, body.threshold), origin_signature: "MrLiouWord" });
    }
    if (path === "/spread") {
      return json({ success: true, result: spread(particles, body.strategy), origin_signature: "MrLiouWord" });
    }
    if (path === "/reweight") {
      return json({ success: true, result: reweight(particles, body.adjustments || {}), origin_signature: "MrLiouWord" });
    }
    if (path === "/loop") {
      const result = attentionLoop(particles, body.max_cycles || 10, body.strategy || "normalize", body.threshold || 0.7);
      return json({ success: true, ...result, origin_signature: "MrLiouWord" });
    }

    return json({ error: "route not found", path }, 404);
  }
};
