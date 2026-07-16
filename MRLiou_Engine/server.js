/**
 * MRL ASI Particle Engine — DL580 G9 Self-Hosted Runtime
 *
 * 單進程載入所有粒子Worker模組，統一路由
 * CF Workers 代碼零修改直接跑
 *
 * Architecture:
 *   Express Server (port 7700)
 *     ├── /hub/*        → particle-system-hub v2.2
 *     ├── /kernel/*     → mrl-kernel v2.0
 *     ├── /router/*     → particle-toolbox-router v1.1
 *     ├── /collapse/*   → collapse-engine v2.1.1 (待載入)
 *     ├── /auth/*       → auth-gateway v1.1 (待載入)
 *     ├── /simhash/*    → particle-simhash (待載入)
 *     ├── /pvm/*        → particle-pvm (待載入)
 *     ├── /attention/*  → particle-attention (待載入)
 *     └── /health       → 全局健康
 *
 * env shim:
 *   KV → Redis (port 6379)
 *   D1 → PostgreSQL (port 5432)
 *   Service Bindings → 直接函數呼叫
 *
 * origin_signature: MrLiouWord
 * 怎麼過去就怎麼回來
 */

import express from "express";
import cors from "cors";
import compression from "compression";
import Redis from "ioredis";
import pg from "pg";
import { buildEnv, workerToMiddleware } from "./worker-adapter.js";

const PORT = process.env.PORT || 7700;
const REDIS_URL = process.env.REDIS_URL || "redis://localhost:6379";
const PG_URL = process.env.DATABASE_URL || "postgresql://mrl:mrl@localhost:5432/mrliouword";

// ─── Connections ───
let redis, pgPool;

async function initConnections() {
  // Redis for KV
  redis = new Redis(REDIS_URL, {
    maxRetriesPerRequest: null,
    retryStrategy: (times) => {
      if (times > 3) return null; // Stop retrying after 3 attempts
      return Math.min(times * 200, 2000);
    },
    lazyConnect: true,
    enableOfflineQueue: false
  });

  redis.on("error", () => {}); // Suppress repeated error logs

  try {
    await redis.connect();
    console.log("[Redis] Connected");
  } catch (e) {
    console.log(`[Redis] Not available — using in-memory fallback`);
    redis.disconnect().catch(() => {});
    redis = createMemoryRedis();
  }

  // PostgreSQL for D1
  pgPool = new pg.Pool({
    connectionString: PG_URL,
    max: 20,
    idleTimeoutMillis: 30000
  });

  try {
    const client = await pgPool.connect();
    client.release();
    console.log("[PostgreSQL] Connected");
  } catch (e) {
    console.warn(`[PostgreSQL] Not available (${e.message}) — D1 shim disabled`);
    pgPool = null;
  }
}

// In-memory Redis fallback (for dev/testing without Redis)
function createMemoryRedis() {
  const store = new Map();
  return {
    async get(key) { return store.get(key) || null; },
    async set(key, val) { store.set(key, val); },
    async setex(key, ttl, val) { store.set(key, val); setTimeout(() => store.delete(key), ttl * 1000); },
    async del(key) { store.delete(key); },
    async keys(pattern) {
      const prefix = pattern.replace("*", "");
      return [...store.keys()].filter(k => k.startsWith(prefix));
    }
  };
}

// ─── Worker Registry ───
const workerRegistry = {};

async function loadWorker(id, modulePath, envConfig) {
  try {
    const mod = await import(modulePath);
    const env = buildEnv(redis, pgPool, workerRegistry, envConfig);
    const handler = mod.default || mod;
    if (handler._env !== undefined || handler.fetch) {
      handler._env = env;
    }
    workerRegistry[id] = handler;
    console.log(`[Worker] Loaded: ${id}`);
    return { module: mod, env, handler };
  } catch (e) {
    console.error(`[Worker] Failed to load ${id}: ${e.message}`);
    return null;
  }
}

// ─── Main ───
async function main() {
  console.log("╔══════════════════════════════════════════════════════════╗");
  console.log("║  MRL ASI Particle Engine — DL580 G9 Self-Hosted        ║");
  console.log("║  origin_signature: MrLiouWord                          ║");
  console.log("║  怎麼過去就怎麼回來                                      ║");
  console.log("╚══════════════════════════════════════════════════════════╝");
  console.log("");

  await initConnections();

  const app = express();
  app.use(cors());
  app.use(compression());
  app.use(express.json({ limit: "50mb" }));

  // ── Load Workers ──
  const workers = {};

  // Common binding config (all Workers can call each other directly)
  const commonBindings = {
    KERNEL: "mrl-kernel",
    AUTH_GATEWAY: "particle-auth-gateway",
    SYSTEM_HUB: "particle-system-hub",
    SIMHASH: "particle-simhash",
    REVERSIBLE: "particle-reversible",
    ATTENTION: "particle-attention",
    PVM: "particle-pvm",
    COLLAPSE_ENGINE: "mrl-particle-collapse-engine",
    METAENV: "metaenv-ctrl",
    CLOUD_BRIDGE: "mrl-cloud-bridge",
    NETWORK_LAYER: "mrl-network-layer",
    LIBRARIAN: "mrl-librarian",
    GLOBE: "mrl-globe",
    OBSERVER: "mrl-observer",
    SYNC_ENGINE: "mrl-sync-engine",
    HEALTH_MONITOR: "mrl-health-monitor",
    TOOLBOX: "particle-toolbox-router"
  };

  const commonKV = {
    VAULT: "mrliouword-vault",
    AUTH_VAULT: "particle-auth-vault"
  };

  const envConfig = {
    kv: commonKV,
    d1: pgPool ? ["DB"] : [],
    bindings: commonBindings,
    vars: {
      METAENV_ENDPOINT: "http://localhost:7700/metaenv",
      ORIGIN_SIGNATURE: "MrLiouWord"
    }
  };

  // Load core Workers from ./workers/ directory
  const workerList = [
    { id: "particle-system-hub", path: "./workers/system-hub.js", route: "/hub" },
    { id: "mrl-kernel", path: "./workers/kernel.js", route: "/kernel" },
    { id: "particle-toolbox-router", path: "./workers/toolbox-router.js", route: "/router" },
    { id: "particle-simhash", path: "./workers/simhash.js", route: "/simhash" },
    { id: "particle-attention", path: "./workers/attention.js", route: "/attention" },
    { id: "particle-reversible", path: "./workers/reversible.js", route: "/reversible" },
    { id: "particle-pvm", path: "./workers/pvm.js", route: "/pvm" }
  ];

  for (const w of workerList) {
    const loaded = await loadWorker(w.id, w.path, envConfig);
    if (loaded) {
      workers[w.id] = loaded;
      // Mount Worker — all paths including root
      const handler = (req, res) => {
        // Rewrite path: /hub/layers → /layers, /hub → /
        let newPath = req.originalUrl.replace(w.route, "") || "/";
        if (newPath === "") newPath = "/";
        req.url = newPath;
        req.originalUrl = newPath;
        workerToMiddleware(loaded.handler, loaded.env)(req, res);
      };
      app.all(`${w.route}`, handler);
      app.all(`${w.route}/*`, handler);
    }
  }

  // ── Global Health ──
  app.get("/health", (req, res) => {
    const loaded = Object.keys(workers);
    res.json({
      status: "healthy",
      service: "mrl-dl580-engine",
      version: "1.0.0",
      origin_signature: "MrLiouWord",
      philosophy: "怎麼過去就怎麼回來",
      runtime: "Node.js DL580 G9",
      workers_loaded: loaded.length,
      workers: loaded,
      connections: {
        redis: redis ? "connected" : "memory-fallback",
        postgresql: pgPool ? "connected" : "disabled"
      },
      uptime: process.uptime(),
      memory: {
        rss_mb: Math.round(process.memoryUsage().rss / 1024 / 1024),
        heap_mb: Math.round(process.memoryUsage().heapUsed / 1024 / 1024)
      },
      timestamp: new Date().toISOString()
    });
  });

  // ── Root: Engine Info ──
  app.get("/", (req, res) => {
    const loaded = Object.keys(workers);
    res.json({
      engine: "MRL ASI Particle Engine",
      version: "1.0.0",
      origin_signature: "MrLiouWord",
      philosophy: "怎麼過去就怎麼回來",
      host: "DL580 G9 (96 cores / 3TB RAM / 6×V100 GPU)",
      laws: [
        "LAW-0: origin_signature invariant",
        "LAW-1: verifiable",
        "LAW-2: fully reversible"
      ],
      closure_laws: [
        "AUTHORITY_INVARIANCE: ROOT 不可被轉移、代理、隱藏",
        "NO_DELETE: 任何刪除都是對衝突的掩蓋",
        "ADDITIVE_RESOLUTION: 所有修正必須堆疊保留歷史"
      ],
      routes: {
        "/": "Engine info",
        "/health": "Global health check",
        "/hub": "particle-system-hub v2.2 (system map + health + topology)",
        "/hub/health": "System health probe (via Service Bindings)",
        "/hub/full-scan": "Full 144 Workers scan",
        "/hub/layers": "Layer overview L(-1) to L∞",
        "/hub/shells": "Shell Workers list",
        "/kernel": "mrl-kernel v2.0 (SINDy + Quantum + Attention + F++)",
        "/kernel/health": "Kernel health",
        "/kernel/run": "POST — Run kernel computation",
        "/router": "particle-toolbox-router v1.1 (Call/Pipeline/Parallel/Fan-out)",
        "/router/call": "POST — Single Worker call",
        "/router/pipeline": "POST — Sequential chain",
        "/router/parallel": "POST — Concurrent calls",
        "/router/fanout": "POST — Broadcast to many",
        "/router/registry": "Worker registry",
        "/simhash": "particle-simhash v1.1 (SimHash64 語意指紋)",
        "/simhash/hash": "POST — Compute SimHash64",
        "/simhash/compare": "POST — Compare two texts",
        "/simhash/batch": "POST — Batch hash",
        "/simhash/find-similar": "POST — Find similar in store",
        "/attention": "particle-attention v1.1 (FOCUS→CHECK→SPREAD→REWEIGHT)",
        "/attention/loop": "POST — Full attention loop",
        "/reversible": "particle-reversible v1.1 (可逆計算 20操作+逆映射)",
        "/reversible/execute": "POST — Execute reversible operation",
        "/reversible/undo": "POST — Undo last operation",
        "/pvm": "particle-pvm v1.1 (25 opcodes + 5 registers)",
        "/pvm/execute": "POST — Execute PVM program"
      },
      workers_loaded: loaded.length,
      timestamp: new Date().toISOString()
    });
  });

  // ── 404 ──
  app.use((req, res) => {
    res.status(404).json({
      error: "route not found",
      path: req.path,
      origin_signature: "MrLiouWord",
      available_routes: ["/", "/health", "/hub", "/hub/*", "/kernel", "/kernel/*", "/router", "/router/*"]
    });
  });

  // ── Start ──
  app.listen(PORT, "0.0.0.0", () => {
    console.log("");
    console.log(`  MRL ASI Engine running on http://0.0.0.0:${PORT}`);
    console.log(`  Workers loaded: ${Object.keys(workers).length}`);
    console.log(`  Redis: ${redis ? "connected" : "memory-fallback"}`);
    console.log(`  PostgreSQL: ${pgPool ? "connected" : "disabled"}`);
    console.log("");
    console.log("  origin_signature: MrLiouWord");
    console.log("  怎麼過去就怎麼回來");
    console.log("");
  });
}

main().catch(err => {
  console.error("Fatal:", err);
  process.exit(1);
});
