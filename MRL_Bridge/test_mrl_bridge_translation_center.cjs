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

async function running(center, callback, handler) {
  const middleware = center.middleware();
  const admission = center.admission();
  const server = http.createServer((req, res) => middleware(req, res, () => admission(req, res, () => {
      if (handler) return handler(req, res);
      res.statusCode = req.url.startsWith('/denied') ? 401 : 200;
      res.write('MRL:');
      res.end(Buffer.from([0, 255]));
  })));
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

test('body append failure after admission record blocks downstream operation', async () => {
  const center = new TranslationCenter();
  const label = center.label.bind(center);
  center.label = (...args) => {
    if (args[2].status === 'received') throw new Error('disk full after started');
    return label(...args);
  };
  await running(center, async port => {
    const result = await request(port, '/ok', Buffer.from('sensitive operation'));
    assert.equal(result.status, 503);
    assert.equal(result.body.includes(Buffer.from('MRL:')), false);
    assert.equal(center.recent.some(r => r.status === 'received'), false);
  });
});

test('oversized unparsed binary bodies are rejected before route dispatch', async () => {
  const center = new TranslationCenter(undefined, { maxBodyBytes: 4 });
  await running(center, async port => {
    const result = await request(port, '/ok', Buffer.from('too large'));
    assert.equal(result.status, 413);
    assert.equal(result.headers['x-mrl-affiliation'], 'MRL');
    assert.equal(center.recent.some(r => r.status === 'body_limit_exceeded'), true);
  });
});

test('chunked binary input cannot bypass the body limit', async () => {
  const center = new TranslationCenter(undefined, { maxBodyBytes: 4 });
  await running(center, async port => {
    const result = await new Promise((resolve, reject) => {
      const req = http.request({ host: '127.0.0.1', port, path: '/ok', method: 'POST',
        headers: { 'Content-Type': 'application/octet-stream' } }, res => {
        res.resume(); res.on('end', () => resolve(res.statusCode));
      });
      req.on('error', reject);
      req.write('12345'); req.end();
    });
    assert.equal(result, 413);
  });
});

test('slow unfinished body times out without dispatch', async () => {
  const center = new TranslationCenter(undefined, { bodyTimeoutMs: 50 });
  await running(center, async port => {
    const status = await new Promise((resolve, reject) => {
      const req = http.request({ host: '127.0.0.1', port, path: '/ok', method: 'POST',
        headers: { 'Content-Type': 'application/octet-stream' } }, res => {
        res.resume(); res.on('end', () => resolve(res.statusCode));
      });
      req.on('error', reject);
      req.write('partial');
    });
    assert.equal(status, 408);
    assert.equal(center.recent.some(r => r.status === 'body_timeout'), true);
    assert.equal(center.recent.some(r => r.status === 'received'), false);
  });
});

test('artifact action links inbound, tag and outbound events', async () => {
  const center = new TranslationCenter();
  await running(center, async port => {
    const result = await request(port, '/artifact', Buffer.from('{}'));
    assert.equal(result.status, 200);
    const records = center.recent;
    assert.equal(records.length, 4);
    assert.equal(records[2].parent_ref, records[1].event_id);
    assert.equal(records[3].parent_ref, records[2].event_id);
  }, (req, res) => {
    const bytes = Buffer.from('original code');
    const record = center.label(crypto.createHash('sha256').update(bytes).digest('hex'), bytes.length, {
      trace_id: req.mrlBridge.trace_id, parent_ref: req.mrlBridge.inbound_event_id,
      source_ref: 'authenticated-bridge-input', destination_ref: 'MRL.artifact-envelope',
      direction: 'internal', status: 'tagged',
    });
    req.mrlBridge.last_event_id = record.event_id;
    res.end('tagged');
  });
});

test('ledger replay streams across UTF-8 chunks and each append fsyncs', () => {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'MRL-stream-'));
  const ledger = path.join(dir, 'ledger.jsonl');
  const readFile = fs.readFileSync;
  const fsync = fs.fsyncSync;
  let syncCount = 0;
  try {
    fs.fsyncSync = function(fd) { syncCount++; return fsync(fd); };
    const center = new TranslationCenter(ledger);
    for (let n = 0; n < 150; n++) center.label('0'.repeat(64), 0, {
      trace_id: crypto.randomUUID(), source_ref: 'MRL來源', destination_ref: 'MRL目的',
      direction: 'internal', status: 'observed',
    });
    assert.equal(syncCount, 150);
    assert.ok(fs.statSync(ledger).size > 64 * 1024);
    fs.readFileSync = () => { throw new Error('Whole-ledger read is forbidden'); };
    assert.equal(new TranslationCenter(ledger).sequence, 150);
  } finally {
    fs.readFileSync = readFile;
    fs.fsyncSync = fsync;
    fs.rmSync(dir, { recursive: true });
  }
});
