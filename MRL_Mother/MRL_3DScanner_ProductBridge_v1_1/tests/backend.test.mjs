import { test } from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import os from 'node:os';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { spawn } from 'node:child_process';
const source = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '../backend/MRL_3D_Reconstruction_Server');
const base = 'http://127.0.0.1:3050';
const python = process.env.MRL_TEST_PYTHON || '/usr/bin/python3';
const pause = ms => new Promise(r => setTimeout(r, ms));
async function start(kind) {
  // Refuse to touch an existing listener; all writes are to a unique temporary tree.
  try { await fetch(base + '/api/health'); throw new Error('Port 3050 occupied; stop test'); }
  catch (e) { if (e.message === 'Port 3050 occupied; stop test') throw e; }
  const root = await fs.mkdtemp(path.join(os.tmpdir(), 'mrl-bridge-test-'));
  await fs.cp(source, root, { recursive: true, filter: p => !p.includes('node_modules') && !p.includes('storage') });
  await fs.symlink(path.join(source, 'node_modules'), path.join(root, 'node_modules'), 'dir');
  if (kind === 'missing-report') await fs.writeFile(path.join(root, 'python/mrl3d_job_runner.py'), 'import sys\nsys.exit(0)\n');
  if (kind === 'interrupted') {
    await fs.mkdir(path.join(root, 'storage/jobs'), {recursive:true});
    await fs.writeFile(path.join(root, 'storage/jobs/old.json'), JSON.stringify({jobId:'old',status:'running'}));
  }
  const child = spawn(process.execPath, [path.join(root, 'server.js')], {cwd:root, env:{...process.env, MRL_BRIDGE_INSTANCE:'test', ...(kind==='missing-colmap'?{PATH:'/usr/bin:/bin'}:{}), MRL_3D_BRIDGE_PORT:'3050', MRL_BRIDGE_PYTHON:kind==='missing-python'?path.join(root,'absent-python'):python}, stdio:['ignore','pipe','pipe']});
  let logs=''; child.stderr.on('data', d => logs += d);
  for (let i=0;i<100;i++) {
    if (child.exitCode !== null) throw new Error(logs);
    try { const h=await (await fetch(base+'/api/health')).json(); if(h.pid === child.pid) return {root,child}; } catch {}
    await pause(50);
  }
  child.kill(); throw new Error('startup timeout '+logs);
}
async function stop(s) { const done=new Promise(r=>s.child.once('exit',r)); s.child.kill(); await done; await fs.rm(s.root,{recursive:true,force:true}); }
async function upload(id, content='v 0 0 0', filename='mesh.obj') {
  const form=new FormData();form.append('files',new Blob([content]),filename);
  return fetch(base+'/api/scans/upload',{method:'POST',headers:{'X-MRL-Scan-ID':id},body:form});
}
async function job(id) {
  const j=await (await fetch(base+'/api/reconstruction/jobs',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({scanId:id})})).json();
  for(let i=0;i<100;i++) { const status=await (await fetch(base+'/api/reconstruction/jobs/'+j.jobId)).json();if(['completed','failed'].includes(status.status))return status;await pause(50); }
  throw new Error('job timeout');
}
test('health, upload preservation, empty upload, invalid scan and restart evidence',async()=>{
  const s=await start('interrupted');try {
    const h=await (await fetch(base+'/api/health')).json();assert.equal(h.port,3050);assert.equal(h.pid,s.child.pid);assert.equal(h.instance,'test');
    const old=JSON.parse(await fs.readFile(path.join(s.root,'storage/jobs/old.json')));assert.equal(old.status,'failed');assert.equal(old.message,'INTERRUPTED_BY_BACKEND_RESTART');
    const response=await upload('unique');assert.equal(response.status,200);assert.equal((await response.json()).uploaded,1);
    assert.equal((await upload('unique','different')).status,409);
    assert.equal(await fs.readFile(path.join(s.root,'storage/uploads/unique/mesh.obj'),'utf8'),'v 0 0 0');
    assert.equal((await upload('../escape')).status,400);
    assert.equal((await fetch(base+'/api/scans/upload',{method:'POST',body:new FormData()})).status,400);
  } finally {await stop(s);}
});
test('missing Python produces terminal failure, never stuck running',async()=>{
 const s=await start('missing-python');try {await upload('missing_python');const j=await job('missing_python');assert.equal(j.status,'failed');assert.match(j.message,/ENOENT/);}finally{await stop(s);}
});
test('exit zero without runner report is failure',async()=>{
 const s=await start('missing-report');try {await upload('missing_report');const j=await job('missing_report');assert.equal(j.status,'failed');assert.equal(j.message,'RUNNER_REPORT_MISSING');assert.equal(j.exitCode,0);}finally{await stop(s);}
});
test('wrong port configuration is rejected',async()=>{
 const c=spawn(process.execPath,[path.join(source,'server.js')],{env:{...process.env,MRL_3D_BRIDGE_PORT:'3051'}});let err='';c.stderr.on('data',d=>err+=d);const code=await new Promise(r=>c.on('exit',r));assert.notEqual(code,0);assert.match(err,/requires port 3050/);
});

test('image upload passes while real runner fails independently for missing COLMAP',async()=>{
 const s=await start('missing-colmap');try {
   const u=await upload('missing_colmap','photo fixture','photo.jpg');assert.equal(u.status,200);assert.equal((await u.json()).uploaded,1);
   const j=await job('missing_colmap');assert.equal(j.status,'failed');assert.equal(j.exitCode,3);assert.match(j.message,/COLMAP_NOT_FOUND/);assert.equal(j.report.status,'failed');
   const h=await (await fetch(base+'/api/health')).json();assert.equal(h.ok,true);
 }finally{await stop(s);}
});
