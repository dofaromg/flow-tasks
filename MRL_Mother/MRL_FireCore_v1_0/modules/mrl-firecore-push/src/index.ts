// mrl-firecore-push — Cloud Messaging / FCM counterpart (edge dispatch queue).
// origin_signature: MrLiouWord
//
// Real edge behavior: device registration (token hashed, never stored raw),
// topic registry, and notification job enqueue in D1. Actual delivery
// (APNs/WebPush credentials + send policy) is authoritative and signed by
// DL580 — /send enqueues a job and returns a typed dispatch hand-off.

import {
  Router,
  type FireCoreBaseEnv,
  ok,
  fail,
  readJson,
  requireString,
  optionalString,
  sha256Hex,
  uuid,
  nowSec,
  hasD1,
  dl580Handoff,
} from '../../../shared/firecore_runtime';

export interface Env extends FireCoreBaseEnv {
  MRL_FC_PUSH_DB?: D1Database;
}

class EdgeUnbound extends Error {}
function db(env: Env): D1Database {
  if (!hasD1(env.MRL_FC_PUSH_DB)) throw new EdgeUnbound();
  return env.MRL_FC_PUSH_DB;
}

const PLATFORMS = new Set(['ios', 'android', 'web']);

const router = new Router<Env>('mrl-firecore-push', 'Cloud Messaging / FCM', [
  '/health', '/v1/push/register', '/v1/push/send', '/v1/push/topics',
]);

// register a device (idempotent on token_hash)
router.post('/v1/push/register', async ({ req, env }) => {
  const body = await readJson(req);
  const token = requireString(body, 'token', { min: 8, max: 4096 });
  const platform = requireString(body, 'platform').toLowerCase();
  if (!PLATFORMS.has(platform)) return fail('invalid_platform', 400, { allowed: [...PLATFORMS] });
  const uid = optionalString(body, 'uid');
  const token_hash = await sha256Hex(token);
  const ts = nowSec();

  const existing = await db(env).prepare('SELECT device_id FROM mrl_fc_push_devices WHERE token_hash = ?').bind(token_hash).first<{ device_id: string }>();
  if (existing) {
    await db(env).prepare('UPDATE mrl_fc_push_devices SET uid = ?, platform = ?, enabled = 1, updated_at = ? WHERE device_id = ?').bind(uid, platform, ts, existing.device_id).run();
    return ok({ device_id: existing.device_id, platform, reused: true });
  }
  const device_id = uuid();
  await db(env).prepare(`INSERT INTO mrl_fc_push_devices (device_id, uid, platform, token_hash, enabled, origin_signature, created_at, updated_at) VALUES (?, ?, ?, ?, 1, 'MrLiouWord', ?, ?)`).bind(device_id, uid, platform, token_hash, ts, ts).run();
  return ok({ device_id, platform, reused: false }, 201);
});

// enqueue a send job; delivery authority is DL580
router.post('/v1/push/send', async ({ req, env }) => {
  const body = await readJson(req);
  const topic_name = optionalString(body, 'topic_name');
  const device_id = optionalString(body, 'device_id');
  if (!topic_name && !device_id) return fail('missing_target:topic_name_or_device_id', 400);
  const data = body.data ?? {};
  const ts = nowSec();
  const job_id = uuid();
  await db(env).prepare(`INSERT INTO mrl_fc_push_jobs (job_id, topic_name, device_id, payload_json, state, origin_signature, created_at, sent_at) VALUES (?, ?, ?, ?, 'queued', 'MrLiouWord', ?, NULL)`).bind(job_id, topic_name, device_id, JSON.stringify(data), ts).run();
  const dispatch = await dl580Handoff('push.dispatch_job', { job_id, topic_name, device_id });
  return ok({ job_id, state: 'queued', dispatch }, 202);
});

// list or create topics
router.get('/v1/push/topics', async ({ env }) => {
  const rows = await db(env).prepare('SELECT topic_name, created_at FROM mrl_fc_push_topics ORDER BY created_at DESC LIMIT 200').all<{ topic_name: string; created_at: number }>();
  return ok({ count: rows.results.length, topics: rows.results });
});
router.post('/v1/push/topics', async ({ req, env }) => {
  const body = await readJson(req);
  const topic_name = requireString(body, 'topic_name', { max: 200 });
  const exists = await db(env).prepare('SELECT topic_id FROM mrl_fc_push_topics WHERE topic_name = ?').bind(topic_name).first();
  if (exists) return fail('topic_exists', 409, { topic_name });
  await db(env).prepare(`INSERT INTO mrl_fc_push_topics (topic_id, topic_name, origin_signature, created_at) VALUES (?, ?, 'MrLiouWord', ?)`).bind(uuid(), topic_name, nowSec()).run();
  return ok({ topic_name }, 201);
});

export default {
  async fetch(req: Request, env: Env): Promise<Response> {
    try {
      return await router.handle(req, env);
    } catch (err) {
      if (err instanceof EdgeUnbound) return fail('edge_store_unbound', 503, { hint: 'bind MRL_FC_PUSH_DB (D1 mrliouword-db)' });
      return fail('internal_error', 500);
    }
  },
};
