'use strict';
// Test fixtures are synthetic and never represent recovered canonical S4/S3.5.
// origin_signature: MrLiouWord
const test = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const os = require('node:os');
const http = require('node:http');
const { spawnSync } = require('node:child_process');
const express = require('express');
const Ajv = require('ajv');
const { DatasetRegistry, compute, checkSnapshot, hash, names, sourceBytes } = require('./engine.cjs');
const { install, PREFIX } = require('./adapter.cjs');
const { handle, invoke } = require('./mcp_stdio.cjs');
const { contracts, outputSchema } = require('./contracts.cjs');
const { register } = require('./register_dataset.cjs');
const { TranslationCenter } = require('../mrl_bridge_translation_center.cjs');
function fixture() {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), 'MRL-panini-test-'));
  const pin = (name, data, version) => {
    const filepath = path.join(root, name);
    const bytes = Buffer.from(JSON.stringify(data)); fs.writeFileSync(filepath, bytes);
    return { filepath, sha256: hash(bytes), ref: 'synthetic-test-only:' + name, version };
  };
  const S4 = pin('S4.json', { fixture: true }, 'v1.0.0');
  const S3_5 = pin('S3_5.json', { fixture: true }, 'fixture-v1');
  const provenance = ({ ref, sha256, version }) => ({ ref, sha256, version });
  const cluster = (name, layers) => ({ root: name, particles: layers.map((layer, i) => ({ id: name + ':' + i, layer })) });
  const data = { schema_version: 'MRL.PaniniClusterInput/v1.0.0', origin_signature: 'MrLiouWord',
    sources: { S4: provenance(S4), S3_5: provenance(S3_5) },
    clusters: [cluster('kriyā', ['L0', 'L0', 'LN', 'LC']), cluster('smṛti', ['L0', 'LC', 'LF']),
      cluster('nāman', ['L0', 'L0', 'LN']), cluster('viśeṣaṇa', ['L0', 'L0', 'LN']), cluster('bīja', ['LF'])] };
  const entry = { snapshot: pin('normalized.json', data, 'MRL.PaniniClusterInput/v1.0.0'), S4, S3_5 };
  const args = { dataset_id: 'test', expected_schema_version: 'panini_cluster_insight/v1.0.0', cluster_root: null, avg_cluster_size_ratio: null };
  return { root, data, entry, args, registry: new DatasetRegistry({ test: entry }), cleanup: () => fs.rmSync(root, { recursive: true }) };
}
function withFixture(fn) { const f = fixture(); try { return fn(f); } finally { f.cleanup(); } }

test('F1 scores unique layers and uses deterministic competition ties', () => withFixture(({ data }) => {
  const rows = compute('F1', data);
  assert.deepEqual(rows.map(r => [r.cluster, r.activity, r.rank]), [['kriyā', 12, 1], ['smṛti', 9, 2], ['nāman', 6, 3], ['viśeṣaṇa', 6, 3], ['bīja', 1, 5]]);
  const reversed = structuredClone(data); reversed.clusters.reverse();
  assert.deepEqual(compute('F1', reversed), rows);
}));
test('F2 exposes all applicable phases, requiring LF for triple', () => withFixture(({ data }) => {
  const rows = compute('F2', data);
  assert.deepEqual(rows[0].aspects, ['parse_runtime_mirror', 'capability_grounding']);
  assert.deepEqual(rows[1].aspects, ['triple_aspect', 'capability_grounding']);
  assert.deepEqual(rows[4].aspects, ['isolated_emergence']);
  const c = structuredClone(data); c.clusters[0].particles = [{ id: 'f', layer: 'LF' }, { id: 'n', layer: 'LN' }];
  assert.deepEqual(compute('F2', c)[0].aspects, ['flow_bridge']);
}));
test('F3 evaluates the specified logarithmic formula with no guessed ratio', () => withFixture(({ data }) => {
  const r = compute('F3', data, 0.5); assert.equal(r.D, Math.log(5) / Math.log(2));
  for (const ratio of [null, 0, 1, -1, Infinity, NaN, '0.5']) assert.throws(() => compute('F3', data, ratio), /F3_RATIO_DEFINITION_REQUIRED/);
}));
test('F4 returns attributed original profiles without invented historical claims', () => withFixture(({ data }) => {
  const rows = compute('F4', data); assert.equal(rows[0].source_pointer, '/key_insight_1_kriyā_activity_depth');
  assert.equal(rows[1].evidence_status, 'canonical_statement_not_independently_verified');
  assert.equal(rows[2].profile, null); assert.equal(rows[2].evidence_status, 'profile_not_present_in_source');
}));
test('F5 matches canonical smṛti 19 / kriyā 12 and preserves ties', () => withFixture(({ data }) => {
  const rows = compute('F5', data); assert.equal(rows[0].cluster, 'smṛti'); assert.equal(rows[0].intensity, 19);
  assert.equal(rows[1].intensity, 12); assert.equal(rows[2].rank, 3); assert.equal(rows[3].rank, 3);
}));
test('F6 recommendations are conditional and never create downstream modules', () => withFixture(({ data }) => {
  assert.equal(compute('F6', data).length, 3);
  assert.ok(compute('F6', data).every(s => s.creates_module === false));
  const c = structuredClone(data); c.clusters = [c.clusters[2]];
  assert.deepEqual(compute('F6', c), []);
}));
test('schema rejects empty, unknown layers, injected paths, duplicate roots and particle IDs', () => withFixture(({ data, registry, args }) => {
  for (const mutate of [d => { d.clusters = []; }, d => { d.clusters[0].particles[0].layer = 'L7'; },
    d => { d.clusters.push(d.clusters[0]); }, d => { d.clusters[0].particles[1].id = d.clusters[0].particles[0].id; },
    d => { d.origin_signature = 'other'; }]) {
    const c = structuredClone(data); mutate(c); assert.throws(() => checkSnapshot(c));
  }
  assert.throws(() => registry.call('F1', { ...args, filepath: 'private' }), /INVALID_CALL/);
  assert.throws(() => registry.call('F1', { ...args, expected_schema_version: 'v2' }), /INVALID_CALL/);
  assert.throws(() => registry.call('F7', args), /UNKNOWN_FUNCTION/);
  assert.throws(() => registry.call('F1', { ...args, dataset_id: 'absent' }), /DATASET_NOT_REGISTERED/);
}));
test('byte pins, S4 version and source lineage fail closed', () => withFixture(({ entry, args }) => {
  const r = () => new DatasetRegistry({ test: entry }).call('F1', args);
  const original = fs.readFileSync(entry.S4.filepath); fs.appendFileSync(entry.S4.filepath, ' ');
  assert.throws(r, /SOURCE_HASH_MISMATCH/); fs.writeFileSync(entry.S4.filepath, original);
  entry.S4.version = 'v2'; assert.throws(r, /UPSTREAM_VERSION_MISMATCH/); entry.S4.version = 'v1.0.0';
  entry.S3_5.ref = 'different'; assert.throws(r, /UPSTREAM_LINEAGE_MISMATCH/);
}));
test('F1-F6 results satisfy output schema, repeat exactly and do not mutate input or files', () => withFixture(({ registry, args, root }) => {
  const validateOutput = new Ajv({ strict: true }).compile(outputSchema);
  const before = Object.fromEntries(fs.readdirSync(root).map(n => [n, hash(fs.readFileSync(path.join(root, n)))]));
  for (const id of Object.keys(names)) {
    const a = { ...args, avg_cluster_size_ratio: id === 'F3' ? 0.5 : null };
    const result = registry.call(id, a); assert.equal(validateOutput(result), true, JSON.stringify(validateOutput.errors));
    assert.deepEqual(result, registry.call(id, a)); assert.equal(result.mutation, false);
  }
  const after = Object.fromEntries(fs.readdirSync(root).map(n => [n, hash(fs.readFileSync(path.join(root, n)))]));
  assert.deepEqual(before, after);
}));
test('tool and JSON Schema contracts are generated without drift; original size retained', () => {
  for (const [name, value] of Object.entries(contracts())) assert.deepEqual(JSON.parse(fs.readFileSync(path.join(__dirname, name))), value);
  assert.equal(sourceBytes.length, 14639);
});
test('F2/F4 root selector is exact; aggregate functions reject scope changes', () => withFixture(({ registry, args }) => {
  assert.equal(registry.call('F2', { ...args, cluster_root: 'smṛti' }).result.length, 1);
  assert.equal(registry.call('F4', { ...args, cluster_root: 'kriyā' }).result[0].cluster, 'kriyā');
  assert.throws(() => registry.call('F2', { ...args, cluster_root: 'unknown' }), /CLUSTER_NOT_FOUND/);
  assert.throws(() => registry.call('F1', { ...args, cluster_root: 'smṛti' }), /CLUSTER_SELECTOR_NOT_SUPPORTED/);
}));
test('registration pins real bytes, refuses overwrite and leaves mother originals intact', () => withFixture(({ entry, root }) => {
  const output = path.join(root, 'catalogue.json');
  const args = { id: 'test', snapshotPath: entry.snapshot.filepath, s4Path: entry.S4.filepath, s35Path: entry.S3_5.filepath, output };
  assert.equal(register(args).source_mutations, 0);
  assert.throws(() => register(args), /EEXIST/);
  assert.equal(hash(fs.readFileSync(entry.S4.filepath)), entry.S4.sha256);
  fs.appendFileSync(entry.S3_5.filepath, ' ');
  assert.throws(() => register({ ...args, output: path.join(root, 'different.json') }), /UPSTREAM_LINEAGE_MISMATCH/);
  assert.equal(fs.existsSync(path.join(root, 'different.json')), false);
}));
test('source profiles remain immutable across calls', () => withFixture(({ data }) => {
  const profile = compute('F4', data)[0].profile;
  assert.throws(() => { profile.title = 'changed'; }, TypeError);
  assert.notEqual(compute('F4', data)[0].profile.title, 'changed');
}));
test('shared particle membership is counted distinctly and conflicting layers are rejected', () => withFixture(({ data }) => {
  const c = structuredClone(data); const before = compute('F3', c, 0.5);
  c.clusters[1].particles.push({ ...c.clusters[0].particles[0] });
  const after = compute('F3', c, 0.5);
  assert.equal(after.particle_count, before.particle_count); assert.equal(after.membership_count, before.membership_count + 1);
  c.clusters[1].particles.at(-1).layer = 'LN'; assert.throws(() => checkSnapshot(c), /PARTICLE_LAYER_CONFLICT/);
}));
test('MCP transport forwards exact names/arguments and rejects an incorrect result digest', async () => {
  const f = fixture(); const original = global.fetch;
  const env = { MRL_PANINI_READ_API_KEY: 'test-key', MRL_BRIDGE_BASE_URL: 'https://bridge.example.test' };
  let tamper = false;
  global.fetch = async (url, options) => {
    assert.equal(url.href, 'https://bridge.example.test' + PREFIX + '/F1');
    assert.equal(options.headers['x-api-key'], 'test-key'); assert.equal(options.redirect, 'error');
    assert.deepEqual(JSON.parse(options.body), f.args);
    const result = f.registry.call('F1', f.args); if (tamper) result.result_sha256 = '0'.repeat(64);
    return new Response(JSON.stringify(result), { status: 200 });
  };
  try {
    assert.deepEqual(await invoke(names.F1, f.args, env), f.registry.call('F1', f.args));
    tamper = true; await assert.rejects(invoke(names.F1, f.args, env), /BRIDGE_IDENTITY_MISMATCH/);
  } finally { global.fetch = original; f.cleanup(); }
});
test('HTTP adapter fails closed without configuration and rejects reuse of admin key', async () => {
  const previous = process.env.MRL_BRIDGE_API_KEY; process.env.MRL_BRIDGE_API_KEY = 'test-admin';
  const app = express(); app.use(express.json()); install(app, { readKey: 'test-admin', registry: new DatasetRegistry() });
  const server = app.listen(0, '127.0.0.1'); await new Promise(r => server.once('listening', r));
  try {
    const r = await fetch('http://127.0.0.1:' + server.address().port + PREFIX + '/tools', { headers: { 'x-api-key': 'test-admin' } });
    assert.equal(r.status, 503); await r.text();
  } finally {
    await new Promise(r => server.close(r));
    if (previous === undefined) delete process.env.MRL_BRIDGE_API_KEY; else process.env.MRL_BRIDGE_API_KEY = previous;
  }
});
test('actual HTTP transport enforces read capability, dataset pins, media type and parent audit', async () => {
  const f = fixture(); const app = express(); const center = new TranslationCenter();
  app.use(center.middleware()); app.use(express.json()); app.use(center.admission());
  install(app, { readKey: 'test-read-only', registry: f.registry });
  const server = http.createServer(app); await new Promise(r => server.listen(0, '127.0.0.1', r));
  const url = 'http://127.0.0.1:' + server.address().port + PREFIX;
  try {
    for (const [key, status] of [[null, 401], ['test-admin-only', 403], ['test-read-only', 200]]) {
      const headers = { 'Content-Type': 'application/json' }; if (key) headers['x-api-key'] = key;
      const res = await fetch(url + '/F1', { method: 'POST', headers, body: JSON.stringify(f.args) });
      assert.equal(res.status, status); const body = await res.json();
      assert.equal(res.headers.get('x-mrl-affiliation'), 'MRL');
      if (status === 200) assert.equal(body.result[0].activity, 12);
    }
    const headers = { 'x-api-key': 'test-read-only', 'Content-Type': 'application/json' };
    for (const id of Object.keys(names)) {
      const res = await fetch(url + '/' + id, { method: 'POST', headers,
        body: JSON.stringify({ ...f.args, avg_cluster_size_ratio: id === 'F3' ? 0.5 : null }) });
      assert.equal(res.status, 200); assert.equal((await res.json()).function.id, id);
    }
    const invalid = await fetch(url + '/F3', { method: 'POST', headers, body: JSON.stringify(f.args) });
    assert.equal(invalid.status, 422); assert.equal((await invalid.json()).error, 'F3_RATIO_DEFINITION_REQUIRED');
    const media = await fetch(url + '/F1', { method: 'POST', headers: { 'x-api-key': 'test-read-only', 'Content-Type': 'text/plain' }, body: '{}' });
    assert.equal(media.status, 415); await media.text();
    const records = JSON.stringify(center.recent); assert.equal(records.includes('test-read-only'), false);
    assert.ok(center.recent.some(r => r.direction === 'mrl_to_external'));
  } finally { await new Promise(r => server.close(r)); f.cleanup(); }
});
test('MCP lists six tools, forwards to Bridge, returns error semantics and ignores notifications', async () => {
  const req = (method, params) => ({ jsonrpc: '2.0', id: 1, method, params });
  assert.equal((await handle(req('tools/list'))).result.tools.length, 6);
  assert.equal(await handle({ jsonrpc: '2.0', method: 'notifications/initialized' }), null);
  assert.equal((await handle(req('tools/call', { name: names.F1, arguments: {} }), async () => { throw new Error('BRIDGE_HTTP_503'); })).result.isError, true);
  const result = await handle(req('tools/call', { name: names.F1, arguments: { dataset_id: 'mother' } }), async (name, args) => ({ name, args }));
  assert.equal(JSON.parse(result.result.content[0].text).args.dataset_id, 'mother');
  const args = { dataset_id: 'mother', expected_schema_version: 'panini_cluster_insight/v1.0.0', cluster_root: null, avg_cluster_size_ratio: null };
  await assert.rejects(invoke(names.F1, args, {}), /READ_KEY_NOT_BOUND/);
  await assert.rejects(invoke(names.F1, args, { MRL_PANINI_READ_API_KEY: 'test', MRL_BRIDGE_BASE_URL: 'http://evil.example' }), /HTTPS_BRIDGE_ORIGIN_REQUIRED/);
});
test('MCP process emits only JSON-RPC on stdout and requires bound capability for calls', () => {
  const env = { ...process.env }; delete env.MRL_PANINI_READ_API_KEY;
  const r = spawnSync(process.execPath, [path.join(__dirname, 'mcp_stdio.cjs')], { env, encoding: 'utf8',
    input: [{ jsonrpc: '2.0', id: 1, method: 'initialize' }, { jsonrpc: '2.0', id: 2, method: 'tools/list' },
      { jsonrpc: '2.0', id: 3, method: 'tools/call', params: { name: names.F1, arguments: {} } }].map(JSON.stringify).join('\n') + '\n' });
  assert.equal(r.status, 0); const lines = r.stdout.trim().split('\n').map(JSON.parse);
  assert.equal(lines.length, 3); assert.equal(lines[2].result.isError, true); assert.equal(r.stderr, '');
});
