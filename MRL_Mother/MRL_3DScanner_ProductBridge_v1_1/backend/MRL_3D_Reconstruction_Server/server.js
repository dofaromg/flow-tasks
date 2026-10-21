import express from 'express';
import cors from 'cors';
import multer from 'multer';
import fs from 'fs-extra';
import http from 'http';
import path from 'path';
import { fileURLToPath } from 'url';
import { v4 as uuidv4 } from 'uuid';
import { spawn } from 'child_process';

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

await fs.ensureDir(UPLOADS);
await fs.ensureDir(JOBS);
await fs.ensureDir(OUTPUTS);
await fs.ensureDir(REPORTS);
await fs.ensureDir(LOGS);
await fs.ensureDir(TMP);

const app = express();
app.use(cors());
app.use(express.json({ limit: '20mb' }));
let backendReady = false;
app.use((req, res, next) => {
  if (!backendReady) return res.status(503).json({ ok: false, error: 'backend initializing' });
  next();
});

function asyncRoute(handler) {
  return (req, res, next) => Promise.resolve(handler(req, res, next)).catch(next);
}
const upload = multer({ dest: path.join(STORAGE, 'tmp') });

function now() { return new Date().toISOString(); }
function jobPath(id) { return path.join(JOBS, `${id}.json`); }
function scanDir(scanId) { return path.join(UPLOADS, scanId); }
async function readJson(p, fallback) { try { return await fs.readJson(p); } catch { return fallback; } }
async function writeJson(p, data) { await fs.ensureDir(path.dirname(p)); await fs.writeJson(p, data, { spaces: 2 }); }
const scanListRequests = new Map();
const scanListWindowMs = 60_000;
const scanListMaxRequests = 60;

function limitScanList(req, res, next) {
  const address = req.socket.remoteAddress || 'unknown';
  const timestamp = Date.now();
  let bucket = scanListRequests.get(address);
  if (!bucket || timestamp - bucket.startedAt >= scanListWindowMs) {
    if (scanListRequests.size >= 1024) {
      for (const [key, value] of scanListRequests) {
        if (timestamp - value.startedAt >= scanListWindowMs) scanListRequests.delete(key);
      }
      if (scanListRequests.size >= 1024) {
        return res.status(429).json({ ok: false, error: 'too many clients' });
      }
    }
    bucket = { startedAt: timestamp, count: 0 };
    scanListRequests.set(address, bucket);
  }
  if (bucket.count >= scanListMaxRequests) {
    res.set('Retry-After', String(Math.ceil((bucket.startedAt + scanListWindowMs - timestamp) / 1000)));
    return res.status(429).json({ ok: false, error: 'scan list rate limit exceeded' });
  }
  bucket.count++;
  next();
}

async function appendLog(line) {
  await fs.appendFile(path.join(LOGS, 'runtime.log'), `[${now()}] ${line}\n`, 'utf8');
}

app.get('/api/health', asyncRoute(async (req, res) => {
  res.json({ ok: true, service: 'MRL_3D_Reconstruction_Server', version: '1.0.0', port: PORT, pid: process.pid, instance: process.env.MRL_BRIDGE_INSTANCE || null, time: now() });
}));

app.get('/api/scans', limitScanList, asyncRoute(async (req, res) => {
  const items = [];
  if (await fs.pathExists(UPLOADS)) {
    for (const name of await fs.readdir(UPLOADS)) {
      const manifest = path.join(UPLOADS, name, 'manifest.json');
      if (await fs.pathExists(manifest)) {
        const item = await fs.readJson(manifest);
        items.push({ ...item, files: (item.files || []).map(({ path: _path, ...file }) => file) });
      }
    }
  }
  res.json({ ok: true, scans: items });
}));

app.post('/api/scans/upload', upload.array('files', 500), asyncRoute(async (req, res) => {
  const scanId = req.header('X-MRL-Scan-ID') || uuidv4();
  if (!/^[a-zA-Z0-9_-]{1,128}$/.test(scanId)) {
    await Promise.all((req.files || []).map(f => fs.remove(f.path)));
    return res.status(400).json({ ok: false, error: 'invalid scanId' });
  }
  if (!req.files?.length) return res.status(400).json({ ok: false, error: 'files required' });
  if (await fs.pathExists(scanDir(scanId))) {
    await Promise.all(req.files.map(f => fs.remove(f.path)));
    return res.status(409).json({ ok: false, error: 'scanId already exists; use a new ID' });
  }
  const scanName = req.header('X-MRL-Scan-Name') || `scan_${scanId}`;
  const dir = scanDir(scanId);
  try { await fs.mkdir(dir); } catch (err) {
    await Promise.all(req.files.map(f => fs.remove(f.path)));
    if (err.code === 'EEXIST') return res.status(409).json({ ok: false, error: 'scanId already exists' });
    throw err;
  }
  const files = [];
  for (const file of req.files || []) {
    const safe = path.basename(file.originalname || file.filename).replace(/[^a-zA-Z0-9._-]/g, '_');
    const target = path.join(dir, safe || file.filename);
    await fs.move(file.path, target, { overwrite: true });
    const stat = await fs.stat(target);
    files.push({ originalName: file.originalname, filename: path.basename(target), size: stat.size });
  }
  const manifest = { scanId, scanName, uploaded: files.length, files, createdAt: now(), status: 'uploaded' };
  await writeJson(path.join(dir, 'manifest.json'), manifest);
  await appendLog(`upload scan=${scanId} files=${files.length}`);
  res.json({ ok: true, scanId, uploaded: files.length });
}));

app.post('/api/reconstruction/jobs', asyncRoute(async (req, res) => {
  const { scanId, mode = 'auto' } = req.body || {};
  if (typeof scanId !== 'string' || !/^[a-zA-Z0-9_-]{1,128}$/.test(scanId)) return res.status(400).json({ ok: false, error: 'scanId required' });
  const manifest = path.join(scanDir(scanId), 'manifest.json');
  if (!(await fs.pathExists(manifest))) return res.status(404).json({ ok: false, error: 'scan manifest not found' });
  const jobId = uuidv4();
  const job = { jobId, scanId, mode, status: 'queued', createdAt: now(), updatedAt: now(), message: null, outputFiles: [] };
  await writeJson(jobPath(jobId), job);
  await appendLog(`job queued job=${jobId} scan=${scanId}`);
  runJob(jobId).catch(async err => {
    const j = await readJson(jobPath(jobId), job);
    j.status = 'failed'; j.message = String(err?.message || err); j.updatedAt = now();
    await writeJson(jobPath(jobId), j);
  });
  res.json({ ok: true, jobId, status: job.status });
}));

app.get('/api/reconstruction/jobs/:id', asyncRoute(async (req, res) => {
  if (!/^[a-zA-Z0-9_-]{1,128}$/.test(req.params.id)) return res.status(400).json({ ok: false, error: 'invalid jobId' });
  const job = await readJson(jobPath(req.params.id), null);
  if (!job) return res.status(404).json({ ok: false, error: 'job not found' });
  res.json(job);
}));

app.get('/api/reconstruction/jobs/:id/files', asyncRoute(async (req, res) => {
  if (!/^[a-zA-Z0-9_-]{1,128}$/.test(req.params.id)) return res.status(400).json({ ok: false, error: 'invalid jobId' });
  const out = path.join(OUTPUTS, req.params.id);
  if (!(await fs.pathExists(out))) return res.json({ ok: true, files: [] });
  const files = [];
  async function walk(d) {
    for (const n of await fs.readdir(d)) {
      const p = path.join(d, n); const st = await fs.stat(p);
      if (st.isDirectory()) await walk(p); else files.push(path.relative(out, p).replaceAll('\\','/'));
    }
  }
  await walk(out);
  res.json({ ok: true, files });
}));


async function runJob(jobId) {
  let job = await fs.readJson(jobPath(jobId));
  job.status = 'running'; job.updatedAt = now();
  await writeJson(jobPath(jobId), job);
  const out = path.join(OUTPUTS, jobId);
  await fs.ensureDir(out);
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
    if (await fs.pathExists(runnerMdPath)) {
      await fs.copy(runnerMdPath, path.join(REPORTS, `${jobId}_RUN_REPORT.md`), { overwrite: true });
    }
  }

  job = await fs.readJson(jobPath(jobId));
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
  if (!(await fs.pathExists(dir))) return files;
  async function walk(d) {
    for (const n of await fs.readdir(d)) {
      const p = path.join(d, n); const st = await fs.stat(p);
      if (st.isDirectory()) await walk(p); else files.push(path.relative(dir, p).replaceAll('\\','/'));
    }
  }
  await walk(dir);
  return files;
}

app.use((err, req, res, next) => {
  appendLog(`request failed: ${err.message}`).catch(console.error);
  if (res.headersSent) return next(err);
  res.status(500).json({ ok: false, error: 'request failed' });
});

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
const servers = BIND.map(() => http.createServer(app));
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
