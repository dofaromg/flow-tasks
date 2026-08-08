import express from 'express';
import cors from 'cors';
import multer from 'multer';
import fs from 'fs-extra';
import path from 'path';
import { fileURLToPath } from 'url';
import { v4 as uuidv4 } from 'uuid';
import { spawn } from 'child_process';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);
const ROOT = __dirname;
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

const upload = multer({ dest: path.join(STORAGE, 'tmp') });

function now() { return new Date().toISOString(); }
function jobPath(id) { return path.join(JOBS, `${id}.json`); }
function scanDir(scanId) { return path.join(UPLOADS, scanId); }
async function readJson(p, fallback) { try { return await fs.readJson(p); } catch { return fallback; } }
async function writeJson(p, data) { await fs.ensureDir(path.dirname(p)); await fs.writeJson(p, data, { spaces: 2 }); }

async function appendLog(line) {
  await fs.appendFile(path.join(LOGS, 'runtime.log'), `[${now()}] ${line}\n`, 'utf8');
}

app.get('/api/health', async (req, res) => {
  res.json({ ok: true, service: 'MRL_3D_Reconstruction_Server', version: '1.0.0', port: 3050, time: now() });
});

app.get('/api/scans', async (req, res) => {
  const items = [];
  if (await fs.pathExists(UPLOADS)) {
    for (const name of await fs.readdir(UPLOADS)) {
      const manifest = path.join(UPLOADS, name, 'manifest.json');
      if (await fs.pathExists(manifest)) items.push(await fs.readJson(manifest));
    }
  }
  res.json({ ok: true, scans: items });
});

app.post('/api/scans/upload', upload.array('files', 500), async (req, res) => {
  const scanId = req.header('X-MRL-Scan-ID') || uuidv4();
  const scanName = req.header('X-MRL-Scan-Name') || `scan_${scanId}`;
  const dir = scanDir(scanId);
  await fs.ensureDir(dir);
  const files = [];
  for (const file of req.files || []) {
    const safe = path.basename(file.originalname || file.filename).replace(/[^a-zA-Z0-9._-]/g, '_');
    const target = path.join(dir, safe || file.filename);
    await fs.move(file.path, target, { overwrite: true });
    const stat = await fs.stat(target);
    files.push({ originalName: file.originalname, filename: path.basename(target), size: stat.size, path: target });
  }
  const manifest = { scanId, scanName, uploaded: files.length, files, createdAt: now(), status: 'uploaded' };
  await writeJson(path.join(dir, 'manifest.json'), manifest);
  await appendLog(`upload scan=${scanId} files=${files.length}`);
  res.json({ ok: true, scanId, uploaded: files.length, manifestPath: path.join(dir, 'manifest.json') });
});

app.post('/api/reconstruction/jobs', async (req, res) => {
  const { scanId, mode = 'auto' } = req.body || {};
  if (!scanId) return res.status(400).json({ ok: false, error: 'scanId required' });
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
});

app.get('/api/reconstruction/jobs/:id', async (req, res) => {
  const job = await readJson(jobPath(req.params.id), null);
  if (!job) return res.status(404).json({ ok: false, error: 'job not found' });
  res.json(job);
});

app.get('/api/reconstruction/jobs/:id/files', async (req, res) => {
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
});


async function runJob(jobId) {
  let job = await fs.readJson(jobPath(jobId));
  job.status = 'running'; job.updatedAt = now();
  await writeJson(jobPath(jobId), job);
  const out = path.join(OUTPUTS, jobId);
  await fs.ensureDir(out);
  const runner = path.join(ROOT, 'python', 'mrl3d_job_runner.py');
  const args = [runner, '--scan-dir', scanDir(job.scanId), '--output-dir', out, '--mode', job.mode];
  const py = process.platform === 'win32' ? 'python' : 'python3';
  await appendLog(`runner start job=${jobId}`);
  const child = spawn(py, args, { cwd: ROOT });
  let stdout = ''; let stderr = '';
  child.stdout.on('data', d => stdout += d.toString());
  child.stderr.on('data', d => stderr += d.toString());
  const code = await new Promise(resolve => child.on('close', resolve));
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
  if (code === 0 && (!report || report.status === 'completed')) {
    job.status = 'completed';
    job.message = report?.reason || 'runner completed';
  } else {
    job.status = 'failed';
    job.message = report?.reason || stderr || stdout || `runner exit ${code}`;
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

const PORT = process.env.MRL_3D_BRIDGE_PORT || 3050;
app.listen(PORT, () => console.log(`MRL 3D Reconstruction Server running on ${PORT}`));
