const fs = require("fs");
const f = "D:\\mrl\\bridge\\server.js";
let c = fs.readFileSync(f, "utf-8");

// 1. 版本號
c = c.replace("const VERSION = '3.0.0'", "const VERSION = '3.1.0'");

// 2. 在 Redis 區塊前插入動態DB池
const redisMarker = "// Redis\n// ─────";
const dbPoolCode = `// ── MRL v3.1: Dynamic Multi-DB Pool ──\nconst MRL_ALLOWED_DBS = ['mrl_baseworld','mrl_vector','mrl_particle','mrl_librarian','mrl_api_transformer','mrl_particle_transformer','mrl_claude_reverse'];\nconst dbPools = new Map();\ndbPools.set('mrl_baseworld', pgPool);\nfunction getDbPool(dbName) {\n  if (!dbName || dbName === 'mrl_baseworld') return pgPool;\n  if (!MRL_ALLOWED_DBS.includes(dbName)) return null;\n  if (dbPools.has(dbName)) return dbPools.get(dbName);\n  const p = new Pool({ host:'127.0.0.1', port:5432, database:dbName, user:'mrl_root', password:(process.env.MRL_BRIDGE_API_KEY || ''), max:3, idleTimeoutMillis:60000 });\n  p.on('error', (e) => log('PG_POOL_ERROR_'+dbName, e.message));\n  dbPools.set(dbName, p);\n  return p;\n}\n\n// ─────────────────────────────────────────────\n// `;
c = c.replace("// ─────────────────────────────────────────────\n// Redis\n// ─────", dbPoolCode + "Redis\n// ─────");

// 3. GET /pg: 加 db 參數
c = c.replace(
  "app.get('/pg', auth, async (req, res) => {\n  const sql = req.query.sql;\n  if (!sql) return fail(res, 400, 'need ?sql= parameter');",
  "app.get('/pg', auth, async (req, res) => {\n  const sql = req.query.sql;\n  const dbName = req.query.db || 'mrl_baseworld';\n  if (!sql) return fail(res, 400, 'need ?sql= parameter');"
);

// 4. GET /pg: pgPool.query → getDbPool
c = c.replace(
  "log('PG_GET', sql, req);\n  try {\n    const r = await pgPool.query(sql);",
  "const pool = getDbPool(dbName);\n  if (!pool) return fail(res, 400, 'unknown db: ' + dbName);\n  log('PG_GET', dbName + ': ' + sql, req);\n  try {\n    const r = await pool.query(sql);"
);

// 5. POST /pg/query: 加 db 參數
c = c.replace(
  "const { sql, params } = req.body;\n    if (!sql) return fail(res, 400, 'need sql');",
  "const { sql, params, db } = req.body;\n    const dbName = db || 'mrl_baseworld';\n    if (!sql) return fail(res, 400, 'need sql');"
);

// 6. POST /pg/query: pgPool.query → getDbPool
c = c.replace(
  "log('PG_POST', sql, req);\n    const r = await pgPool.query(sql, params || []);",
  "const pool = getDbPool(dbName);\n    if (!pool) return fail(res, 400, 'unknown db: ' + dbName);\n    log('PG_POST', dbName + ': ' + sql, req);\n    const r = await pool.query(sql, params || []);"
);

fs.writeFileSync(f, c, "utf-8");
console.log("v3.1 patch complete, size=" + c.length);
