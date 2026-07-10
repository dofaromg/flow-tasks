/**
 * particle-toolbox-router v1.0.0 — 粒子工具箱統一調度路由器
 *
 * Cross-Worker orchestration with 4 composition modes:
 *   Pipeline  — A → B → C (sequential, each output feeds next)
 *   Parallel  — A | B | C (concurrent, collect all results)
 *   Fan-out   — A → [B, C, D] (one input, broadcast to many)
 *   Retry     — A (retry with backoff on failure)
 *
 * Unified ParticleCall protocol:
 *   POST /call    — single Worker call
 *   POST /pipeline — sequential chain
 *   POST /parallel — concurrent execution
 *   POST /fanout   — broadcast to multiple
 *   GET  /health   — health check
 *   GET  /         — service info
 *   GET  /registry — list callable Workers
 *
 * origin_signature: MrLiouWord
 * layer: L3-Execution
 * 怎麼過去就怎麼回來
 */

const SUBDOMAIN = "z814241.workers.dev";
const VERSION = "1.1.0";
const MAX_RETRIES = 3;
const RETRY_BASE_MS = 200;
const CALL_TIMEOUT_MS = 8000;

// Registry of callable particle Workers with their primary endpoints
const REGISTRY = {
  // L(-1) MetaEnv
  "metaenv-ctrl":     { layer: "L(-1)", endpoints: ["/health", "/spawn", "/policy", "/attest", "/snapshot", "/channel", "/reverse", "/lockdown", "/backtrace"] },
  "collapse-engine":  { layer: "L(-1)", worker: "mrl-particle-collapse-engine", endpoints: ["/health", "/collapse", "/passport", "/signature"] },
  "cloud-bridge":     { layer: "L(-1)", worker: "mrl-cloud-bridge", endpoints: ["/health", "/guard", "/channel", "/reverse", "/isotope"] },
  "network-layer":    { layer: "L(-1)", worker: "mrl-network-layer", endpoints: ["/health", "/translate", "/merkle", "/route"] },

  // L0 Trust
  "auth-gateway":     { layer: "L0", worker: "particle-auth-gateway", endpoints: ["/health", "/status", "/init"] },
  "sig-verify":       { layer: "L0", worker: "particle-sig-verify", endpoints: ["/"] },

  // L1 Kernel
  "kernel":           { layer: "L1", worker: "mrl-kernel", endpoints: ["/health", "/run", "/amplify/scale-up", "/amplify/verify-reversible", "/reverse-mine"] },
  "atom":             { layer: "L1", worker: "particle-atom", endpoints: ["/"] },
  "boot":             { layer: "L1", worker: "particle-boot", endpoints: ["/"] },

  // L2 Memory
  "memory":           { layer: "L2", worker: "particle-memory", endpoints: ["/"] },
  "simhash":          { layer: "L2", worker: "particle-simhash", endpoints: ["/hash", "/compare", "/batch", "/find-similar"] },
  "reversible":       { layer: "L2", worker: "particle-reversible", endpoints: ["/execute", "/undo", "/redo", "/replay"] },
  "delta":            { layer: "L2", worker: "particle-delta", endpoints: ["/"] },

  // L3 Execution
  "pvm":              { layer: "L3", worker: "particle-pvm", endpoints: ["/execute", "/attention-loop"] },
  "attention":        { layer: "L3", worker: "particle-attention", endpoints: ["/focus", "/spread", "/reweight", "/check", "/loop"] },
  "chat":             { layer: "L3", worker: "particle-chat", endpoints: ["/"] },
  "ai-gateway":       { layer: "L3", worker: "particle-ai-gateway", endpoints: ["/"] },
  "sync-engine":      { layer: "L3", worker: "mrl-sync-engine", endpoints: ["/health"] },

  // L4 Interface
  "globe":            { layer: "L4", worker: "mrl-globe", endpoints: ["/health"] },
  "observer":         { layer: "L4", worker: "mrl-observer", endpoints: ["/health"] },

  // L5 Ecosystem
  "librarian":        { layer: "L5", worker: "mrl-librarian", endpoints: ["/health", "/search", "/index"] },
  "health-monitor":   { layer: "L5", worker: "mrl-health-monitor", endpoints: ["/health"] },
  "system-hub":       { layer: "L5", worker: "particle-system-hub", endpoints: ["/", "/health", "/layers", "/full-scan", "/shells", "/topology"] }
};

// Service Binding name mapping (alias → env binding name)
const ALIAS_TO_BINDING = {
  "kernel": "KERNEL",
  "auth-gateway": "AUTH_GATEWAY",
  "system-hub": "SYSTEM_HUB",
  "simhash": "SIMHASH",
  "reversible": "REVERSIBLE",
  "attention": "ATTENTION",
  "pvm": "PVM",
  "collapse-engine": "COLLAPSE_ENGINE",
  "metaenv-ctrl": "METAENV",
  "cloud-bridge": "CLOUD_BRIDGE",
  "network-layer": "NETWORK_LAYER",
  "librarian": "LIBRARIAN",
  "globe": "GLOBE",
  "observer": "OBSERVER",
  "sync-engine": "SYNC_ENGINE",
  "health-monitor": "HEALTH_MONITOR"
};

// Resolve Worker URL from alias
function resolveWorker(alias) {
  const entry = REGISTRY[alias];
  if (!entry) return null;
  const workerName = entry.worker || `particle-${alias}`;
  return { name: workerName, url: `https://${workerName}.${SUBDOMAIN}`, ...entry };
}

// Global env ref (set per request)
let _env = null;

// Single call with retry — uses Service Bindings when available, fallback to subdomain
async function callWorker(alias, endpoint, method = "GET", body = null, retries = MAX_RETRIES) {
  const resolved = resolveWorker(alias);
  if (!resolved) {
    return { success: false, error: `Unknown particle: ${alias}`, alias };
  }

  const bindingName = ALIAS_TO_BINDING[alias];
  const binding = bindingName && _env ? _env[bindingName] : null;
  const url = `${resolved.url}${endpoint}`;
  let lastError = null;

  for (let attempt = 0; attempt <= retries; attempt++) {
    if (attempt > 0) {
      await new Promise(r => setTimeout(r, RETRY_BASE_MS * Math.pow(2, attempt - 1)));
    }

    const start = Date.now();
    try {
      const opts = {
        method,
        signal: AbortSignal.timeout(CALL_TIMEOUT_MS),
        headers: {
          "Content-Type": "application/json",
          "X-Particle-Router": "toolbox-router/1.0",
          "X-Origin-Signature": "MrLiouWord"
        }
      };
      if (body && method !== "GET") {
        opts.body = JSON.stringify(body);
      }

      // Use Service Binding if available (avoids subdomain 1042 bug)
      // binding.fetch() takes a Request or URL relative to the Worker
      const resp = binding
        ? await binding.fetch(new Request(`https://internal${endpoint}`, opts))
        : await fetch(url, opts);
      const ms = Date.now() - start;

      let data;
      const contentType = resp.headers.get("content-type") || "";
      if (contentType.includes("json")) {
        data = await resp.json();
      } else {
        data = await resp.text();
      }

      if (resp.ok) {
        return {
          success: true,
          alias,
          worker: resolved.name,
          endpoint,
          http: resp.status,
          ms,
          attempt: attempt + 1,
          data
        };
      }

      // Non-OK but got response
      lastError = { http: resp.status, data, ms };

      // Don't retry on 4xx (client errors)
      if (resp.status >= 400 && resp.status < 500) break;

    } catch (e) {
      lastError = { error: e.message, ms: Date.now() - start };
    }
  }

  return {
    success: false,
    alias,
    worker: resolved.name,
    endpoint,
    attempts: retries + 1,
    lastError
  };
}

// Pipeline: A → B → C (sequential, output of each feeds into next)
async function executePipeline(steps) {
  const results = [];
  let previousOutput = null;

  for (const step of steps) {
    const body = step.body || previousOutput;
    const result = await callWorker(
      step.alias,
      step.endpoint,
      step.method || "POST",
      body,
      step.retries ?? 1
    );
    results.push(result);

    if (!result.success) {
      return {
        mode: "pipeline",
        success: false,
        completed: results.length - 1,
        total: steps.length,
        failed_at: step.alias,
        results
      };
    }
    previousOutput = result.data;
  }

  return {
    mode: "pipeline",
    success: true,
    completed: results.length,
    total: steps.length,
    final_output: previousOutput,
    results
  };
}

// Parallel: A | B | C (concurrent, collect all)
async function executeParallel(calls) {
  const promises = calls.map(c =>
    callWorker(c.alias, c.endpoint, c.method || "GET", c.body || null, c.retries ?? 1)
  );

  const results = await Promise.allSettled(promises);
  const outputs = results.map((r, i) => {
    if (r.status === "fulfilled") return r.value;
    return { success: false, alias: calls[i].alias, error: String(r.reason) };
  });

  const succeeded = outputs.filter(o => o.success).length;

  return {
    mode: "parallel",
    success: succeeded === outputs.length,
    succeeded,
    failed: outputs.length - succeeded,
    total: outputs.length,
    results: outputs
  };
}

// Fan-out: one input → broadcast to many Workers
async function executeFanout(input, targets) {
  const calls = targets.map(t => ({
    alias: t.alias,
    endpoint: t.endpoint,
    method: t.method || "POST",
    body: input,
    retries: t.retries ?? 1
  }));
  const result = await executeParallel(calls);
  result.mode = "fanout";
  result.input = input;
  return result;
}

// ─── Route Handler ───
export default {
  async fetch(request, env) {
    _env = env;  // Make env available for Service Bindings in callWorker
    const url = new URL(request.url);
    const path = url.pathname;

    const cors = {
      "Content-Type": "application/json; charset=utf-8",
      "Access-Control-Allow-Origin": "*",
      "X-Particle-Router": `toolbox-router/${VERSION}`,
      "X-Origin-Signature": "MrLiouWord"
    };

    if (request.method === "OPTIONS") {
      return new Response(null, { headers: { ...cors, "Access-Control-Allow-Methods": "GET, POST, OPTIONS" } });
    }

    const json = (data, status = 200) => new Response(JSON.stringify(data, null, 2), { status, headers: cors });

    // ── Root: Service Info ──
    if (path === "/" || path === "") {
      return json({
        service: "particle-toolbox-router",
        version: VERSION,
        layer: "L3-Execution",
        origin_signature: "MrLiouWord",
        philosophy: "怎麼過去就怎麼回來",
        description: "跨Worker統一調度路由器 — 四種組合模式",
        modes: {
          call: "POST /call — single Worker call with retry",
          pipeline: "POST /pipeline — sequential A→B→C (output feeds next)",
          parallel: "POST /parallel — concurrent A|B|C (collect all)",
          fanout: "POST /fanout — one input broadcast to many"
        },
        endpoints: ["/", "/health", "/registry", "/call", "/pipeline", "/parallel", "/fanout"],
        registry_count: Object.keys(REGISTRY).length,
        service_bindings: Object.keys(ALIAS_TO_BINDING).length,
        timestamp: new Date().toISOString()
      });
    }

    // ── Health ──
    if (path === "/health") {
      return json({
        status: "healthy",
        service: "particle-toolbox-router",
        version: VERSION,
        origin_signature: "MrLiouWord",
        layer: "L3-Execution",
        registry_count: Object.keys(REGISTRY).length,
        timestamp: new Date().toISOString()
      });
    }

    // ── Registry ──
    if (path === "/registry") {
      const registry = {};
      for (const [alias, entry] of Object.entries(REGISTRY)) {
        registry[alias] = {
          layer: entry.layer,
          worker: entry.worker || `particle-${alias}`,
          url: `https://${entry.worker || `particle-${alias}`}.${SUBDOMAIN}`,
          endpoints: entry.endpoints
        };
      }
      return json({
        service: "particle-toolbox-router",
        origin_signature: "MrLiouWord",
        timestamp: new Date().toISOString(),
        count: Object.keys(registry).length,
        registry
      });
    }

    // ── POST /call — Single call ──
    if (path === "/call" && request.method === "POST") {
      try {
        const { alias, endpoint, method, body, retries } = await request.json();
        if (!alias || !endpoint) {
          return json({ success: false, error: "Required: alias, endpoint" }, 400);
        }
        const result = await callWorker(alias, endpoint, method || "GET", body, retries ?? MAX_RETRIES);
        return json(result, result.success ? 200 : 502);
      } catch (e) {
        return json({ success: false, error: e.message }, 400);
      }
    }

    // ── POST /pipeline — Sequential chain ──
    if (path === "/pipeline" && request.method === "POST") {
      try {
        const { steps } = await request.json();
        if (!steps || !Array.isArray(steps) || steps.length === 0) {
          return json({ success: false, error: "Required: steps[] with {alias, endpoint, method?, body?, retries?}" }, 400);
        }
        if (steps.length > 10) {
          return json({ success: false, error: "Max 10 pipeline steps" }, 400);
        }
        const result = await executePipeline(steps);
        return json(result, result.success ? 200 : 502);
      } catch (e) {
        return json({ success: false, error: e.message }, 400);
      }
    }

    // ── POST /parallel — Concurrent calls ──
    if (path === "/parallel" && request.method === "POST") {
      try {
        const { calls } = await request.json();
        if (!calls || !Array.isArray(calls) || calls.length === 0) {
          return json({ success: false, error: "Required: calls[] with {alias, endpoint, method?, body?, retries?}" }, 400);
        }
        if (calls.length > 20) {
          return json({ success: false, error: "Max 20 parallel calls" }, 400);
        }
        const result = await executeParallel(calls);
        return json(result, result.success ? 200 : 207);
      } catch (e) {
        return json({ success: false, error: e.message }, 400);
      }
    }

    // ── POST /fanout — Broadcast ──
    if (path === "/fanout" && request.method === "POST") {
      try {
        const { input, targets } = await request.json();
        if (!targets || !Array.isArray(targets) || targets.length === 0) {
          return json({ success: false, error: "Required: input (any), targets[] with {alias, endpoint}" }, 400);
        }
        if (targets.length > 20) {
          return json({ success: false, error: "Max 20 fanout targets" }, 400);
        }
        const result = await executeFanout(input, targets);
        return json(result, result.success ? 200 : 207);
      } catch (e) {
        return json({ success: false, error: e.message }, 400);
      }
    }

    // ── 404 ──
    return json({
      error: "route not found",
      path,
      origin_signature: "MrLiouWord",
      endpoints: ["/", "/health", "/registry", "POST /call", "POST /pipeline", "POST /parallel", "POST /fanout"]
    }, 404);
  }
};
