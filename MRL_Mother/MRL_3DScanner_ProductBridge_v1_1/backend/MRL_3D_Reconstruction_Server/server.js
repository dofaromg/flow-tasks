import fs from 'node:fs/promises';
import { createWriteStream } from 'node:fs';
import http from 'node:http';
import path from 'node:path';
import crypto from 'node:crypto';
import { once } from 'node:events';
import { fileURLToPath } from 'node:url';
import { spawn } from 'node:child_process';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const ROOT = __dirname;
const PORT = Number(process.env.MRL_3D_BRIDGE_PORT || 3050);
if (PORT !== 3050) throw new Error('MRL bridge requires port 3050');
// ROOT: the MRL world is entered and left only through DL580's Tailscale address.
// Loopback stays for on-host health checks; never listen on all interfaces.
const BIND = (process.env.MRL_BRIDGE_BIND || '100.78.70.78,127.0.0.1').split(',').map(h => h.trim()).filter(Boolean);
if (!BIND.length || BIND.some(h => ['0.0.0.0', '::', '[::]', '*'].includes(h))) throw new Error('MRL bridge must bind explicit addresses, never all interfaces');
const STORAGE = path.join(ROOT, 'storage');
const UPLOADS = path.join(STORAGE, 'uploads');
const JOBS = path.join(STORAGE, 'jobs');
const OUTPUTS = path.join(STORAGE, 'outputs');
const REPORTS = path.join(STORAGE, 'reports');
const LOGS = path.join(STORAGE, 'logs');
const TMP = path.join(STORAGE, 'tmp');
const JSON_LIMIT = 20 * 1024 * 1024;
const MAX_UPLOAD_FILES = 500;

async function ensureDir(p) { await fs.mkdir(p, { recursive: true }); }
async function pathExists(p) { try { await fs.access(p); return true; } catch { return false; } }
async function removePath(p) { await fs.rm(p, { recursive: true, force: true }); }
async function moveFile(src, dest) {
  await ensureDir(path.dirname(dest));
  try {
    await fs.rename(src, dest);
  } catch (err) {
    if (err.code === 'EXDEV') {
      await fs.copyFile(src, dest);
      await fs.rm(src, { force: true });
      return;
    }
    if (err.code === 'EEXIST' || err.code === 'EPERM') {
      await fs.rm(dest, { force: true });
      await fs.rename(src, dest);
      return;
    }
    throw err;
  }
}
function newId() { return crypto.randomUUID(); }
function header(req, name) {
  const value = req.headers[name.toLowerCase()];
  return Array.isArray(value) ? value[0] : value;
}
function sendJson(res, status, body) {
  if (res.headersSent) return;
  const payload = JSON.stringify(body);
  res.statusCode = status;
  res.setHeader('Content-Type', 'application/json; charset=utf-8');
  res.setHeader('Content-Length', Buffer.byteLength(payload));
  res.end(payload);
}
function clientError(status, error) {
  const err = new Error(error);
  err.statusCode = status;
  err.body = { ok: false, error };
  return err;
}
function setCors(res) {
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type, X-MRL-Scan-ID, X-MRL-Scan-Name');
  res.setHeader('Access-Control-Allow-Methods', 'GET,POST,OPTIONS');
}

await ensureDir(UPLOADS);
await ensureDir(JOBS);
await ensureDir(OUTPUTS);
await ensureDir(REPORTS);
await ensureDir(LOGS);
await ensureDir(TMP);

let backendReady = false;

function now() { return new Date().toISOString(); }
function jobPath(id) { return path.join(JOBS, `${id}.json`); }
function scanDir(scanId) { return path.join(UPLOADS, scanId); }
async function readJson(p, fallback) { try { return JSON.parse(await fs.readFile(p, 'utf8')); } catch { return fallback; } }
async function writeJson(p, data) { await ensureDir(path.dirname(p)); await fs.writeFile(p, JSON.stringify(data, null, 2), 'utf8'); }
const scanListRequests = new Map();
const scanListWindowMs = 60_000;
const scanListMaxRequests = 60;

function limitScanList(req, res) {
  const address = req.socket.remoteAddress || 'unknown';
  const timestamp = Date.now();
  let bucket = scanListRequests.get(address);
  if (!bucket || timestamp - bucket.startedAt >= scanListWindowMs) {
    if (scanListRequests.size >= 1024) {
      for (const [key, value] of scanListRequests) {
        if (timestamp - value.startedAt >= scanListWindowMs) scanListRequests.delete(key);
      }
      if (scanListRequests.size >= 1024) {
        sendJson(res, 429, { ok: false, error: 'too many clients' });
        return false;
      }
    }
    bucket = { startedAt: timestamp, count: 0 };
    scanListRequests.set(address, bucket);
  }
  if (bucket.count >= scanListMaxRequests) {
    res.setHeader('Retry-After', String(Math.ceil((bucket.startedAt + scanListWindowMs - timestamp) / 1000)));
    sendJson(res, 429, { ok: false, error: 'scan list rate limit exceeded' });
    return false;
  }
  bucket.count++;
  return true;
}

async function appendLog(line) {
  await fs.appendFile(path.join(LOGS, 'runtime.log'), `[${now()}] ${line}\n`, 'utf8');
}

async function writeStream(stream, chunk) {
  if (!stream.write(chunk)) await once(stream, 'drain');
}

async function closeStream(stream) {
  await new Promise((resolve, reject) => {
    stream.end(err => err ? reject(err) : resolve());
  });
}

function multipartBoundary(contentType) {
  const match = String(contentType || '').match(/boundary\s*=\s*(?:"([^"]+)"|([^;]+))/i);
  if (!match) return null;
  return (match[1] || match[2] || '').trim();
}

function parseDisposition(value) {
  const name = /(?:^|;)\s*name=(?:"([^"]*)"|([^;]*))/i.exec(value || '');
  const encoded = /(?:^|;)\s*filename\*=(?:UTF-8''|utf-8'')([^;]+)/i.exec(value || '');
  const filename = /(?:^|;)\s*filename=(?:"([^"]*)"|([^;]*))/i.exec(value || '');
  let originalname = '';
  if (encoded) {
    try { originalname = decodeURIComponent(encoded[1].trim().replace(/^"|"$/g, '')); } catch { originalname = encoded[1].trim(); }
  } else if (filename) {
    originalname = (filename[1] ?? filename[2] ?? '').trim();
  }
  return { name: name ? (name[1] ?? name[2] ?? '').trim() : '', originalname };
}

async function parseMultipartFiles(req) {
  const boundary = multipartBoundary(header(req, 'content-type'));
  if (!boundary) throw clientError(400, 'files required');
  const dashBoundary = Buffer.from(`--${boundary}`);
  const delimiter = Buffer.from(`\r\n--${boundary}`);
  const headerSep = Buffer.from('\r\n\r\n');
  const files = [];
  let buf = Buffer.alloc(0);
  let state = 'start';
  let current = null;

  async function fail(err) {
    if (current?.stream) {
      current.stream.destroy();
      await removePath(current.path);
      current = null;
    }
    await Promise.all(files.map(file => removePath(file.path)));
    throw err;
  }

  async function finishPart() {
    if (!current) return;
    if (current.stream) {
      await closeStream(current.stream);
      files.push({ path: current.path, originalname: current.originalname, filename: current.filename });
    }
    current = null;
  }

  async function consume(chunk) {
    buf = Buffer.concat([buf, chunk]);
    while (buf.length) {
      if (state === 'done') { buf = Buffer.alloc(0); return; }
      if (state === 'start') {
        const idx = buf.indexOf(dashBoundary);
        if (idx === -1) {
          if (buf.length > dashBoundary.length + 8) await fail(clientError(400, 'files required'));
          return;
        }
        buf = buf.subarray(idx + dashBoundary.length);
        state = 'after-boundary';
        continue;
      }
      if (state === 'after-boundary') {
        if (buf.length < 2) return;
        if (buf[0] === 0x2d && buf[1] === 0x2d) { state = 'done'; buf = Buffer.alloc(0); return; }
        if (buf[0] === 0x0d && buf[1] === 0x0a) {
          buf = buf.subarray(2);
          state = 'headers';
          continue;
        }
        await fail(clientError(400, 'files required'));
      }
      if (state === 'headers') {
        const sep = buf.indexOf(headerSep);
        if (sep === -1) {
          if (buf.length > 16 * 1024) await fail(clientError(400, 'files required'));
          return;
        }
        const headerText = buf.subarray(0, sep).toString('utf8');
        buf = buf.subarray(sep + 4);
        const headers = {};
        for (const line of headerText.split('\r\n')) {
          const colon = line.indexOf(':');
          if (colon > 0) headers[line.slice(0, colon).trim().toLowerCase()] = line.slice(colon + 1).trim();
        }
        const disp = parseDisposition(headers['content-disposition']);
        if (disp.name === 'files' && disp.originalname) {
          if (files.length >= MAX_UPLOAD_FILES) await fail(clientError(400, 'files required'));
          const filename = newId();
          const filePath = path.join(TMP, filename);
          current = {
            path: filePath,
            filename,
            originalname: path.basename(disp.originalname),
            stream: createWriteStream(filePath)
          };
        } else {
          current = { skip: true };
        }
        state = 'body';
        continue;
      }
      if (state === 'body') {
        const idx = buf.indexOf(delimiter);
        if (idx === -1) {
          const keep = delimiter.length - 1;
          if (buf.length > keep) {
            const write = buf.subarray(0, buf.length - keep);
            buf = buf.subarray(buf.length - keep);
            if (current?.stream) await writeStream(current.stream, write);
          }
          return;
        }
        const write = buf.subarray(0, idx);
        buf = buf.subarray(idx + 2);
        if (current?.stream) await writeStream(current.stream, write);
        await finishPart();
        state = 'start';
      }
    }
  }

  try {
    for await (const chunk of req) {
      if (state === 'done') break;
      await consume(chunk);
    }
    if (current) await fail(clientError(400, 'files required'));
    return files;
  } catch (err) {
    if (err.body) throw err;
    await fail(err);
  }
}

async function readJsonBody(req) {
  const chunks = [];
  let size = 0;
  for await (const chunk of req) {
    size += chunk.length;
    if (size > JSON_LIMIT) throw clientError(413, 'payload too large');
    chunks.push(chunk);
  }
  if (!size) return {};
  try {
    return JSON.parse(Buffer.concat(chunks).toString('utf8'));
  } catch {
    throw clientError(400, 'invalid json');
  }
}

async function handleHealth(_req, res) {
  sendJson(res, 200, { ok: true, service: 'MRL_3D_Reconstruction_Server', version: '1.0.0', port: PORT, pid: process.pid, instance: process.env.MRL_BRIDGE_INSTANCE || null, time: now() });
}

async function handleScanList(req, res) {
  if (!limitScanList(req, res)) return;
  const items = [];
  if (await pathExists(UPLOADS)) {
    for (const name of await fs.readdir(UPLOADS)) {
      const manifest = path.join(UPLOADS, name, 'manifest.json');
      if (await pathExists(manifest)) {
        const item = await readJson(manifest, {});
        items.push({ ...item, files: (item.files || []).map(({ path: _path, ...file }) => file) });
      }
    }
  }
  sendJson(res, 200, { ok: true, scans: items });
}

async function handleUpload(req, res) {
  const files = await parseMultipartFiles(req);
  const scanId = header(req, 'x-mrl-scan-id') || newId();
  if (!/^[a-zA-Z0-9_-]{1,128}$/.test(scanId)) {
    await Promise.all(files.map(f => removePath(f.path)));
    sendJson(res, 400, { ok: false, error: 'invalid scanId' });
    return;
  }
  if (!files.length) {
    sendJson(res, 400, { ok: false, error: 'files required' });
    return;
  }
  if (await pathExists(scanDir(scanId))) {
    await Promise.all(files.map(f => removePath(f.path)));
    sendJson(res, 409, { ok: false, error: 'scanId already exists; use a new ID' });
    return;
  }
  const scanName = header(req, 'x-mrl-scan-name') || `scan_${scanId}`;
  const dir = scanDir(scanId);
  try { await fs.mkdir(dir); } catch (err) {
    await Promise.all(files.map(f => removePath(f.path)));
    if (err.code === 'EEXIST') {
      sendJson(res, 409, { ok: false, error: 'scanId already exists' });
      return;
    }
    throw err;
  }
  const stored = [];
  for (const file of files) {
    const safe = path.basename(file.originalname || file.filename).replace(/[^a-zA-Z0-9._-]/g, '_');
    const target = path.join(dir, safe || file.filename);
    await moveFile(file.path, target);
    const stat = await fs.stat(target);
    stored.push({ originalName: file.originalname, filename: path.basename(target), size: stat.size });
  }
  const manifest = { scanId, scanName, uploaded: stored.length, files: stored, createdAt: now(), status: 'uploaded' };
  await writeJson(path.join(dir, 'manifest.json'), manifest);
  await appendLog(`upload scan=${scanId} files=${stored.length}`);
  sendJson(res, 200, { ok: true, scanId, uploaded: stored.length });
}

async function handleCreateJob(req, res) {
  const body = await readJsonBody(req);
  const { scanId, mode = 'auto' } = body || {};
  if (typeof scanId !== 'string' || !/^[a-zA-Z0-9_-]{1,128}$/.test(scanId)) {
    sendJson(res, 400, { ok: false, error: 'scanId required' });
    return;
  }
  const manifest = path.join(scanDir(scanId), 'manifest.json');
  if (!(await pathExists(manifest))) {
    sendJson(res, 404, { ok: false, error: 'scan manifest not found' });
    return;
  }
  const jobId = newId();
  const job = { jobId, scanId, mode, status: 'queued', createdAt: now(), updatedAt: now(), message: null, outputFiles: [] };
  await writeJson(jobPath(jobId), job);
  await appendLog(`job queued job=${jobId} scan=${scanId}`);
  runJob(jobId).catch(async err => {
    const j = await readJson(jobPath(jobId), job);
    j.status = 'failed'; j.message = String(err?.message || err); j.updatedAt = now();
    await writeJson(jobPath(jobId), j);
  });
  sendJson(res, 200, { ok: true, jobId, status: job.status });
}

async function handleGetJob(req, res, id) {
  if (!/^[a-zA-Z0-9_-]{1,128}$/.test(id)) {
    sendJson(res, 400, { ok: false, error: 'invalid jobId' });
    return;
  }
  const job = await readJson(jobPath(id), null);
  if (!job) {
    sendJson(res, 404, { ok: false, error: 'job not found' });
    return;
  }
  sendJson(res, 200, job);
}

async function handleJobFiles(req, res, id) {
  if (!/^[a-zA-Z0-9_-]{1,128}$/.test(id)) {
    sendJson(res, 400, { ok: false, error: 'invalid jobId' });
    return;
  }
  const out = path.join(OUTPUTS, id);
  if (!(await pathExists(out))) {
    sendJson(res, 200, { ok: true, files: [] });
    return;
  }
  sendJson(res, 200, { ok: true, files: await listFiles(out) });
}

async function runJob(jobId) {
  let job = await readJson(jobPath(jobId), null);
  job.status = 'running'; job.updatedAt = now();
  await writeJson(jobPath(jobId), job);
  const out = path.join(OUTPUTS, jobId);
  await ensureDir(out);
  const runner = path.join(ROOT, 'python', 'mrl3d_job_runner.py');
  const args = [runner, '--scan-dir', scanDir(job.scanId), '--output-dir', out, '--mode', job.mode];
  const py = process.env.MRL_BRIDGE_PYTHON || (process.platform === 'win32' ? 'python' : 'python3');
  await appendLog(`runner start job=${jobId}`);
  const child = spawn(py, args, { cwd: ROOT });
  let stdout = ''; let stderr = '';
  child.stdout.on('data', d => stdout += d.toString());
  child.stderr.on('data', d => stderr += d.toString());
  const code = await new Promise((resolve, reject) => {
    child.once('error', reject);
    child.once('close', resolve);
  });
  await fs.writeFile(path.join(out, 'runner_stdout.log'), stdout, 'utf8');
  await fs.writeFile(path.join(out, 'runner_stderr.log'), stderr, 'utf8');

  const runnerReportPath = path.join(out, 'MRL_JOB_REPORT.json');
  const runnerMdPath = path.join(out, 'RUN_REPORT.md');
  const report = await readJson(runnerReportPath, null);
  if (report) {
    await writeJson(path.join(REPORTS, `${jobId}_MRL_JOB_REPORT.json`), report);
    if (await pathExists(runnerMdPath)) {
      await fs.copyFile(runnerMdPath, path.join(REPORTS, `${jobId}_RUN_REPORT.md`));
    }
  }

  job = await readJson(jobPath(jobId), job);
  job.updatedAt = now();
  if (code === 0 && report?.status === 'completed') {
    job.status = 'completed';
    job.message = report?.reason || 'runner completed';
  } else {
    job.status = 'failed';
    job.message = report?.reason || (!report ? 'RUNNER_REPORT_MISSING' : stderr || stdout || `runner exit ${code}`);
  }
  job.exitCode = code;
  job.report = report || null;
  job.outputFiles = await listFiles(out);
  job.reportFiles = await listFiles(REPORTS);
  await writeJson(jobPath(jobId), job);
  await appendLog(`runner finish job=${jobId} status=${job.status} reason=${job.message}`);
}

async function listFiles(dir) {
  const files = [];
  if (!(await pathExists(dir))) return files;
  async function walk(d) {
    for (const n of await fs.readdir(d)) {
      const p = path.join(d, n); const st = await fs.stat(p);
      if (st.isDirectory()) await walk(p); else files.push(path.relative(dir, p).replaceAll('\\','/'));
    }
  }
  await walk(dir);
  return files;
}

async function handleRequest(req, res) {
  setCors(res);
  if (req.method === 'OPTIONS') {
    res.statusCode = 204;
    res.end();
    return;
  }
  if (!backendReady) {
    sendJson(res, 503, { ok: false, error: 'backend initializing' });
    return;
  }
  const url = new URL(req.url, 'http://127.0.0.1');
  const pathname = url.pathname;
  try {
    if (req.method === 'GET' && pathname === '/api/health') return await handleHealth(req, res);
    if (req.method === 'GET' && pathname === '/api/scans') return await handleScanList(req, res);
    if (req.method === 'POST' && pathname === '/api/scans/upload') return await handleUpload(req, res);
    if (req.method === 'POST' && pathname === '/api/reconstruction/jobs') return await handleCreateJob(req, res);
    const jobFiles = /^\/api\/reconstruction\/jobs\/([^/]+)\/files$/.exec(pathname);
    if (req.method === 'GET' && jobFiles) return await handleJobFiles(req, res, decodeURIComponent(jobFiles[1]));
    const job = /^\/api\/reconstruction\/jobs\/([^/]+)$/.exec(pathname);
    if (req.method === 'GET' && job) return await handleGetJob(req, res, decodeURIComponent(job[1]));
    sendJson(res, 404, { ok: false, error: 'not found' });
  } catch (err) {
    await appendLog(`request failed: ${err.message}`).catch(console.error);
    if (res.headersSent) return;
    if (err.body && err.statusCode) {
      sendJson(res, err.statusCode, err.body);
      return;
    }
    sendJson(res, 500, { ok: false, error: 'request failed' });
  }
}

async function markInterruptedJobs() {
  for (const name of await fs.readdir(JOBS)) {
    if (!name.endsWith('.json')) continue;
    const p = path.join(JOBS, name);
    const job = await readJson(p, null);
    if (job && ['queued', 'running'].includes(job.status)) {
      job.status = 'failed'; job.message = 'INTERRUPTED_BY_BACKEND_RESTART'; job.updatedAt = now();
      await writeJson(p, job);
    }
  }
}

// Acquire every configured listener before changing jobs from an earlier backend.
const servers = BIND.map(() => http.createServer(handleRequest));
const listenResults = await Promise.allSettled(servers.map((server, index) => new Promise((resolve, reject) => {
  const host = BIND[index];
  const onError = err => reject(new Error(`listen ${host}:${PORT} failed: ${err.code || err.message}`));
  server.once('error', onError);
  server.listen(PORT, host, () => {
    server.off('error', onError);
    console.log(`MRL 3D Reconstruction Server running on ${host}:${PORT}`);
    resolve();
  });
})));
const listenFailure = listenResults.find(result => result.status === 'rejected');
if (listenFailure) {
  await Promise.all(servers.filter(server => server.listening).map(server => new Promise(resolve => server.close(resolve))));
  console.error(listenFailure.reason.message);
  process.exit(1);
}
for (const server of servers) {
  server.on('error', err => {
    console.error(`bridge listener failed: ${err.code || err.message}`);
    process.exit(1);
  });
}
try {
  await markInterruptedJobs();
  backendReady = true;
} catch (err) {
  await Promise.all(servers.map(server => new Promise(resolve => {
    if (server.listening) server.close(resolve);
    else resolve();
  })));
  throw err;
}
