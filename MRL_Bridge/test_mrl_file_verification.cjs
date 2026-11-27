'use strict';
// origin_signature: MrLiouWord
const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const crypto = require('node:crypto');
const vm = require('node:vm');
const { createRequire } = require('node:module');
const childProcess = require('node:child_process');
const { TranslationCenter } = require('./mrl_bridge_translation_center.cjs');
const sha = b => crypto.createHash('sha256').update(b).digest('hex');

async function fixture(run) {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), 'MRL-write-regression-'));
  const source = fs.readFileSync(path.join(__dirname, 'server.js'), 'utf8');
  const localRequire = createRequire(path.join(__dirname, 'server.js'));
  const injectedFs = Object.create(fs);
  const child = Object.create(childProcess);
  const context = { __filename: path.join(__dirname, 'server.js'), require(name) {
    if (name === 'fs') return injectedFs;
    if (name === 'child_process') return { execSync: (...args) => child.execSync(...args), execFileSync: (...args) => child.execFileSync(...args) };
    if (name === 'pg') return { Pool: class { on() {} } };
    if (name === 'ioredis') return class { on() {} };
    return localRequire(name);
  }, Buffer, console, URL, setTimeout, clearTimeout, setInterval() {},
  process: { env: { MRL_BRIDGE_API_KEY: 'isolated-test-only', MRL_BRIDGE_LOG_DIR: path.join(root, 'logs') },
    pid: process.pid, on() {}, version: process.version, platform: process.platform, arch: process.arch } };
  vm.createContext(context);
  vm.runInContext(source.replace(/boot\(\);\s*$/, '') + '\nglobalThis.application=app; globalThis.center=mrlTranslationCenter;', context);
  const server = context.application.listen(0, '127.0.0.1');
  await new Promise(resolve => server.once('listening', resolve));
  const request = async (route, body, method = 'POST') => {
    const response = await fetch(`http://127.0.0.1:${server.address().port}${route}`, {
      method, headers: { 'x-api-key': 'isolated-test-only', 'Content-Type': 'application/json' },
      ...(method === 'POST' ? { body: JSON.stringify(body) } : {}),
    });
    return { status: response.status, body: await response.json(), trace: response.headers.get('x-mrl-trace-id') };
  };
  try { await run({root, request, injectedFs, child, center:context.center}); }
  finally { await new Promise(resolve => server.close(resolve)); fs.rmSync(root, { recursive: true, force: true }); assert.equal(fs.existsSync(root), false); }
}

test('HTTP POST UTF-8/binary/empty writes: existence, independent read/hash, linked durable receipt and cleanup', () => fixture(async ({root, request}) => {
  for (const bytes of [Buffer.from('MRL 隔離測試\r\nsecond line'), Buffer.from([0,255,128,10]), Buffer.alloc(0)]) {
    const filepath = path.join(root, crypto.randomUUID(), 'payload.bin');
    const w = await request('/MRL_file/write', { filepath, b64: bytes.toString('base64') });
    assert.equal(w.status, 200); assert.equal(w.body.ok, true);
    assert.deepEqual(fs.readFileSync(filepath), bytes);
    assert.equal(w.body.verification.sha256, sha(bytes));
    assert.equal(w.body.verification.expected_sha256, sha(bytes));
    assert.equal(w.body.verification.trace_id, w.trace);
    const r = await request('/MRL_file/read', {filepath, encoding:'base64'});
    assert.equal(r.status,200); assert.equal(r.body.sha256,sha(bytes));
    assert.deepEqual(Buffer.from(r.body.content, 'base64'), bytes);
    const ledger = path.join(root,'logs',`MRL_bridge_translation-${process.pid}.jsonl`);
    const replay = new TranslationCenter(ledger);
    assert.ok(replay.sequence > 0);
    const records = fs.readFileSync(ledger,'utf8').trim().split('\n').map(JSON.parse);
    const event = records.find(x=>x.event_id===w.body.verification.event_id);
    assert.equal(event.payload_sha256,sha(bytes)); assert.equal(event.parent_ref,records.find(x=>x.trace_id===w.trace && x.status==='received').event_id);
    assert.ok(records.some(x=>x.parent_ref===event.event_id && x.status==='sent'));
    fs.unlinkSync(filepath); assert.equal((await request('/MRL_file/read',{filepath})).status,404);
  }
}));

test('GET base64 keeps original binary bytes and sliced reads identify full-file hash', () => fixture(async ({root,request})=>{
  const filepath=path.join(root,'get.bin'), bytes=Buffer.from([0,255,128]);
  const w=await request('/MRL_write?'+new URLSearchParams({path:filepath,b64:bytes.toString('base64')}),null,'GET');
  assert.equal(w.status,200); assert.deepEqual(fs.readFileSync(filepath),bytes);
  await request('/MRL_file/write',{filepath,content:'一\n二\n三'});
  const r=await request('/MRL_file/read',{filepath,lines:1,offset:1});
  assert.equal(r.body.content,'二'); assert.equal(r.body.sha256,sha(fs.readFileSync(filepath)));
  assert.equal(r.body.content_scope,'line-slice');
}));

test('invalid input rejected before creating a target',()=>fixture(async({root,request})=>{
  const filepath=path.join(root,'invalid');
  for(const body of [{filepath,b64:'%%%='},{filepath,content:123},{filepath,b64:'a'}]) {
    assert.equal((await request('/MRL_file/write',body)).status,400);
    assert.equal(fs.existsSync(filepath),false);
  }
}));

for (const fault of ['no-write','corruption','permission','read-error','fsync-error']) {
  test(`write fails closed on ${fault}`,()=>fixture(async({root,request,injectedFs})=>{
    const filepath=path.join(root,'fault.bin');
    if(fault==='no-write') injectedFs.writeFileSync=(fd,...args)=>{ if(typeof fd!=='number') return fs.writeFileSync(fd,...args); };
    if(fault==='corruption') injectedFs.writeFileSync=(fd,...args)=>fs.writeFileSync(fd,typeof fd==='number'?Buffer.from('wrong'):args[0],...args.slice(1));
    if(fault==='permission') injectedFs.openSync=(p,...args)=>{if(p===filepath)throw new Error('EACCES');return fs.openSync(p,...args);};
    if(fault==='read-error') injectedFs.readFileSync=(p,...args)=>{if(p===filepath)throw new Error('read failed');return fs.readFileSync(p,...args);};
    if(fault==='fsync-error') injectedFs.fsyncSync=()=>{throw new Error('sync failed');};
    const r=await request('/MRL_file/write',{filepath,content:'expected'});
    assert.equal(r.status,500); assert.equal(r.body.ok,false); assert.equal(r.body.verification,undefined);
  }));
}

test('both execution routes use strict encoded PowerShell and return HTTP failure',()=>fixture(async({root,request,child})=>{
  const calls=[];
  child.execFileSync=(shell,args)=>{ calls.push({shell,args}); const e=new Error('command failed'); e.status=1;e.stderr='failure';e.stdout='';throw e; };
  for(const route of ['/MRL_run?'+new URLSearchParams({cmd:'Write-Error boom',cwd:root}),'/MRL_exec']) {
    const r=await request(route,{cmd:'Write-Error boom',cwd:root},route.startsWith('/MRL_run')?'GET':'POST');
    assert.equal(r.status,500);assert.equal(r.body.ok,false);assert.equal(r.body.exitCode,1);
  }
  assert.equal(calls.length,2);
  const script=Buffer.from(calls[0].args.at(-1),'base64').toString('utf16le');
  assert.match(script,/ErrorActionPreference='Stop'/);assert.match(script,/Write-Error boom/);
  child.execFileSync=()=> 'done';
  const r=await request('/MRL_exec',{cmd:'write-output done',cwd:root});
  assert.equal(r.body.execution.file_verified,false);assert.equal(r.body.execution.scope,'process-only');
}));

test('native Windows PowerShell errors/native exits and successful write/read/hash', {skip:process.platform!=='win32'},()=>fixture(async({root,request})=>{
  for(const cmd of ['Write-Error boom', "Set-Content -LiteralPath 'Z:\\MRL-missing\\x' -Value x", 'cmd /c exit 7']) {
    const r=await request('/MRL_exec',{cmd,cwd:root});assert.equal(r.status,500);assert.equal(r.body.ok,false);
  }
  const filepath=path.join(root,'powershell.txt');
  const cmd=`[IO.File]::WriteAllText('${filepath.replaceAll("'","''")}', 'MRL isolated')`;
  const r=await request('/MRL_run?'+new URLSearchParams({cmd,cwd:root}),null,'GET');
  assert.equal(r.status,200);assert.equal(r.body.execution.file_verified,false);
  const read=await request('/MRL_file/read',{filepath});
  assert.equal(read.body.sha256,sha(Buffer.from('MRL isolated')));
}));


test('receipt append failure never returns verified success after file mutation',()=>fixture(async({root,request,center})=>{
  const label=center.label.bind(center);
  center.label=(...args)=>{if(args[2].status==='file_readback_verified')throw new Error('receipt disk full');return label(...args);};
  const filepath=path.join(root,'receipt-failure');
  const r=await request('/MRL_file/write',{filepath,content:'isolated'});
  assert.equal(r.status,500);assert.equal(r.body.ok,false);
  assert.equal(fs.readFileSync(filepath,'utf8'),'isolated');
  assert.equal(r.body.verification,undefined);
}));

test('command timeout returns HTTP 504',()=>fixture(async({root,request,child})=>{
  child.execFileSync=()=>{const e=new Error('timed out');e.signal='SIGTERM';e.status=null;throw e;};
  const r=await request('/MRL_exec',{cmd:'Start-Sleep 99',cwd:root});
  assert.equal(r.status,504);assert.equal(r.body.ok,false);
}));
