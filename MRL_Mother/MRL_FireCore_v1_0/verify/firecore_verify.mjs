// MRL FireCore — reproducible behavior verification.
// origin_signature: MrLiouWord
//
// Runs each edge module in Node against a REAL SQLite database (node:sqlite)
// loaded with that module's actual migration SQL, exercising the real HTTP
// surface. Proves behavior, not string constants. Invoked by run.sh, which
// compiles the TypeScript with the local tsc first.
//
//   node firecore_verify.mjs <compiled_modules_dir> <package_root>

import { DatabaseSync } from 'node:sqlite';
import { readFileSync } from 'node:fs';
import { createRequire } from 'node:module';

const require = createRequire(import.meta.url);
const DIST = process.argv[2];
const ROOT = process.argv[3];

function env(binding, module) {
  const sqlite = new DatabaseSync(':memory:');
  sqlite.exec(readFileSync(`${ROOT}/modules/${module}/migrations/0001_${module.replace(/-/g, '_')}.sql`, 'utf8'));
  const D1 = {
    prepare(sql) {
      const s = sqlite.prepare(sql);
      let p = [];
      return {
        bind(...a) { p = a; return this; },
        async first() { return s.get(...p) ?? null; },
        async run() { const i = s.run(...p); return { success: true, meta: { changes: i.changes, last_row_id: i.lastInsertRowid } }; },
        async all() { return { results: s.all(...p), success: true, meta: {} }; },
      };
    },
  };
  return { env: { [binding]: D1, MRL_FIRECORE_MODE: 'verify' }, sqlite };
}
const worker = (m) => require(`${DIST}/${m}/src/index.js`).default;
const req = (m, p, b) => new Request('https://edge.mrliou' + p, { method: m, headers: { 'content-type': 'application/json', 'cf-connecting-ip': '203.0.113.9', 'user-agent': 'verify' }, body: b !== undefined ? JSON.stringify(b) : undefined });

let PASS = 0, FAIL = 0;
const c = (n, cond, d) => { if (cond) { PASS++; console.log('  ✅', n); } else { FAIL++; console.log('  ❌', n, d ?? ''); } };

async function auth() {
  console.log('== mrl-firecore-auth ==');
  const w = worker('mrl-firecore-auth');
  const { env: e, sqlite } = env('MRL_FC_AUTH_DB', 'mrl-firecore-auth');
  const call = (m, p, b) => w.fetch(req(m, p, b), e);
  let r = await call('GET', '/health'); let j = await r.json();
  c('health 200 + endpoints', r.status === 200 && Array.isArray(j.endpoints));
  r = await call('POST', '/v1/auth/signup', { email: 'Root@MrLiou.example', password: 'correcthorse8' }); j = await r.json();
  c('signup 201 + uid', r.status === 201 && !!j.uid); c('signup defers canonical to DL580', j.canonical_sync?.authority === 'DL580');
  const uid = j.uid;
  r = await call('POST', '/v1/auth/signup', { email: 'root@mrliou.example', password: 'correcthorse8' }); c('duplicate email 409', r.status === 409);
  r = await call('POST', '/v1/auth/signup', { email: 'a@b.example', password: 'short' }); c('weak password 400', r.status === 400);
  r = await call('POST', '/v1/auth/signup', { email: 'bad', password: 'correcthorse8' }); c('bad email 400', r.status === 400);
  r = await call('POST', '/v1/auth/signin', { email: 'root@mrliou.example', password: 'WRONGpass9' }); c('wrong password 401', r.status === 401);
  r = await call('POST', '/v1/auth/signin', { email: 'root@mrliou.example', password: 'correcthorse8' }); j = await r.json();
  c('signin 200 + refresh_token', r.status === 200 && typeof j.refresh_token === 'string'); c('access token -> DL580', j.access_token?.authority === 'DL580');
  const refresh1 = j.refresh_token;
  r = await call('POST', '/signin', { email: 'root@mrliou.example', password: 'correcthorse8' }); c('legacy /signin alias 200', r.status === 200);
  r = await call('POST', '/v1/auth/refresh', { refresh_token: refresh1 }); j = await r.json();
  c('refresh rotates', r.status === 200 && j.refresh_token !== refresh1); const refresh2 = j.refresh_token;
  r = await call('POST', '/v1/auth/refresh', { refresh_token: refresh1 }); c('rotated-out token 401', r.status === 401);
  r = await call('POST', '/v1/auth/refresh', { refresh_token: refresh2 }); c('rotated-in token 200', r.status === 200);
  r = await call('POST', '/v1/auth/verify', { uid }); c('verify email 200', r.status === 200);
  r = await call('GET', '/v1/auth/nope'); c('unknown route 404', r.status === 404);
  c('audit trail written', sqlite.prepare('SELECT COUNT(*) c FROM mrl_fc_auth_audit').get().c >= 5);
  c('password stored as PBKDF2', /^[0-9a-f]{32}\$120000\$[0-9a-f]{64}$/.test(sqlite.prepare('SELECT password_hash FROM mrl_fc_users WHERE uid=?').get(uid).password_hash));
}
async function store() {
  console.log('== mrl-firecore-store ==');
  const w = worker('mrl-firecore-store'); const { env: e, sqlite } = env('MRL_FC_STORE_DB', 'mrl-firecore-store'); const call = (m, p, b) => w.fetch(req(m, p, b), e);
  let r = await call('POST', '/v1/store/documents', { collection: 'users', id: 'u1', data: { name: 'Liou' } }); let j = await r.json();
  c('create 201 v1', r.status === 201 && j.document.version === 1); c('create -> DL580', j.authority_sync?.authority === 'DL580');
  r = await call('POST', '/v1/store/documents', { collection: 'users', id: 'u1', data: {} }); c('dup 409', r.status === 409);
  r = await call('GET', '/v1/store/documents/users/u1'); j = await r.json(); c('read 200', r.status === 200 && j.document.data.name === 'Liou');
  r = await call('PUT', '/v1/store/documents/users/u1', { data: { name: 'MrLiou' } }); j = await r.json(); c('update -> v2', j.document.version === 2);
  c('version history (2)', sqlite.prepare('SELECT COUNT(*) c FROM mrl_fc_document_versions').get().c === 2);
  r = await call('POST', '/v1/store/query', { collection: 'users' }); j = await r.json(); c('query 1 doc', j.count === 1);
  r = await call('DELETE', '/v1/store/documents/users/u1'); c('soft delete 200', r.status === 200);
  r = await call('GET', '/v1/store/documents/users/u1'); c('deleted read 404', r.status === 404);
  c('row preserved (soft)', sqlite.prepare('SELECT deleted FROM mrl_fc_documents WHERE document_path=?').get('users/u1').deleted === 1);
}
async function vault() {
  console.log('== mrl-firecore-vault ==');
  const w = worker('mrl-firecore-vault'); const { env: e } = env('MRL_FC_VAULT_DB', 'mrl-firecore-vault'); const call = (m, p, b) => w.fetch(req(m, p, b), e); const sha = 'a'.repeat(64);
  let r = await call('POST', '/v1/vault/objects', { object_key: 'docs/a.pdf', sha256: sha, byte_size: 12, content_type: 'application/pdf' }); let j = await r.json();
  c('register 201 edge_pending', r.status === 201 && j.object.r2_state === 'edge_pending'); c('custody -> DL580', j.custody?.authority === 'DL580'); const oid = j.object.object_id;
  r = await call('POST', '/v1/vault/objects', { object_key: 'docs/a.pdf', sha256: sha }); c('dup key 409', r.status === 409);
  r = await call('POST', '/v1/vault/objects', { object_key: 'x', sha256: 'short' }); c('bad sha 400', r.status === 400);
  r = await call('GET', '/v1/vault/objects/' + oid); c('get meta 200', r.status === 200);
  r = await call('POST', '/v1/vault/signed-url', { object_key: 'docs/a.pdf' }); j = await r.json(); c('signed-url -> DL580', j.signed_url?.authority === 'DL580');
  r = await call('DELETE', '/v1/vault/objects/' + oid); j = await r.json(); c('delete -> delete_pending', j.r2_state === 'delete_pending');
}
async function live() {
  console.log('== mrl-firecore-live ==');
  const w = worker('mrl-firecore-live'); const { env: e } = env('MRL_FC_LIVE_DB', 'mrl-firecore-live'); const call = (m, p, b) => w.fetch(req(m, p, b), e);
  let r = await call('POST', '/v1/live/topics/room.42', { event_type: 'join', data: { u: 'liou' } }); let j = await r.json(); c('publish seq=1', j.sequence_no === 1);
  r = await call('POST', '/v1/live/topics/room.42', { event_type: 'msg', data: { t: 'hi' } }); j = await r.json(); c('publish seq=2 ordered', j.sequence_no === 2);
  r = await call('GET', '/v1/live/stream?topic=room.42&since=1'); j = await r.json(); c('stream since=1 -> 1 ev cursor=2', j.events.length === 1 && j.cursor === 2);
  r = await call('GET', '/v1/live/topics/room.42'); j = await r.json(); c('topic newest-first', j.events[0].sequence_no === 2);
  r = await call('GET', '/v1/live/ws'); j = await r.json(); c('ws 426 + DO/DL580 bridge', r.status === 426 && j.bridge?.authority === 'DL580');
}
async function push() {
  console.log('== mrl-firecore-push ==');
  const w = worker('mrl-firecore-push'); const { env: e, sqlite } = env('MRL_FC_PUSH_DB', 'mrl-firecore-push'); const call = (m, p, b) => w.fetch(req(m, p, b), e);
  let r = await call('POST', '/v1/push/register', { token: 'devicetoken123', platform: 'ios', uid: 'u1' }); let j = await r.json(); c('register 201', r.status === 201 && !!j.device_id);
  r = await call('POST', '/v1/push/register', { token: 'devicetoken123', platform: 'ios' }); j = await r.json(); c('re-register idempotent', j.reused === true);
  c('token hashed (64 hex)', /^[0-9a-f]{64}$/.test(sqlite.prepare('SELECT token_hash FROM mrl_fc_push_devices').get().token_hash));
  r = await call('POST', '/v1/push/register', { token: 'x123456789', platform: 'nokia' }); c('bad platform 400', r.status === 400);
  r = await call('POST', '/v1/push/topics', { topic_name: 'news' }); c('create topic 201', r.status === 201);
  r = await call('GET', '/v1/push/topics'); j = await r.json(); c('list topics', j.count === 1);
  r = await call('POST', '/v1/push/send', { topic_name: 'news', data: { title: 'hi' } }); j = await r.json(); c('send 202 + DL580 dispatch', r.status === 202 && j.dispatch?.authority === 'DL580');
  r = await call('POST', '/v1/push/send', { data: {} }); c('send no target 400', r.status === 400);
}
async function trace() {
  console.log('== mrl-firecore-trace ==');
  const w = worker('mrl-firecore-trace'); const { env: e, sqlite } = env('MRL_FC_TRACE_DB', 'mrl-firecore-trace'); const call = (m, p, b) => w.fetch(req(m, p, b), e);
  let r = await call('POST', '/v1/trace/session', { uid: 'u1' }); let j = await r.json(); c('session start 201', r.status === 201 && !!j.session_id); const sid = j.session_id;
  r = await call('POST', '/v1/trace/events', { event_name: 'page_view', session_id: sid, data: { p: '/' } }); j = await r.json(); c('single event 201', j.accepted === 1);
  r = await call('POST', '/v1/trace/events', { events: [{ event_name: 'click' }, { event_name: 'scroll' }, { event_name: 'click' }] }); j = await r.json(); c('batch of 3', j.accepted === 3);
  r = await call('POST', '/v1/trace/events', { data: {} }); c('missing event_name 400', r.status === 400);
  r = await call('POST', '/v1/trace/flush', { window_start: 0 }); j = await r.json(); c('flush counts 4', j.metric_value === 4);
  c('rollup row written', sqlite.prepare('SELECT COUNT(*) c FROM mrl_fc_trace_rollups').get().c === 1);
  r = await call('POST', '/v1/trace/session', { action: 'end', session_id: sid }); c('session end 200', r.status === 200);
}

await auth(); await store(); await vault(); await live(); await push(); await trace();
console.log(`\n===== FireCore TOTAL: ${PASS} passed, ${FAIL} failed =====`);
process.exit(FAIL ? 1 : 0);
