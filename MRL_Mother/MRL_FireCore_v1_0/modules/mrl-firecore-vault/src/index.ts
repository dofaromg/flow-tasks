// mrl-firecore-vault — Firebase Storage counterpart (edge object registry).
// origin_signature: MrLiouWord
//
// Real edge behavior: object metadata registry in D1, transfer bookkeeping
// (edge R2 <-> DL580 NAS), and audit. Signed download URLs are authoritative
// and minted by DL580 — the edge returns a typed signing hand-off, never a
// forged URL. Object bytes live in R2 at the edge; DL580 NAS holds custody.

import {
  Router,
  type FireCoreBaseEnv,
  ok,
  fail,
  readJson,
  requireString,
  uuid,
  nowSec,
  audit,
  hasD1,
  dl580Handoff,
} from '../../../shared/firecore_runtime';

export interface Env extends FireCoreBaseEnv {
  MRL_FC_VAULT_DB?: D1Database;
}

class EdgeUnbound extends Error {}
function db(env: Env): D1Database {
  if (!hasD1(env.MRL_FC_VAULT_DB)) throw new EdgeUnbound();
  return env.MRL_FC_VAULT_DB;
}

interface ObjRow {
  object_id: string; object_key: string; content_type: string | null;
  byte_size: number; sha256: string; dl580_path: string; r2_state: string; updated_at: number;
}
const present = (r: ObjRow) => ({
  object_id: r.object_id, object_key: r.object_key, content_type: r.content_type,
  byte_size: r.byte_size, sha256: r.sha256, dl580_path: r.dl580_path, r2_state: r.r2_state, updated_at: r.updated_at,
});

const router = new Router<Env>('mrl-firecore-vault', 'Firebase Storage', [
  '/health', '/v1/vault/objects', '/v1/vault/objects/:object_id', '/v1/vault/signed-url',
]);

// register object + open an edge->DL580 transfer
router.post('/v1/vault/objects', async ({ req, env }) => {
  const body = await readJson(req);
  const object_key = requireString(body, 'object_key', { max: 512 });
  const sha256 = requireString(body, 'sha256', { min: 64, max: 64 });
  const content_type = typeof body.content_type === 'string' ? body.content_type : null;
  const byte_size = Number.isFinite(Number(body.byte_size)) ? Number(body.byte_size) : 0;
  const dl580_path = `nas://mrl-firecore-vault/${object_key}`;
  const ts = nowSec();

  const exists = await db(env).prepare('SELECT object_id FROM mrl_fc_vault_objects WHERE object_key = ?').bind(object_key).first();
  if (exists) return fail('object_key_exists', 409, { object_key });

  const object_id = uuid();
  await db(env)
    .prepare(
      `INSERT INTO mrl_fc_vault_objects
       (object_id, bucket_name, object_key, content_type, byte_size, sha256, dl580_path, r2_state, origin_signature, created_at, updated_at)
       VALUES (?, 'mrl-firecore-vault', ?, ?, ?, ?, ?, 'edge_pending', 'MrLiouWord', ?, ?)`,
    )
    .bind(object_id, object_key, content_type, byte_size, sha256, dl580_path, ts, ts)
    .run();
  await db(env)
    .prepare(`INSERT INTO mrl_fc_vault_transfers (transfer_id, object_id, direction, state, retry_count, origin_signature, created_at) VALUES (?, ?, 'edge_to_dl580', 'queued', 0, 'MrLiouWord', ?)`)
    .bind(uuid(), object_id, ts)
    .run();
  await audit(env.MRL_FC_VAULT_DB, 'mrl_fc_vault_audit', { audit_id: uuid(), object_key, action: 'register', origin_signature: 'MrLiouWord', created_at: ts });

  const custody = await dl580Handoff('vault.commit_custody', { object_key, sha256 });
  const row = await db(env).prepare('SELECT * FROM mrl_fc_vault_objects WHERE object_id = ?').bind(object_id).first<ObjRow>();
  return ok({ object: present(row!), custody }, 201);
});

router.get('/v1/vault/objects/:object_id', async ({ env, params }) => {
  const row = await db(env).prepare('SELECT * FROM mrl_fc_vault_objects WHERE object_id = ?').bind(params.object_id).first<ObjRow>();
  if (!row) return fail('object_not_found', 404, { object_id: params.object_id });
  return ok({ object: present(row) });
});

router.on('DELETE', '/v1/vault/objects/:object_id', async ({ env, params }) => {
  const ts = nowSec();
  const row = await db(env).prepare('SELECT object_key FROM mrl_fc_vault_objects WHERE object_id = ?').bind(params.object_id).first<{ object_key: string }>();
  if (!row) return fail('object_not_found', 404);
  await db(env).prepare(`UPDATE mrl_fc_vault_objects SET r2_state = 'delete_pending', updated_at = ? WHERE object_id = ?`).bind(ts, params.object_id).run();
  await db(env).prepare(`INSERT INTO mrl_fc_vault_transfers (transfer_id, object_id, direction, state, retry_count, origin_signature, created_at) VALUES (?, ?, 'delete', 'queued', 0, 'MrLiouWord', ?)`).bind(uuid(), params.object_id, ts).run();
  await audit(env.MRL_FC_VAULT_DB, 'mrl_fc_vault_audit', { audit_id: uuid(), object_key: row.object_key, action: 'delete_request', origin_signature: 'MrLiouWord', created_at: ts });
  const authority = await dl580Handoff('vault.delete_custody', { object_key: row.object_key });
  return ok({ object_id: params.object_id, r2_state: 'delete_pending', authority });
});

// signed URL is authoritative -> DL580
router.post('/v1/vault/signed-url', async ({ req, env }) => {
  const body = await readJson(req);
  const object_key = requireString(body, 'object_key');
  const row = await db(env).prepare('SELECT object_key FROM mrl_fc_vault_objects WHERE object_key = ?').bind(object_key).first();
  if (!row) return fail('object_not_found', 404, { object_key });
  const signing = await dl580Handoff('vault.sign_download_url', { object_key });
  return ok({ object_key, signed_url: signing });
});

export default {
  async fetch(req: Request, env: Env): Promise<Response> {
    try {
      return await router.handle(req, env);
    } catch (err) {
      if (err instanceof EdgeUnbound) return fail('edge_store_unbound', 503, { hint: 'bind MRL_FC_VAULT_DB (D1 mrliouword-db)' });
      return fail('internal_error', 500);
    }
  },
};
