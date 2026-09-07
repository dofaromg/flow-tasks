// mrl-firecore-trace — Analytics counterpart (edge event collection).
// origin_signature: MrLiouWord
//
// Real edge behavior: event collection (single or batch), session lifecycle,
// and windowed roll-up computation — all in D1. Analytics collection is
// legitimately edge-authoritative; /flush computes a real count roll-up and
// returns a DL580 hand-off for warehouse consolidation.

import {
  Router,
  type FireCoreBaseEnv,
  ok,
  fail,
  readJson,
  requireString,
  optionalString,
  uuid,
  nowSec,
  hasD1,
  dl580Handoff,
} from '../../../shared/firecore_runtime';

export interface Env extends FireCoreBaseEnv {
  MRL_FC_TRACE_DB?: D1Database;
}

class EdgeUnbound extends Error {}
function db(env: Env): D1Database {
  if (!hasD1(env.MRL_FC_TRACE_DB)) throw new EdgeUnbound();
  return env.MRL_FC_TRACE_DB;
}

const router = new Router<Env>('mrl-firecore-trace', 'Analytics', [
  '/health', '/v1/trace/events', '/v1/trace/session', '/v1/trace/flush',
]);

// collect one event or a batch
router.post('/v1/trace/events', async ({ req, env }) => {
  const body = await readJson(req);
  const incoming = Array.isArray(body.events) ? body.events : [body];
  if (incoming.length === 0 || incoming.length > 500) return fail('invalid_batch_size', 400, { max: 500 });
  const ts = nowSec();
  const ids: string[] = [];
  for (const raw of incoming) {
    const ev = (raw && typeof raw === 'object' ? raw : {}) as Record<string, unknown>;
    const event_name = requireString(ev, 'event_name', { max: 160 });
    const session_id = optionalString(ev, 'session_id');
    const client_ts = Number.isFinite(Number(ev.client_ts)) ? Number(ev.client_ts) : null;
    const event_id = uuid();
    await db(env).prepare(`INSERT INTO mrl_fc_trace_events (event_id, session_id, event_name, payload_json, client_ts, origin_signature, created_at) VALUES (?, ?, ?, ?, ?, 'MrLiouWord', ?)`).bind(event_id, session_id, event_name, JSON.stringify(ev.data ?? {}), client_ts, ts).run();
    ids.push(event_id);
  }
  return ok({ accepted: ids.length, event_ids: ids }, 201);
});

// start or end a session
router.post('/v1/trace/session', async ({ req, env }) => {
  const body = await readJson(req);
  const action = optionalString(body, 'action') ?? 'start';
  const ts = nowSec();
  if (action === 'start') {
    const session_id = uuid();
    const uid = optionalString(body, 'uid');
    await db(env).prepare(`INSERT INTO mrl_fc_trace_sessions (session_id, uid, started_at, ended_at, origin_signature) VALUES (?, ?, ?, NULL, 'MrLiouWord')`).bind(session_id, uid, ts).run();
    return ok({ session_id, started_at: ts }, 201);
  }
  if (action === 'end') {
    const session_id = requireString(body, 'session_id');
    const res = await db(env).prepare('UPDATE mrl_fc_trace_sessions SET ended_at = ? WHERE session_id = ? AND ended_at IS NULL').bind(ts, session_id).run();
    if (!res.meta.changes) return fail('session_not_found_or_ended', 404, { session_id });
    return ok({ session_id, ended_at: ts });
  }
  return fail('invalid_action', 400, { allowed: ['start', 'end'] });
});

// compute a windowed count roll-up (real aggregation)
router.post('/v1/trace/flush', async ({ req, env }) => {
  const body = await readJson(req);
  const window_start = Number.isFinite(Number(body.window_start)) ? Number(body.window_start) : 0;
  const window_end = Number.isFinite(Number(body.window_end)) ? Number(body.window_end) : nowSec();
  const metric_name = optionalString(body, 'metric_name') ?? 'events_total';
  const row = await db(env).prepare('SELECT COUNT(*) AS c FROM mrl_fc_trace_events WHERE created_at >= ? AND created_at <= ?').bind(window_start, window_end).first<{ c: number }>();
  const metric_value = row?.c ?? 0;
  const rollup_id = uuid();
  await db(env).prepare(`INSERT INTO mrl_fc_trace_rollups (rollup_id, window_start, window_end, metric_name, metric_value, origin_signature, created_at) VALUES (?, ?, ?, ?, ?, 'MrLiouWord', ?)`).bind(rollup_id, window_start, window_end, metric_name, metric_value, nowSec()).run();
  const consolidate = await dl580Handoff('trace.consolidate_rollup', { rollup_id, metric_name });
  return ok({ rollup_id, metric_name, metric_value, window_start, window_end, consolidate }, 201);
});

export default {
  async fetch(req: Request, env: Env): Promise<Response> {
    try {
      return await router.handle(req, env);
    } catch (err) {
      if (err instanceof EdgeUnbound) return fail('edge_store_unbound', 503, { hint: 'bind MRL_FC_TRACE_DB (D1 mrliouword-db)' });
      return fail('internal_error', 500);
    }
  },
};
