import test from 'node:test';
import assert from 'node:assert/strict';
import { execFileSync, spawnSync } from 'node:child_process';
import { createServer } from 'node:http';
import { mkdirSync, mkdtempSync, readFileSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { dirname, extname, join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { createHash, randomBytes } from 'node:crypto';
import { runInNewContext } from 'node:vm';
import puppeteer from 'puppeteer';
import { corsHeaders, isAllowedOrigin } from '../../../lib/Mrliou_MRL_public_cors_v1.mjs';

const PACKAGE = resolve(dirname(fileURLToPath(import.meta.url)), '..');
const BUILD = join(PACKAGE, 'scripts/Mrliou_MRL_build_pages_v1.mjs');
const VERIFY = join(PACKAGE, 'scripts/Mrliou_MRL_verify_pages_v1.mjs');
const HEAD = 'a'.repeat(40);
const loadVerifier = () => {
  const window = {};
  runInNewContext(readFileSync(join(PACKAGE, 'src/app.js'), 'utf8'), {
    window, URL, setTimeout,
    document: {getElementById: () => ({addEventListener() {}})},
  });
  return window.MRLPages;
};
const liveReceipt = () => {
  const h = 'b'.repeat(64);
  return {schema:'MRL_AI_Mother_Live_Acceptance_v1',canonical_id:'MRL_AI_Mother_Autonomous_Runtime_Baseline_v1',origin_signature:'MrLiouWord',git_head:HEAD,hardware_id:'MRL_test',runtime_id:'test',backend:'ollama',model:'test',model_endpoint:'http://127.0.0.1:11434',model_release_id:'MRL_release',model_release_manifest_sha256:h,model_artifact_sha256:h,model_artifact_size_bytes:1,model_sha256_verified:true,health_ready:true,memory_chain_head:h,evidence_chain_head:h,passport_hash:h,return_anchor:h,evidence_ref:h,request_sha256:h,result_sha256:h,external_model_disconnected:true,accepted_at:'2026-09-16T00:00:00Z',operator_id:'MRL_operator',acceptance_gate:'MRL_AI_MOTHER_AUTONOMOUS_RUNTIME_ACCEPTANCE_PASS'};
};
const routeReceipt = (mode = 'PUBLIC_HTTPS') => ({
  schema:'MRL_APIWorks_Public_Route_Receipt_v1',origin_signature:'MrLiouWord',capture_mode:mode,
  probe_git_head:HEAD,route_map_sha256:'b'.repeat(64),
  public_route_gate:mode === 'PUBLIC_HTTPS' ? 'PUBLIC_ROUTE_HTTP_PASS' : 'PUBLIC_ROUTE_TEST_PASS',
  routes:[{http_status:200,expected_status:200,error:null,status_match:true,response_sha256:'b'.repeat(64),response_size_bytes:1}],
});

test('live receipts enforce literal loopback and reject URL normalization bypasses', () => {
  const {verifyLive} = loadVerifier();
  for (const endpoint of ['http://127.0.0.1:11434','https://localhost/v1','http://[::1]:8080/v1']) {
    assert.equal(verifyLive({...liveReceipt(),model_endpoint:endpoint}).length,0,endpoint);
  }
  for (const endpoint of ['https://api.openai.com','http://localhost.evil.test','http://user:pass@localhost',
    'http://localhost?token=secret','http://localhost/#private','file:///model','http://127.1',
    'http://2130706433','http://0x7f000001','http://127.0.0.1:99999','http://local\nhost',
    'http://localhost\\@evil.test','http://localhost@evil.test','//localhost','not-a-url']) {
    assert.ok(verifyLive({...liveReceipt(),model_endpoint:endpoint}).some(x=>x.startsWith('model_endpoint')),endpoint);
  }
  assert.ok(verifyLive(null).length);
});

test('route status zero never matches or produces a successful route gate', () => {
  const {verifyRoutes} = loadVerifier();
  for (const mode of ['PUBLIC_HTTPS','TEST_LOOPBACK']) {
    const receipt=routeReceipt(mode);
    assert.equal(verifyRoutes(receipt).length,0);
    receipt.routes[0]={...receipt.routes[0],http_status:0,expected_status:0,status_match:true,response_size_bytes:0};
    const failures=verifyRoutes(receipt);
    assert.ok(failures.some(x=>x.includes('expected_status')));
    assert.ok(failures.some(x=>x.includes('status_match')));
    assert.ok(failures.some(x=>x.includes('public_route_gate')));
    receipt.routes[0]={...receipt.routes[0],expected_status:200,status_match:false,error:'TimeoutError: fixture'};
    receipt.public_route_gate=mode==='PUBLIC_HTTPS'?'PUBLIC_ROUTE_HTTP_FAIL':'PUBLIC_ROUTE_TEST_FAIL';
    assert.equal(verifyRoutes(receipt).length,0,'a faithfully recorded transport failure remains valid failure evidence');
  }
  for (const status of [-1,1,99,600,200.5,'200',true,null]) {
    const receipt=routeReceipt(); receipt.routes[0].http_status=status; receipt.routes[0].expected_status=status;
    assert.ok(verifyRoutes(receipt).length,`invalid status ${status}`);
  }
  assert.ok(verifyRoutes({...routeReceipt(),routes:[null]}).length);
});

test('incremental SHA-256 matches independent native crypto at padding and chunk boundaries', async () => {
  const {hashModelFile,MODEL_CHUNK_BYTES}=loadVerifier();
  const vectors=[Buffer.alloc(0),Buffer.from('abc'),Buffer.alloc(1000000,97)];
  for (const size of [1,55,56,63,64,65,119,120,127,128,129,MODEL_CHUNK_BYTES-1,MODEL_CHUNK_BYTES,MODEL_CHUNK_BYTES+1,MODEL_CHUNK_BYTES*2+57]) vectors.push(randomBytes(size));
  for (const bytes of vectors) {
    const file=new Blob([bytes]);
    const slices=[];
    const bounded={size:file.size,arrayBuffer:()=>{throw new Error('whole-file read forbidden');},slice:(start,end)=>{
      assert.ok(end-start<=MODEL_CHUNK_BYTES); slices.push([start,end]); return file.slice(start,end);
    }};
    const progress=[];
    assert.equal(await hashModelFile(bounded,(done)=>progress.push(done)),createHash('sha256').update(bytes).digest('hex'),`size ${bytes.length}`);
    assert.equal(slices.length,Math.ceil(bytes.length/MODEL_CHUNK_BYTES));
    if(bytes.length) assert.equal(progress.at(-1),bytes.length);
  }
  await assert.rejects(()=>hashModelFile({size:8,slice:()=>new Blob([new Uint8Array(2)])}),/short read/);
  await assert.rejects(()=>hashModelFile({size:Number.MAX_SAFE_INTEGER+1}),/invalid size/);
});

test('Pages CI triggers on both CORS inputs for pull requests and main pushes', () => {
  const workflow=readFileSync(join(PACKAGE,'../../.github/workflows/mrliou-mrl-pages-static.yml'),'utf8');
  const pr=workflow.split('  pull_request:')[1].split('  push:')[0];
  const push=workflow.split('  push:')[1].split('\npermissions:')[0];
  for(const section of [pr,push]) for(const path of ['lib/Mrliou_MRL_public_cors_v1.mjs','middleware.js']) assert.ok(section.includes(`- "${path}"`));
});

test('SHA-256 preserves the high length word beyond 512 MiB with bounded reads', async () => {
  const {hashModelFile,MODEL_CHUNK_BYTES}=loadVerifier();
  const size=512*1024*1024+1;
  const native=createHash('sha256');
  let largestRead=0;
  const file={size,slice(start,end){
    largestRead=Math.max(largestRead,end-start);
    const bytes=Buffer.alloc(end-start,0x5a); native.update(bytes);
    return new Blob([bytes]);
  }};
  assert.equal(await hashModelFile(file),native.digest('hex'));
  assert.equal(largestRead,MODEL_CHUNK_BYTES);
});
const build = () => {
  const parent = mkdtempSync(join(tmpdir(), 'mrl-pages-'));
  const output = join(parent, 'out');
  execFileSync(process.execPath, [BUILD, '--output', output], {env:{...process.env,MRL_SOURCE_HEAD:HEAD}});
  return output;
};

test('CORS permits only canonical or explicitly configured Pages origins', () => {
  assert.equal(isAllowedOrigin('https://flow-tasks.pages.dev'), true);
  assert.equal(isAllowedOrigin('https://mrliouword.com'), true);
  assert.equal(isAllowedOrigin('https://preview.example', 'https://preview.example'), true);
  assert.equal(isAllowedOrigin('https://evil.example'), false);
  assert.deepEqual(corsHeaders('https://flow-tasks.pages.dev'), {
    'Access-Control-Allow-Origin':'https://flow-tasks.pages.dev',
    'Access-Control-Allow-Methods':'GET, OPTIONS',
    'Access-Control-Allow-Headers':'Accept, Content-Type',
    'Access-Control-Max-Age':'86400',Vary:'Origin',
  });
});

test('build has exact inventory and tamper detection', () => {
  const output = build();
  const pass = JSON.parse(execFileSync(process.execPath, [VERIFY, output], {encoding:'utf8'}));
  assert.equal(pass.integrity_gate, 'PASS'); assert.equal(pass.expected_count, 9); assert.equal(pass.actual_count, 9);
  assert.match(readFileSync(join(output, 'index.html'), 'utf8'), /build aaaaaaaaaaaa/);
  execFileSync(process.execPath, [BUILD, '--output', output], {env:{...process.env,MRL_SOURCE_HEAD:HEAD}});
  const repeated = JSON.parse(execFileSync(process.execPath, [VERIFY, output], {encoding:'utf8'}));
  assert.equal(repeated.integrity_gate, 'PASS');
  writeFileSync(join(output, 'styles.css'), 'tampered', 'utf8');
  const failed = spawnSync(process.execPath, [VERIFY, output], {encoding:'utf8'});
  assert.notEqual(failed.status, 0); assert.match(failed.stdout, /checksum mismatch/);
  const foreign=join(dirname(output),'foreign'); mkdirSync(foreign); writeFileSync(join(foreign,'unrelated.txt'),'do not replace');
  const refused=spawnSync(process.execPath,[BUILD,'--output',foreign],{env:{...process.env,MRL_SOURCE_HEAD:HEAD},encoding:'utf8'});
  assert.notEqual(refused.status,0); assert.equal(readFileSync(join(foreign,'unrelated.txt'),'utf8'),'do not replace');
});

test('browser renders and validates a local receipt without upload', async (context) => {
  const output = build();
  const types = {'.html':'text/html; charset=utf-8','.js':'text/javascript; charset=utf-8','.css':'text/css; charset=utf-8','.json':'application/json'};
  const server = createServer((request, response) => {
    const name = request.url === '/' ? 'index.html' : request.url.slice(1);
    try { response.setHeader('content-type', types[extname(name)] || 'text/plain'); response.end(readFileSync(join(output, name))); }
    catch { response.statusCode=404; response.end(readFileSync(join(output,'404.html'))); }
  });
  await new Promise((resolveReady) => server.listen(0, '127.0.0.1', resolveReady));
  let browser;
  try {
    browser = await puppeteer.launch({headless:true,args:['--no-sandbox']});
  } catch (error) {
    server.close();
    if (process.env.MRL_REQUIRE_BROWSER === '1') throw error;
    context.skip(`Chromium unavailable: ${error.message}`); return;
  }
  try {
    const page = await browser.newPage();
    const consoleErrors=[]; page.on('console',(message)=>{if(message.type()==='error')consoleErrors.push(message.text());}); page.on('pageerror',(error)=>consoleErrors.push(error.message));
    await page.setViewport({width:390,height:844,deviceScaleFactor:1});
    await page.goto(`http://127.0.0.1:${server.address().port}/`,{waitUntil:'networkidle0'});
    assert.equal(await page.$$eval('main section', nodes=>nodes.length),4);
    assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth<=document.documentElement.clientWidth),true);
    const receiptPath=join(dirname(output),'receipt.json');
    const h='b'.repeat(64);
    writeFileSync(receiptPath,JSON.stringify({schema:'MRL_AI_Mother_Live_Acceptance_v1',canonical_id:'MRL_AI_Mother_Autonomous_Runtime_Baseline_v1',origin_signature:'MrLiouWord',git_head:'a'.repeat(40),hardware_id:'MRL_test',runtime_id:'test',backend:'ollama',model:'test',model_endpoint:'http://127.0.0.1:1',model_release_id:'MRL_release',model_release_manifest_sha256:h,model_artifact_sha256:h,model_artifact_size_bytes:1,model_sha256_verified:true,health_ready:true,memory_chain_head:h,evidence_chain_head:h,passport_hash:h,return_anchor:h,evidence_ref:h,request_sha256:h,result_sha256:h,external_model_disconnected:true,accepted_at:'2026-09-16T00:00:00Z',operator_id:'MRL_operator',acceptance_gate:'MRL_AI_MOTHER_AUTONOMOUS_RUNTIME_ACCEPTANCE_PASS'}));
    const input=await page.$('#receipt-file'); await input.uploadFile(receiptPath); await page.click('#verify-receipt');
    await page.waitForFunction(()=>document.querySelector('#verify-result').classList.contains('pass'));
    assert.match(await page.$eval('#verify-result',node=>node.textContent),/^PASS/);
    const requests=[]; page.on('request',request=>requests.push(request.url()));
    const modelPath=join(dirname(output),'model.fixture');
    const modelBytes=Buffer.from('MRL local model artifact fixture');
    writeFileSync(modelPath,modelBytes);
    const localReceipt={...liveReceipt(),model_artifact_size_bytes:modelBytes.length,model_artifact_sha256:createHash('sha256').update(modelBytes).digest('hex')};
    writeFileSync(receiptPath,JSON.stringify(localReceipt)); await input.uploadFile(receiptPath);
    await (await page.$('#model-file')).uploadFile(modelPath); await page.click('#verify-receipt');
    await page.waitForFunction(()=>!document.querySelector('#verify-receipt').disabled);
    assert.match(await page.$eval('#verify-result',node=>node.textContent),/PASS.*[\s\S]*hash／size 相符/);
    localReceipt.model_artifact_sha256='0'.repeat(64);
    writeFileSync(receiptPath,JSON.stringify(localReceipt)); await input.uploadFile(receiptPath); await page.click('#verify-receipt');
    await page.waitForFunction(()=>!document.querySelector('#verify-receipt').disabled);
    assert.match(await page.$eval('#verify-result',node=>node.textContent),/FAIL.*[\s\S]*SHA-256 mismatch/);
    localReceipt.model_endpoint='https://external.example/model';
    writeFileSync(receiptPath,JSON.stringify(localReceipt)); await input.uploadFile(receiptPath); await page.click('#verify-receipt');
    await page.waitForFunction(()=>!document.querySelector('#verify-receipt').disabled);
    assert.match(await page.$eval('#verify-result',node=>node.textContent),/FAIL.*[\s\S]*model_endpoint/);
    await page.$eval('#model-file',node=>{node.value='';});
    const invalidRoute=routeReceipt(); invalidRoute.routes[0].http_status=0; invalidRoute.routes[0].expected_status=0;
    writeFileSync(receiptPath,JSON.stringify(invalidRoute)); await input.uploadFile(receiptPath); await page.click('#verify-receipt');
    await page.waitForFunction(()=>!document.querySelector('#verify-receipt').disabled);
    assert.match(await page.$eval('#verify-result',node=>node.textContent),/FAIL.*[\s\S]*public_route_gate/);
    assert.deepEqual(requests,[],'receipt and model verification must never make network requests');
    await page.type('#worker-url','http://example.com'); await page.click('#check-status');
    await page.waitForFunction(()=>document.querySelector('#status-result').classList.contains('fail'));
    assert.deepEqual(consoleErrors,[]);
  } finally { await browser.close(); server.close(); }
});
