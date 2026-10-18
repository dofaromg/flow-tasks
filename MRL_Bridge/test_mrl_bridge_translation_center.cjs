'use strict';
// origin_signature: MrLiouWord
const test = require('node:test');
const assert = require('node:assert/strict');
const http = require('node:http');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const crypto = require('node:crypto');
const { TranslationCenter } = require('./mrl_bridge_translation_center.cjs');

async function running(center, callback) {
  const middleware = center.middleware();
  const server = http.createServer((req, res) => middleware(req, res, () => {
    req.resume();
    req.once('end', () => {
      res.statusCode = req.url.startsWith('/denied') ? 401 : 200;
      res.write('MRL:');
      res.end(Buffer.from([0, 255]));
    });
  }));
  await new Promise(resolve => server.listen(0, '127.0.0.1', resolve));
  try { await callback(server.address().port); }
  finally { await new Promise(resolve => server.close(resolve)); }
}

function request(port, route, bytes) {
  return new Promise((resolve, reject) => {
    const req = http.request({ host: '127.0.0.1', port, path: route, method: 'POST',
      headers: { 'X-MRL-Trace-Id': 'untrusted-client-trace', 'Content-Length': bytes.length } }, res => {
      const chunks = [];
      res.on('data', chunk => chunks.push(chunk));
      res.on('end', () => resolve({ headers: res.headers, status: res.statusCode, body: Buffer.concat(chunks) }));
    });
    req.on('error', reject);
    req.end(bytes);
  });
}

test('real HTTP binary request/streamed response and error traffic keep labels', async () => {
  const center = new TranslationCenter();
  await running(center, async port => {
    for (const route of ['/ok?token=never-record', '/denied']) {
      const body = Buffer.from([0, 128, 255]);
      const result = await request(port, route, body);
      assert.equal(result.headers['x-mrl-affiliation'], 'MRL');
      assert.notEqual(result.headers['x-mrl-trace-id'], 'untrusted-client-trace');
      assert.deepEqual(result.body, Buffer.concat([Buffer.from('MRL:'), Buffer.from([0, 255])]));
      const records = center.recent.filter(r => r.trace_id === result.headers['x-mrl-trace-id']);
      assert.equal(records.length, 3);
      assert.equal(records[1].payload_sha256, crypto.createHash('sha256').update(body).digest('hex'));
      assert.equal(records[2].payload_sha256, crypto.createHash('sha256').update(result.body).digest('hex'));
      assert.equal(records[2].parent_ref, records[1].event_id);
      assert.equal(records[2].http_status, route === '/denied' ? 401 : 200);
      assert.equal(JSON.stringify(records).includes('never-record'), false);
    }
  });
});

test('append-only ledger survives restart; tampering fails', async () => {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'MRL-bridge-'));
  const ledger = path.join(dir, 'ledger.jsonl');
  try {
    const center = new TranslationCenter(ledger);
    await running(center, port => request(port, '/ok', Buffer.from('hello')));
    const reopened = new TranslationCenter(ledger);
    assert.equal(reopened.sequence, 3);
    const original = fs.readFileSync(ledger, 'utf8');
    fs.writeFileSync(ledger, original.replace('"mrl_affiliation":"MRL"', '"mrl_affiliation":"OTHER"'));
    assert.throws(() => new TranslationCenter(ledger), /integrity failure/);
  } finally { fs.rmSync(dir, { recursive: true }); }
});

test('audit storage failure prevents unrecorded dispatch', async () => {
  const center = new TranslationCenter();
  center.label = () => { throw new Error('disk unavailable'); };
  await running(center, async port => {
    const result = await request(port, '/ok', Buffer.from('hello'));
    assert.equal(result.status, 503);
    assert.equal(result.headers['x-mrl-affiliation'], 'MRL');
    assert.equal(center.lastError, 'AUDIT_APPEND_FAILED');
  });
});
