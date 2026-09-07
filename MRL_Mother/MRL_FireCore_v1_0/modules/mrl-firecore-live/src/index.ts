// mrl-firecore-live — Firestore Listeners counterpart (edge realtime bridge).
// origin_signature: MrLiouWord
//
// Real edge behavior: topic registry, ordered event log (per-topic sequence)
// in D1, and a poll-based subscription over /stream. True WebSocket fan-out
// needs Durable Objects + DL580 PostgreSQL LISTEN/NOTIFY; /ws returns a typed
// upgrade hand-off rather than pretending to hold a socket at the plain edge.

import {
  Router,
  type FireCoreBaseEnv,
  ok,
  fail,
  readJson,
  requireString,
  uuid,
  nowSec,
  hasD1,
  dl580Handoff,
} from '../../../shared/firecore_runtime';

export interface Env extends FireCoreBaseEnv {
  MRL_FC_LIVE_DB?: D1Database;
}

class EdgeUnbound extends Error {}
function db(env: Env): D1Database {
  if (!hasD1(env.MRL_FC_LIVE_DB)) throw new EdgeUnbound();
  return env.MRL_FC_LIVE_DB;
}

async function ensureTopic(env: Env, topic_path: string): Promise<string> {
  const existing = await db(env).prepare('SELECT topic_id FROM mrl_fc_live_topics WHERE topic_path = ?').bind(topic_path).first<{ topic_id: string }>();
  if (existing) return existing.topic_id;
  const topic_id = uuid();
  const ts = nowSec();
  await db(env).prepare(`INSERT INTO mrl_fc_live_topics (topic_id, topic_path, source_kind, origin_signature, created_at, updated_at) VALUES (?, ?, 'dl580_pg_notify', 'MrLiouWord', ?, ?)`).bind(topic_id, topic_path, ts, ts).run();
  return topic_id;
}

const router = new Router<Env>('mrl-firecore-live', 'Firestore Listeners', [
  '/health', '/v1/live/stream', '/v1/live/ws', '/v1/live/topics/:topic',
]);

// publish an event to a topic (ordered)
router.post('/v1/live/topics/:topic', async ({ req, env, params }) => {
  const body = await readJson(req);
  const event_type = requireString(body, 'event_type', { max: 120 });
  const data = body.data ?? {};
  const topic_path = params.topic;
  const topic_id = await ensureTopic(env, topic_path);
  const ts = nowSec();
  const seqRow = await db(env).prepare('SELECT COALESCE(MAX(sequence_no), 0) AS max_seq FROM mrl_fc_live_events WHERE topic_id = ?').bind(topic_id).first<{ max_seq: number }>();
  const sequence_no = (seqRow?.max_seq ?? 0) + 1;
  const event_id = uuid();
  await db(env).prepare(`INSERT INTO mrl_fc_live_events (event_id, topic_id, event_type, payload_json, sequence_no, origin_signature, created_at) VALUES (?, ?, ?, ?, ?, 'MrLiouWord', ?)`).bind(event_id, topic_id, event_type, JSON.stringify(data), sequence_no, ts).run();
  const fanout = await dl580Handoff('live.fanout_event', { topic_path, sequence_no });
  return ok({ event_id, topic: topic_path, sequence_no, event_type, authority_fanout: fanout }, 201);
});

// read recent events for a topic
router.get('/v1/live/topics/:topic', async ({ env, params }) => {
  const topic = await db(env).prepare('SELECT topic_id, topic_path, source_kind FROM mrl_fc_live_topics WHERE topic_path = ?').bind(params.topic).first<{ topic_id: string; topic_path: string; source_kind: string }>();
  if (!topic) return fail('topic_not_found', 404, { topic: params.topic });
  const events = await db(env).prepare('SELECT event_id, event_type, payload_json, sequence_no, created_at FROM mrl_fc_live_events WHERE topic_id = ? ORDER BY sequence_no DESC LIMIT 50').bind(topic.topic_id).all<{ event_id: string; event_type: string; payload_json: string; sequence_no: number; created_at: number }>();
  return ok({
    topic: topic.topic_path,
    source_kind: topic.source_kind,
    events: events.results.map((e) => ({ event_id: e.event_id, event_type: e.event_type, sequence_no: e.sequence_no, data: JSON.parse(e.payload_json), created_at: e.created_at })),
  });
});

// poll-based subscription: events after ?since= (real, transport=poll)
router.get('/v1/live/stream', async ({ env, url }) => {
  const topic_path = url.searchParams.get('topic');
  if (!topic_path) return fail('missing_query:topic', 400);
  const since = Number(url.searchParams.get('since') ?? '0') || 0;
  const topic = await db(env).prepare('SELECT topic_id FROM mrl_fc_live_topics WHERE topic_path = ?').bind(topic_path).first<{ topic_id: string }>();
  if (!topic) return fail('topic_not_found', 404, { topic: topic_path });
  const events = await db(env).prepare('SELECT event_id, event_type, payload_json, sequence_no, created_at FROM mrl_fc_live_events WHERE topic_id = ? AND sequence_no > ? ORDER BY sequence_no ASC LIMIT 100').bind(topic.topic_id, since).all<{ event_id: string; event_type: string; payload_json: string; sequence_no: number; created_at: number }>();
  const results = events.results.map((e) => ({ event_id: e.event_id, event_type: e.event_type, sequence_no: e.sequence_no, data: JSON.parse(e.payload_json), created_at: e.created_at }));
  const cursor = results.length ? results[results.length - 1].sequence_no : since;
  return ok({ topic: topic_path, transport: 'poll', since, cursor, events: results });
});

// WebSocket upgrade is a Durable Object + DL580 concern
router.get('/v1/live/ws', async ({ req }) => {
  const handoff = await dl580Handoff('live.ws_upgrade', { upgrade: req.headers.get('upgrade') ?? null });
  return fail('websocket_requires_durable_object_bridge', 426, { transport: 'websocket', bridge: handoff });
});

export default {
  async fetch(req: Request, env: Env): Promise<Response> {
    try {
      return await router.handle(req, env);
    } catch (err) {
      if (err instanceof EdgeUnbound) return fail('edge_store_unbound', 503, { hint: 'bind MRL_FC_LIVE_DB (D1 mrliouword-db)' });
      return fail('internal_error', 500);
    }
  },
};
