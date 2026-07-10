$f = "D:\mrl\bridge\server.js"
$c = [System.IO.File]::ReadAllText($f, [System.Text.Encoding]::UTF8)

# 版本號
$c = $c.Replace("const VERSION = 3.0.0", "const VERSION = 3.1.0")

# 找插入點：pgPool.on error 那段結束後
$insertCode = @"

// ── MRL v3.1: 動態多DB連線池 ──
const MRL_ALLOWED_DBS = [mrl_baseworld,mrl_vector,mrl_particle,mrl_librarian,mrl_api_transformer,mrl_particle_transformer,mrl_claude_reverse];
const dbPools = new Map();
dbPools.set(mrl_baseworld, pgPool);
function getDbPool(dbName) {
  if (!dbName || dbName === mrl_baseworld) return pgPool;
  if (!MRL_ALLOWED_DBS.includes(dbName)) return null;
  if (dbPools.has(dbName)) return dbPools.get(dbName);
  const p = new Pool({ host:127.0.0.1, port:5432, database:dbName, user:mrl_root, password:REDACTED_USE_ENV, max:3, idleTimeoutMillis:60000 });
  p.on(error, (e) => log(PG_POOL_ERROR_+dbName, e.message));
  dbPools.set(dbName, p);
  return p;
}

"@

# 在 Redis 定義之前插入
$marker = "// ─────────────────────────────────────────────`n// Redis"
$c = $c.Replace($marker, $insertCode + $marker)

# 修改 /pg GET 端點：加 db 參數支援
$oldPg = "app.get(/pg, auth, async (req, res) => {`n  const sql = req.query.sql;`n  if (!sql) return fail(res, 400, need ?sql= parameter);"
$newPg = "app.get(/pg, auth, async (req, res) => {`n  const sql = req.query.sql;`n  const dbName = req.query.db || mrl_baseworld;`n  if (!sql) return fail(res, 400, need ?sql= parameter);"
$c = $c.Replace($oldPg, $newPg)

# 修改 pgPool.query 為動態池（GET /pg 裡面那個）
$oldQuery = "log(PG_GET, sql, req);`n  try {`n    const r = await pgPool.query(sql);"
$newQuery = "const pool = getDbPool(dbName);`n  if (!pool) return fail(res, 400, unknown db:  + dbName + . Allowed:  + MRL_ALLOWED_DBS.join(,));`n  log(PG_GET, dbName + :  + sql, req);`n  try {`n    const r = await pool.query(sql);"
$c = $c.Replace($oldQuery, $newQuery)

# 修改 POST /pg/query 也支援多DB
$oldPost = "app.post(/pg/query, auth, async (req, res) => {`n  try {`n    const { sql, params } = req.body;"
$newPost = "app.post(/pg/query, auth, async (req, res) => {`n  try {`n    const { sql, params, db } = req.body;`n    const dbName = db || mrl_baseworld;"
$c = $c.Replace($oldPost, $newPost)

$oldPostQuery = "log(PG_POST, sql, req);`n    const r = await pgPool.query(sql, params || []);"
$newPostQuery = "const pool = getDbPool(dbName);`n    if (!pool) return fail(res, 400, unknown db:  + dbName);`n    log(PG_POST, dbName + :  + sql, req);`n    const r = await pool.query(sql, params || []);"
$c = $c.Replace($oldPostQuery, $newPostQuery)

[System.IO.File]::WriteAllText($f, $c, [System.Text.Encoding]::UTF8)
Write-Output "v3.1 patch complete"
