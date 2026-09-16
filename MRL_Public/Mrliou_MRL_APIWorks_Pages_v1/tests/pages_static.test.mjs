import test from 'node:test';
import assert from 'node:assert/strict';
import { execFileSync, spawnSync } from 'node:child_process';
import { createServer } from 'node:http';
import { mkdirSync, mkdtempSync, readFileSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { dirname, extname, join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import puppeteer from 'puppeteer';
import { corsHeaders, isAllowedOrigin } from '../../../lib/Mrliou_MRL_public_cors_v1.mjs';

const PACKAGE = resolve(dirname(fileURLToPath(import.meta.url)), '..');
const BUILD = join(PACKAGE, 'scripts/Mrliou_MRL_build_pages_v1.mjs');
const VERIFY = join(PACKAGE, 'scripts/Mrliou_MRL_verify_pages_v1.mjs');
const HEAD = 'a'.repeat(40);
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
    await page.type('#worker-url','http://example.com'); await page.click('#check-status');
    await page.waitForFunction(()=>document.querySelector('#status-result').classList.contains('fail'));
    assert.equal(consoleErrors.length,0);
  } finally { await browser.close(); server.close(); }
});
