// ╔══════════════════════════════════════════════════════════════╗
// ║  MRL_Bridge_API v3.0.0                                     ║
// ║  origin_signature: MrLiouWord                              ║
// ║  歸屬：MRL系統 / DL580 母體通道層                             ║
// ║  用途：Claude ↔ Cloudflare Tunnel ↔ DL580 全鏈路操作通道     ║
// ║  能力：檔案讀寫、PG查詢、Redis操作、指令執行、系統監控        ║
// ║  認證：API Key SHA-256 (header x-api-key 或 query ?key=)    ║
// ║  模式：GET + POST 雙模式 (GET 供 Claude web_fetch)          ║
// ║  port: 7800                                                 ║
// ║  建立日期: 2026-04-05                                       ║
// ╚══════════════════════════════════════════════════════════════╝

const express = require('express');
const fs = require('fs');
const path = require('path');
const os = require('os');
const { execSync } = require('child_process');
const crypto = require('crypto');
const { Pool } = require('pg');
const Redis = require('ioredis');

// ─────────────────────────────────────────────
// 常數
// ─────────────────────────────────────────────
const VERSION = '3.0.0';
const PORT = 7800;
const ORIGIN = 'MrLiouWord';
const API_KEY_HASH = crypto.createHash('sha256').update((process.env.MRL_BRIDGE_API_KEY || '')).digest('hex');
const LOG_DIR = path.join('D:', 'mrl', 'bridge', 'logs');
const MAX_FILE_READ = 5 * 1024 * 1024;
const MAX_EXEC_TIMEOUT = 30000;
const RATE_WINDOW_MS = 60 * 1000;
const RATE_MAX = 120;
const BOOT_TIME = new Date();

// 請求計數器
const stats = { total: 0, success: 0, error: 0, blocked: 0 };

// ─────────────────────────────────────────────
// 初始化
// ─────────────────────────────────────────────
if (!fs.existsSync(LOG_DIR)) fs.mkdirSync(LOG_DIR, { recursive: true });

const app = express();
app.use(express.json({ limit: '10mb' }));
app.use(express.text({ limit: '10mb' }));
app.disable('x-powered-by');

// ─────────────────────────────────────────────
// PostgreSQL 連線池
// ─────────────────────────────────────────────
const pgPool = new Pool({
  host: '127.0.0.1',
  port: 5432,
  database: 'mrl_baseworld',
  user: 'mrl_root',
  password: (process.env.MRL_BRIDGE_API_KEY || ''),
  max: 10,
  idleTimeoutMillis: 30000,
  connectionTimeoutMillis: 5000,
});

pgPool.on('error', (err) => {
  log('PG_POOL_ERROR', err.message);
});

// ─────────────────────────────────────────────
// Redis
// ─────────────────────────────────────────────
const redis = new Redis({
  host: '127.0.0.1',
  port: 6379,
  maxRetriesPerRequest: 3,
  lazyConnect: true,
  retryStrategy: (times) => Math.min(times * 500, 3000),
});

redis.on('error', (err) => {
  log('REDIS_ERROR', err.message);
});

// ─────────────────────────────────────────────
// 審計日誌（每日 JSONL + 7天自動旋轉）
// ─────────────────────────────────────────────
function log(action, detail, req) {
  const entry = {
    t: new Date().toISOString(),
    action,
    detail: typeof detail === 'object' ? detail : { msg: detail },
  };
  if (req) {
    entry.ip = req.ip || req.connection.remoteAddress || '-';
    entry.method = req.method;
    entry.path = req.originalUrl ? req.originalUrl.split('?')[0] : req.path;
  }
  const line = JSON.stringify(entry) + '\n';
  const logFile = path.join(LOG_DIR, `bridge_${new Date().toISOString().slice(0, 10)}.jsonl`);
  try { fs.appendFileSync(logFile, line, 'utf-8'); } catch (_) { /* silent */ }
}

function rotateLogs() {
  try {
    const cutoff = Date.now() - 7 * 24 * 60 * 60 * 1000;
    const files = fs.readdirSync(LOG_DIR).filter(f => f.startsWith('bridge_') && f.endsWith('.jsonl'));
    for (const f of files) {
      const fPath = path.join(LOG_DIR, f);
      const st = fs.statSync(fPath);
      if (st.mtimeMs < cutoff) {
        fs.unlinkSync(fPath);
        log('LOG_ROTATED', f);
      }
    }
  } catch (_) { /* silent */ }
}

// 每6小時旋轉一次
setInterval(rotateLogs, 6 * 60 * 60 * 1000);

// ─────────────────────────────────────────────
// CORS
// ─────────────────────────────────────────────
app.use((req, res, next) => {
  res.header('Access-Control-Allow-Origin', '*');
  res.header('Access-Control-Allow-Methods', 'GET,POST,OPTIONS');
  res.header('Access-Control-Allow-Headers', 'Content-Type,x-api-key');
  res.header('X-MRL-Bridge-Version', VERSION);
  if (req.method === 'OPTIONS') return res.sendStatus(204);
  stats.total++;
  next();
});

// ─────────────────────────────────────────────
// 速率限制
// ─────────────────────────────────────────────
const rateMap = new Map();

function rateLimit(req, res, next) {
  const key = req.ip || 'unknown';
  const now = Date.now();
  let rec = rateMap.get(key);
  if (!rec || now - rec.start > RATE_WINDOW_MS) {
    rec = { count: 1, start: now };
  } else {
    rec.count++;
  }
  rateMap.set(key, rec);

  res.header('X-RateLimit-Limit', String(RATE_MAX));
  res.header('X-RateLimit-Remaining', String(Math.max(0, RATE_MAX - rec.count)));
  res.header('X-RateLimit-Reset', String(Math.ceil((rec.start + RATE_WINDOW_MS) / 1000)));

  if (rec.count > RATE_MAX) {
    stats.blocked++;
    log('RATE_LIMITED', { ip: key, count: rec.count }, req);
    return res.status(429).json({ error: 'rate limit exceeded', limit: RATE_MAX, window: '60s', retryAfter: Math.ceil((rec.start + RATE_WINDOW_MS - now) / 1000) });
  }
  next();
}

// 定期清理過期速率記錄
setInterval(() => {
  const now = Date.now();
  for (const [k, v] of rateMap) {
    if (now - v.start > RATE_WINDOW_MS * 2) rateMap.delete(k);
  }
}, 5 * 60 * 1000);

app.use(rateLimit);

// ─────────────────────────────────────────────
// API Key 認證
// ─────────────────────────────────────────────
function auth(req, res, next) {
  const key = req.headers['x-api-key'] || req.query.key;
  if (!key) {
    stats.blocked++;
    log('AUTH_MISSING', '-', req);
    return res.status(401).json({ error: 'API key required. Header: x-api-key or query: ?key=YOUR_KEY' });
  }
  if (crypto.createHash('sha256').update(key).digest('hex') !== API_KEY_HASH) {
    stats.blocked++;
    log('AUTH_INVALID', '-', req);
    return res.status(403).json({ error: 'Invalid API key' });
  }
  next();
}

// ─────────────────────────────────────────────
// 安全閘門
// ─────────────────────────────────────────────
const SQL_BLOCKED = ['DROP DATABASE', 'DROP SCHEMA', 'TRUNCATE', 'ALTER SYSTEM', 'CREATE ROLE', 'DROP ROLE', 'COPY.*TO PROGRAM'];
const REDIS_BLOCKED = ['FLUSHALL', 'FLUSHDB', 'SHUTDOWN', 'DEBUG', 'CONFIG', 'SLAVEOF', 'REPLICAOF', 'MODULE', 'ACL'];

function sqlSafe(sql) {
  const up = sql.toUpperCase().replace(/\s+/g, ' ').trim();
  for (const pattern of SQL_BLOCKED) {
    if (new RegExp(pattern).test(up)) return false;
  }
  return true;
}

function redisSafe(cmd) {
  return !REDIS_BLOCKED.includes(cmd.toUpperCase());
}

// ─────────────────────────────────────────────
// 輔助函數
// ─────────────────────────────────────────────
function safePath(p) {
  // 禁止路徑穿越
  const resolved = path.resolve(p);
  if (resolved.includes('..')) return null;
  return resolved;
}

function fileInfo(filePath) {
  const st = fs.statSync(filePath);
  return {
    path: filePath,
    size: st.size,
    isDir: st.isDirectory(),
    modified: st.mtime.toISOString(),
    created: st.birthtime.toISOString(),
  };
}

function ok(res, data) {
  stats.success++;
  res.json({ ok: true, ...data, _v: VERSION, _t: new Date().toISOString() });
}

function fail(res, code, error) {
  stats.error++;
  res.status(code).json({ ok: false, error, _v: VERSION, _t: new Date().toISOString() });
}

// ═════════════════════════════════════════════
// PUBLIC ENDPOINTS（不需要 API Key）
// ═════════════════════════════════════════════

// GET /health
app.get('/health', async (req, res) => {
  const result = {
    service: 'MRL_Bridge_API',
    version: VERSION,
    origin_signature: ORIGIN,
    api: true,
    pg: false,
    redis: false,
    uptime: Math.round(process.uptime()),
    boot: BOOT_TIME.toISOString(),
    stats: { ...stats },
    timestamp: new Date().toISOString(),
  };

  try {
    const r = await pgPool.query('SELECT count(*)::int AS n FROM information_schema.tables WHERE table_schema=$1', ['public']);
    result.pg = true;
    result.pg_tables = r.rows[0].n;
    result.pg_pool = { total: pgPool.totalCount, idle: pgPool.idleCount, waiting: pgPool.waitingCount };
  } catch (e) { result.pg_error = e.message; }

  try {
    result.redis = (await redis.ping()) === 'PONG';
    const dbsize = await redis.dbsize();
    result.redis_keys = dbsize;
  } catch (e) { result.redis_error = e.message; }

  res.json(result);
});

// GET /version
app.get('/version', (req, res) => {
  res.json({
    service: 'MRL_Bridge_API',
    version: VERSION,
    origin_signature: ORIGIN,
    node: process.version,
    platform: process.platform,
    arch: process.arch,
    hostname: os.hostname(),
    endpoints: {
      public: ['GET /health', 'GET /version'],
      get: ['GET /pg', 'GET /ls', 'GET /cat', 'GET /run', 'GET /redis-cmd', 'GET /sysinfo', 'GET /write', 'GET /audit', 'GET /tables'],
      post: ['POST /file/write', 'POST /file/read', 'POST /file/list', 'POST /exec', 'POST /pg/query', 'POST /redis'],
    },
  });
});

// ═════════════════════════════════════════════
// GET ENDPOINTS（Claude web_fetch 專用）
// ═════════════════════════════════════════════

// GET /pg?sql=...&key=
app.get('/pg', auth, async (req, res) => {
  const sql = req.query.sql;
  if (!sql) return fail(res, 400, 'need ?sql= parameter');
  if (!sqlSafe(sql)) {
    log('SQL_BLOCKED', sql, req);
    stats.blocked++;
    return fail(res, 403, 'forbidden SQL operation');
  }
  log('PG_GET', sql, req);
  try {
    const r = await pgPool.query(sql);
    ok(res, {
      rowCount: r.rowCount,
      rows: r.rows,
      fields: r.fields ? r.fields.map(f => ({ name: f.name, dataTypeID: f.dataTypeID })) : [],
    });
  } catch (e) { fail(res, 500, e.message); }
});

// GET /tables?key= — 列出所有表與行數
app.get('/tables', auth, async (req, res) => {
  log('TABLES', 'list', req);
  try {
    const r = await pgPool.query(`
      SELECT schemaname, tablename,
        pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size,
        (SELECT count(*)::int FROM information_schema.columns c
         WHERE c.table_schema=t.schemaname AND c.table_name=t.tablename) AS columns
      FROM pg_tables t
      WHERE schemaname='public'
      ORDER BY tablename
    `);
    ok(res, { count: r.rowCount, tables: r.rows });
  } catch (e) { fail(res, 500, e.message); }
});

// GET /ls?path=D:\mrl&key=
app.get('/ls', auth, (req, res) => {
  const d = req.query.path || 'D:\\mrl';
  const sp = safePath(d);
  if (!sp) return fail(res, 400, 'invalid path');
  log('LS', d, req);
  try {
    if (!fs.existsSync(sp)) return fail(res, 404, 'path not found: ' + d);
    const st = fs.statSync(sp);
    if (!st.isDirectory()) return fail(res, 400, 'not a directory');
    const items = fs.readdirSync(sp, { withFileTypes: true }).map(i => {
      const full = path.join(sp, i.name);
      const info = { name: i.name, type: i.isDirectory() ? 'dir' : 'file' };
      try {
        const s = fs.statSync(full);
        if (i.isFile()) {
          info.size = s.size;
          info.sizeHuman = s.size > 1048576 ? (s.size / 1048576).toFixed(1) + 'MB' : s.size > 1024 ? (s.size / 1024).toFixed(1) + 'KB' : s.size + 'B';
        }
        info.modified = s.mtime.toISOString();
      } catch (_) { /* skip */ }
      return info;
    });
    ok(res, { path: d, count: items.length, dirs: items.filter(i => i.type === 'dir').length, files: items.filter(i => i.type === 'file').length, items });
  } catch (e) { fail(res, 500, e.message); }
});

// GET /cat?path=...&key=&lines=100&offset=0
app.get('/cat', auth, (req, res) => {
  const f = req.query.path;
  if (!f) return fail(res, 400, 'need ?path= parameter');
  const sp = safePath(f);
  if (!sp) return fail(res, 400, 'invalid path');
  log('CAT', f, req);
  try {
    if (!fs.existsSync(sp)) return fail(res, 404, 'file not found: ' + f);
    const st = fs.statSync(sp);
    if (st.isDirectory()) return fail(res, 400, 'is a directory, use /ls');
    if (st.size > MAX_FILE_READ) return fail(res, 413, 'file too large: ' + st.size + ' bytes, max ' + MAX_FILE_READ);
    let content = fs.readFileSync(sp, 'utf-8');

    // 支援行數截取
    const lines = parseInt(req.query.lines);
    const offset = parseInt(req.query.offset) || 0;
    let totalLines = null;
    if (lines > 0) {
      const allLines = content.split('\n');
      totalLines = allLines.length;
      content = allLines.slice(offset, offset + lines).join('\n');
    }

    const result = { path: f, size: st.size, modified: st.mtime.toISOString(), content };
    if (totalLines !== null) {
      result.totalLines = totalLines;
      result.offset = offset;
      result.linesReturned = content.split('\n').length;
    }
    ok(res, result);
  } catch (e) { fail(res, 500, e.message); }
});

// GET /run?cmd=...&key=&cwd=&timeout=
app.get('/run', auth, (req, res) => {
  const cmd = req.query.cmd;
  if (!cmd) return fail(res, 400, 'need ?cmd= parameter');
  const cwd = req.query.cwd || 'D:\\mrl';
  const timeout = Math.min(parseInt(req.query.timeout) || 15, 30) * 1000;
  log('RUN_GET', { cmd, cwd }, req);
  try {
    const output = execSync(cmd, {
      cwd,
      timeout,
      encoding: 'utf-8',
      shell: 'powershell.exe',
      maxBuffer: 5 * 1024 * 1024,
      windowsHide: true,
    });
    ok(res, { cmd, cwd, output: output.trim() });
  } catch (e) {
    stats.error++;
    res.json({ ok: false, cmd, cwd, exitCode: e.status, stderr: (e.stderr || '').trim(), stdout: (e.stdout || '').trim(), error: e.message, _v: VERSION, _t: new Date().toISOString() });
  }
});

// GET /redis-cmd?command=...&args=a,b&key=
app.get('/redis-cmd', auth, async (req, res) => {
  const command = req.query.command;
  if (!command) return fail(res, 400, 'need ?command= parameter');
  if (!redisSafe(command)) {
    log('REDIS_BLOCKED', command, req);
    stats.blocked++;
    return fail(res, 403, 'forbidden Redis command');
  }
  log('REDIS_GET', command, req);
  try {
    const args = req.query.args ? req.query.args.split(',') : [];
    const result = await redis.call(command, ...args);
    ok(res, { command, args, result });
  } catch (e) { fail(res, 500, e.message); }
});

// GET /sysinfo?key=
app.get('/sysinfo', auth, (req, res) => {
  log('SYSINFO', 'query', req);
  try {
    const info = {
      hostname: os.hostname(),
      platform: os.platform(),
      arch: os.arch(),
      cpus: os.cpus().length,
      node: process.version,
      bridge: VERSION,
      origin_signature: ORIGIN,
      uptime_host: Math.round(os.uptime()),
      uptime_bridge: Math.round(process.uptime()),
      boot_time: BOOT_TIME.toISOString(),
      memory: {
        total_gb: (os.totalmem() / 1073741824).toFixed(2),
        free_gb: (os.freemem() / 1073741824).toFixed(2),
        used_percent: ((1 - os.freemem() / os.totalmem()) * 100).toFixed(1),
        bridge_mb: (process.memoryUsage().rss / 1048576).toFixed(1),
      },
      pg_pool: {
        total: pgPool.totalCount,
        idle: pgPool.idleCount,
        waiting: pgPool.waitingCount,
      },
      stats: { ...stats },
      timestamp: new Date().toISOString(),
    };

    // 磁碟（PowerShell 取）
    try {
      const diskC = execSync('powershell -NoProfile -Command "(Get-PSDrive C).Free"', { encoding: 'utf-8', timeout: 5000, windowsHide: true }).trim();
      const diskD = execSync('powershell -NoProfile -Command "(Get-PSDrive D).Free"', { encoding: 'utf-8', timeout: 5000, windowsHide: true }).trim();
      info.disk = {
        c_free_gb: (parseInt(diskC) / 1073741824).toFixed(2),
        d_free_gb: (parseInt(diskD) / 1073741824).toFixed(2),
      };
    } catch (_) { info.disk = { error: 'unable to query' }; }

    ok(res, info);
  } catch (e) { fail(res, 500, e.message); }
});

// GET /write?path=...&content=...&key= (短文本)
// GET /write?path=...&b64=BASE64...&key= (base64 編碼，支援大檔案或二進位)
app.get('/write', auth, (req, res) => {
  const filepath = req.query.path;
  if (!filepath) return fail(res, 400, 'need ?path= parameter');
  const sp = safePath(filepath);
  if (!sp) return fail(res, 400, 'invalid path');

  let content;
  if (req.query.b64) {
    try {
      content = Buffer.from(req.query.b64, 'base64').toString('utf-8');
    } catch (e) { return fail(res, 400, 'invalid base64: ' + e.message); }
  } else if (req.query.content !== undefined) {
    content = req.query.content;
  } else {
    return fail(res, 400, 'need ?content= or ?b64= parameter');
  }

  log('WRITE_GET', { filepath, size: content.length }, req);
  try {
    const dir = path.dirname(sp);
    if (!fs.existsSync(dir)) fs.mkdirSync(dir, { recursive: true });
    fs.writeFileSync(sp, content, 'utf-8');
    const st = fs.statSync(sp);
    ok(res, { filepath, size: st.size, modified: st.mtime.toISOString() });
  } catch (e) { fail(res, 500, e.message); }
});

// GET /audit?date=2026-04-05&key=&tail=50
app.get('/audit', auth, (req, res) => {
  const date = req.query.date || new Date().toISOString().slice(0, 10);
  const tail = parseInt(req.query.tail) || 0;
  const logFile = path.join(LOG_DIR, `bridge_${date}.jsonl`);
  log('AUDIT_VIEW', { date, tail }, req);
  try {
    if (!fs.existsSync(logFile)) return ok(res, { date, count: 0, entries: [], message: 'no log for this date' });
    const raw = fs.readFileSync(logFile, 'utf-8').trim();
    if (!raw) return ok(res, { date, count: 0, entries: [] });
    let lines = raw.split('\n');
    const totalCount = lines.length;
    if (tail > 0) lines = lines.slice(-tail);
    const entries = lines.map(l => { try { return JSON.parse(l); } catch (_) { return { raw: l }; } });
    ok(res, { date, totalCount, returned: entries.length, entries });
  } catch (e) { fail(res, 500, e.message); }
});

// ═════════════════════════════════════════════
// POST ENDPOINTS（完整操作介面）
// ═════════════════════════════════════════════

// POST /file/write { filepath, content, encoding, mkdir }
app.post('/file/write', auth, (req, res) => {
  try {
    const { filepath, content, encoding, b64 } = req.body;
    if (!filepath) return fail(res, 400, 'need filepath');
    const sp = safePath(filepath);
    if (!sp) return fail(res, 400, 'invalid path');

    let data;
    if (b64) {
      data = Buffer.from(b64, 'base64');
    } else if (content !== undefined) {
      data = content;
    } else {
      return fail(res, 400, 'need content or b64');
    }

    log('FILE_WRITE', { filepath, size: typeof data === 'string' ? data.length : data.length }, req);
    const dir = path.dirname(sp);
    if (!fs.existsSync(dir)) fs.mkdirSync(dir, { recursive: true });
    fs.writeFileSync(sp, data, typeof data === 'string' ? (encoding || 'utf-8') : undefined);
    const st = fs.statSync(sp);
    ok(res, { filepath, size: st.size, modified: st.mtime.toISOString() });
  } catch (e) { fail(res, 500, e.message); }
});

// POST /file/read { filepath, encoding, lines, offset }
app.post('/file/read', auth, (req, res) => {
  try {
    const { filepath, encoding, lines, offset } = req.body;
    if (!filepath) return fail(res, 400, 'need filepath');
    if (!fs.existsSync(filepath)) return fail(res, 404, 'file not found');
    const st = fs.statSync(filepath);
    if (st.size > MAX_FILE_READ) return fail(res, 413, 'file too large: ' + st.size + ' bytes');
    log('FILE_READ', filepath, req);

    let content = fs.readFileSync(filepath, encoding || 'utf-8');
    const result = { filepath, size: st.size, modified: st.mtime.toISOString() };

    if (lines > 0) {
      const all = content.split('\n');
      result.totalLines = all.length;
      const off = offset || 0;
      content = all.slice(off, off + lines).join('\n');
      result.offset = off;
      result.linesReturned = content.split('\n').length;
    }
    result.content = content;
    ok(res, result);
  } catch (e) { fail(res, 500, e.message); }
});

// POST /file/list { dirpath, recursive, pattern }
app.post('/file/list', auth, (req, res) => {
  try {
    const { dirpath, recursive, pattern } = req.body;
    if (!dirpath) return fail(res, 400, 'need dirpath');
    if (!fs.existsSync(dirpath)) return fail(res, 404, 'directory not found');
    log('FILE_LIST', dirpath, req);

    function listDir(dir, depth) {
      const entries = fs.readdirSync(dir, { withFileTypes: true });
      const items = [];
      for (const e of entries) {
        const full = path.join(dir, e.name);
        if (pattern && !e.name.includes(pattern)) continue;
        const info = { name: e.name, type: e.isDirectory() ? 'dir' : 'file', path: full };
        if (e.isFile()) {
          try { info.size = fs.statSync(full).size; } catch (_) {}
        }
        items.push(info);
        if (recursive && e.isDirectory() && depth < 3) {
          try { info.children = listDir(full, depth + 1); } catch (_) {}
        }
      }
      return items;
    }

    const items = listDir(dirpath, 0);
    ok(res, { dirpath, count: items.length, items });
  } catch (e) { fail(res, 500, e.message); }
});

// POST /exec { cmd, cwd, timeout, shell }
app.post('/exec', auth, (req, res) => {
  try {
    const { cmd, cwd, timeout, shell } = req.body;
    if (!cmd) return fail(res, 400, 'need cmd');
    const t = Math.min((timeout || 15) * 1000, MAX_EXEC_TIMEOUT);
    const s = shell || 'powershell.exe';
    log('EXEC', { cmd, cwd: cwd || 'D:\\mrl', shell: s }, req);
    const output = execSync(cmd, {
      cwd: cwd || 'D:\\mrl',
      timeout: t,
      encoding: 'utf-8',
      shell: s,
      maxBuffer: 5 * 1024 * 1024,
      windowsHide: true,
    });
    ok(res, { cmd, output: output.trim() });
  } catch (e) {
    stats.error++;
    res.json({ ok: false, cmd: req.body.cmd, exitCode: e.status, stderr: (e.stderr || '').trim(), stdout: (e.stdout || '').trim(), error: e.message, _v: VERSION, _t: new Date().toISOString() });
  }
});

// POST /pg/query { sql, params }
app.post('/pg/query', auth, async (req, res) => {
  try {
    const { sql, params } = req.body;
    if (!sql) return fail(res, 400, 'need sql');
    if (!sqlSafe(sql)) {
      log('SQL_BLOCKED', sql, req);
      stats.blocked++;
      return fail(res, 403, 'forbidden SQL operation');
    }
    log('PG_POST', sql, req);
    const r = await pgPool.query(sql, params || []);
    ok(res, {
      rowCount: r.rowCount,
      rows: r.rows,
      fields: r.fields ? r.fields.map(f => ({ name: f.name, dataTypeID: f.dataTypeID })) : [],
    });
  } catch (e) { fail(res, 500, e.message); }
});

// POST /redis { command, args }
app.post('/redis', auth, async (req, res) => {
  try {
    const { command, args } = req.body;
    if (!command) return fail(res, 400, 'need command');
    if (!redisSafe(command)) {
      log('REDIS_BLOCKED', command, req);
      stats.blocked++;
      return fail(res, 403, 'forbidden Redis command');
    }
    log('REDIS_POST', { command, args }, req);
    const result = await redis.call(command, ...(args || []));
    ok(res, { command, args, result });
  } catch (e) { fail(res, 500, e.message); }
});

// ═════════════════════════════════════════════
// 404 + 全局錯誤處理
// ═════════════════════════════════════════════

app.use((req, res) => {
  res.status(404).json({
    ok: false,
    error: 'endpoint not found: ' + req.method + ' ' + req.path,
    available: '/health /version /pg /tables /ls /cat /run /redis-cmd /sysinfo /write /audit',
    _v: VERSION,
  });
});

app.use((err, req, res, _next) => {
  log('UNHANDLED_ERROR', err.message, req);
  stats.error++;
  res.status(500).json({ ok: false, error: 'internal server error', _v: VERSION });
});

// ═════════════════════════════════════════════
// 啟動 + 自檢 + 優雅關機
// ═════════════════════════════════════════════

let httpServer;

async function boot() {
  console.log('');
  console.log('╔══════════════════════════════════════════════════════════╗');
  console.log('║  MRL_Bridge_API v' + VERSION + '                                ║');
  console.log('║  origin_signature: MrLiouWord                          ║');
  console.log('╚══════════════════════════════════════════════════════════╝');
  console.log('');

  // 1. Redis 連線
  try {
    await redis.connect();
    const pong = await redis.ping();
    console.log('[BOOT] Redis ........... ' + (pong === 'PONG' ? 'OK' : 'FAIL'));
  } catch (e) {
    console.warn('[BOOT] Redis ........... FAIL: ' + e.message);
  }

  // 2. PG 連線 + 表數確認
  try {
    const r = await pgPool.query('SELECT count(*)::int AS n FROM information_schema.tables WHERE table_schema=$1', ['public']);
    console.log('[BOOT] PostgreSQL ...... OK (' + r.rows[0].n + ' tables)');
  } catch (e) {
    console.warn('[BOOT] PostgreSQL ...... FAIL: ' + e.message);
  }

  // 3. 日誌目錄
  console.log('[BOOT] Log dir ......... ' + LOG_DIR);

  // 4. HTTP 啟動
  httpServer = app.listen(PORT, '0.0.0.0', () => {
    console.log('[BOOT] HTTP ............ port ' + PORT);
    console.log('');
    console.log('[ENDPOINTS]');
    console.log('  PUBLIC:  GET /health  GET /version');
    console.log('  GET:     /pg /tables /ls /cat /run /redis-cmd /sysinfo /write /audit');
    console.log('  POST:    /file/write /file/read /file/list /exec /pg/query /redis');
    console.log('  AUTH:    x-api-key header or ?key= query');
    console.log('');
    console.log('[READY] Bridge is listening on 0.0.0.0:' + PORT);
    console.log('');
    log('BOOT', { version: VERSION, port: PORT, timestamp: new Date().toISOString() });
  });
}

function shutdown(signal) {
  console.log('');
  console.log('[SHUTDOWN] ' + signal + ' received');
  log('SHUTDOWN', { signal, uptime: Math.round(process.uptime()), stats });

  if (httpServer) {
    httpServer.close(() => {
      console.log('[SHUTDOWN] HTTP server closed');
      pgPool.end().then(() => {
        console.log('[SHUTDOWN] PG pool closed');
        redis.disconnect();
        console.log('[SHUTDOWN] Redis disconnected');
        console.log('[SHUTDOWN] Clean exit');
        process.exit(0);
      }).catch(() => process.exit(0));
    });

    // 強制 10 秒後退出
    setTimeout(() => {
      console.log('[SHUTDOWN] Force exit after 10s timeout');
      process.exit(1);
    }, 10000);
  } else {
    process.exit(0);
  }
}

process.on('SIGINT', () => shutdown('SIGINT'));
process.on('SIGTERM', () => shutdown('SIGTERM'));

process.on('uncaughtException', (err) => {
  console.error('[FATAL] Uncaught exception:', err.message);
  log('UNCAUGHT_EXCEPTION', { message: err.message, stack: err.stack });
  // 不退出，繼續運行
});

process.on('unhandledRejection', (reason) => {
  console.error('[FATAL] Unhandled rejection:', reason);
  log('UNHANDLED_REJECTION', { reason: String(reason) });
  // 不退出，繼續運行
});

// 啟動
boot();
