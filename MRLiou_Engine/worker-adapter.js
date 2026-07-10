/**
 * worker-adapter.js — CF Worker → Express 轉譯層
 *
 * 讓 Cloudflare Worker 代碼直接在 Node.js/Express 上跑
 * 不改原始 Worker 一行代碼
 *
 * 轉換:
 *   - export default { fetch(request, env) } → Express middleware
 *   - KV namespace → Redis
 *   - D1 → PostgreSQL
 *   - Service Bindings → 直接函數呼叫（零延遲）
 *   - AbortSignal.timeout → Node.js AbortController
 *
 * origin_signature: MrLiouWord
 */

import Redis from "ioredis";
import pg from "pg";

// ─── KV Shim (Redis-backed) ───
export class KVShim {
  constructor(redis, prefix) {
    this.redis = redis;
    this.prefix = prefix;
  }

  async get(key, opts) {
    const val = await this.redis.get(`${this.prefix}:${key}`);
    if (!val) return null;
    if (opts === "json" || opts?.type === "json") {
      try { return JSON.parse(val); } catch { return val; }
    }
    return val;
  }

  async put(key, value, opts) {
    const k = `${this.prefix}:${key}`;
    const v = typeof value === "object" ? JSON.stringify(value) : String(value);
    if (opts?.expirationTtl) {
      await this.redis.setex(k, opts.expirationTtl, v);
    } else {
      await this.redis.set(k, v);
    }
  }

  async delete(key) {
    await this.redis.del(`${this.prefix}:${key}`);
  }

  async list(opts) {
    const prefix = opts?.prefix ? `${this.prefix}:${opts.prefix}` : `${this.prefix}:`;
    const keys = await this.redis.keys(`${prefix}*`);
    return {
      keys: keys.map(k => ({ name: k.replace(`${this.prefix}:`, "") })),
      list_complete: true
    };
  }
}

// ─── D1 Shim (PostgreSQL-backed) ───
export class D1Shim {
  constructor(pool) {
    this.pool = pool;
  }

  prepare(sql) {
    return new D1PreparedStatement(this.pool, sql);
  }

  async exec(sql) {
    const result = await this.pool.query(sql);
    return { success: true, results: result.rows };
  }

  async batch(statements) {
    const client = await this.pool.connect();
    try {
      await client.query("BEGIN");
      const results = [];
      for (const stmt of statements) {
        const r = await client.query(stmt.sql, stmt.params || []);
        results.push({ success: true, results: r.rows });
      }
      await client.query("COMMIT");
      return results;
    } catch (e) {
      await client.query("ROLLBACK");
      throw e;
    } finally {
      client.release();
    }
  }
}

class D1PreparedStatement {
  constructor(pool, sql) {
    this.pool = pool;
    // Convert CF D1 ? params to PostgreSQL $1, $2...
    let idx = 0;
    this.sql = sql.replace(/\?/g, () => `$${++idx}`);
    this.params = [];
  }

  bind(...args) {
    this.params = args;
    return this;
  }

  async first(col) {
    const result = await this.pool.query(this.sql, this.params);
    if (result.rows.length === 0) return null;
    return col ? result.rows[0][col] : result.rows[0];
  }

  async all() {
    const result = await this.pool.query(this.sql, this.params);
    return { success: true, results: result.rows };
  }

  async run() {
    const result = await this.pool.query(this.sql, this.params);
    return { success: true, meta: { changes: result.rowCount } };
  }
}

// ─── Service Binding Shim (direct function call) ───
export class ServiceBindingShim {
  constructor(workerModule) {
    this.module = workerModule;
  }

  async fetch(requestOrUrl, init) {
    const req = requestOrUrl instanceof Request
      ? requestOrUrl
      : new Request(requestOrUrl, init);
    // Direct call — no HTTP overhead, no subdomain, no 1042 bug
    return this.module.fetch(req, this.module._env || {});
  }
}

// ─── Build env object for a Worker ───
export function buildEnv(redis, pgPool, workerRegistry, config = {}) {
  const env = {};

  // KV namespaces
  if (config.kv) {
    for (const [name, prefix] of Object.entries(config.kv)) {
      env[name] = new KVShim(redis, prefix);
    }
  }

  // D1 databases
  if (config.d1) {
    for (const name of config.d1) {
      env[name] = new D1Shim(pgPool);
    }
  }

  // Service Bindings (direct function calls)
  if (config.bindings) {
    for (const [name, workerId] of Object.entries(config.bindings)) {
      const target = workerRegistry[workerId];
      if (target) {
        env[name] = new ServiceBindingShim(target);
      }
    }
  }

  // Extra env vars
  if (config.vars) {
    Object.assign(env, config.vars);
  }

  return env;
}

// ─── Convert CF Worker → Express middleware ───
export function workerToMiddleware(workerModule, env) {
  // Store env reference on module for ServiceBindingShim
  workerModule._env = env;

  return async (req, res) => {
    try {
      // Build CF-compatible Request from Express req
      const url = `${req.protocol}://${req.hostname}${req.originalUrl}`;
      const headers = new Headers();
      for (const [k, v] of Object.entries(req.headers)) {
        if (typeof v === "string") headers.set(k, v);
      }

      const init = {
        method: req.method,
        headers
      };

      // Include body for POST/PUT/PATCH
      if (["POST", "PUT", "PATCH"].includes(req.method) && req.body) {
        init.body = JSON.stringify(req.body);
        headers.set("Content-Type", "application/json");
      }

      const cfRequest = new Request(url, init);

      // Call the Worker's fetch handler
      const handler = workerModule.default || workerModule;
      const fetchFn = typeof handler === "function" ? handler : handler.fetch;
      const response = await fetchFn.call(handler, cfRequest, env);

      // Convert CF Response → Express response
      res.status(response.status);
      for (const [k, v] of response.headers.entries()) {
        res.setHeader(k, v);
      }

      const body = await response.text();
      res.send(body);
    } catch (err) {
      console.error(`[Worker Error] ${req.path}:`, err.message);
      res.status(500).json({
        success: false,
        error: err.message,
        origin_signature: "MrLiouWord"
      });
    }
  };
}
