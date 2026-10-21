// mrl-firecore-store — Firestore counterpart (edge document mirror).
// origin_signature: MrLiouWord
//
// Real edge behavior: collection/document CRUD against the D1 mirror, version
// history, soft-delete, and collection query. Each mirror row tracks
// dl580_sync_state; DL580 PostgreSQL remains the authority and reconciles the
// pending rows. Deletes are soft (deleted=1) — no hard removal at the edge.

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
  MRL_FC_STORE_DB?: D1Database;
}

class EdgeUnbound extends Error {}
function db(env: Env): D1Database {
  if (!hasD1(env.MRL_FC_STORE_DB)) throw new EdgeUnbound();
  return env.MRL_FC_STORE_DB;
}

interface DocRow {
  doc_id: string;
  collection_path: string;
  document_path: string;
  payload_json: string;
  version: number;
  deleted: number;
  dl580_sync_state: string;
  updated_at: number;
}

function present(row: DocRow) {
  return {
    doc_id: row.doc_id,
    collection: row.collection_path,
    path: row.document_path,
    version: row.version,
    data: JSON.parse(row.payload_json),
    dl580_sync_state: row.dl580_sync_state,
    updated_at: row.updated_at,
  };
}

const router = new Router<Env>('mrl-firecore-store', 'Firestore', [
  '/health',
  '/v1/store/documents',
  '/v1/store/documents/:collection/:id',
  '/v1/store/query',
]);

// create
router.post('/v1/store/documents', async ({ req, env }) => {
  const body = await readJson(req);
  const collection = requireString(body, 'collection', { max: 200 });
  const id = typeof body.id === 'string' && body.id ? body.id : uuid();
  const data = body.data ?? {};
  const document_path = `${collection}/${id}`;
  const ts = nowSec();

  const exists = await db(env).prepare('SELECT doc_id FROM mrl_fc_documents WHERE document_path = ?').bind(document_path).first();
  if (exists) return fail('document_already_exists', 409, { path: document_path });

  const doc_id = uuid();
  const payload_json = JSON.stringify(data);
  await db(env)
    .prepare(
      `INSERT INTO mrl_fc_documents
       (doc_id, collection_path, document_path, payload_json, version, deleted, origin_signature, dl580_sync_state, created_at, updated_at)
       VALUES (?, ?, ?, ?, 1, 0, 'MrLiouWord', 'pending', ?, ?)`,
    )
    .bind(doc_id, collection, document_path, payload_json, ts, ts)
    .run();
  await db(env)
    .prepare(`INSERT INTO mrl_fc_document_versions (version_id, doc_id, version, payload_json, origin_signature, created_at) VALUES (?, ?, 1, ?, 'MrLiouWord', ?)`)
    .bind(uuid(), doc_id, payload_json, ts)
    .run();
  await audit(env.MRL_FC_STORE_DB, 'mrl_fc_store_audit', { audit_id: uuid(), document_path, action: 'create', origin_signature: 'MrLiouWord', created_at: ts });

  const sync = await dl580Handoff('store.upsert_document', { document_path, version: 1 });
  const row = await db(env).prepare('SELECT * FROM mrl_fc_documents WHERE doc_id = ?').bind(doc_id).first<DocRow>();
  return ok({ document: present(row!), authority_sync: sync }, 201);
});

// read
router.get('/v1/store/documents/:collection/:id', async ({ env, params }) => {
  const document_path = `${params.collection}/${params.id}`;
  const row = await db(env).prepare('SELECT * FROM mrl_fc_documents WHERE document_path = ? AND deleted = 0').bind(document_path).first<DocRow>();
  if (!row) return fail('document_not_found', 404, { path: document_path });
  return ok({ document: present(row) });
});

// update (new version)
router.on('PUT', '/v1/store/documents/:collection/:id', async ({ req, env, params }) => {
  const body = await readJson(req);
  const data = body.data ?? {};
  const document_path = `${params.collection}/${params.id}`;
  const row = await db(env).prepare('SELECT * FROM mrl_fc_documents WHERE document_path = ? AND deleted = 0').bind(document_path).first<DocRow>();
  if (!row) return fail('document_not_found', 404, { path: document_path });

  const nextVersion = row.version + 1;
  const payload_json = JSON.stringify(data);
  const ts = nowSec();
  await db(env).prepare(`UPDATE mrl_fc_documents SET payload_json = ?, version = ?, dl580_sync_state = 'pending', updated_at = ? WHERE doc_id = ?`).bind(payload_json, nextVersion, ts, row.doc_id).run();
  await db(env).prepare(`INSERT INTO mrl_fc_document_versions (version_id, doc_id, version, payload_json, origin_signature, created_at) VALUES (?, ?, ?, ?, 'MrLiouWord', ?)`).bind(uuid(), row.doc_id, nextVersion, payload_json, ts).run();
  await audit(env.MRL_FC_STORE_DB, 'mrl_fc_store_audit', { audit_id: uuid(), document_path, action: 'update', origin_signature: 'MrLiouWord', created_at: ts });

  const sync = await dl580Handoff('store.upsert_document', { document_path, version: nextVersion });
  const updated = await db(env).prepare('SELECT * FROM mrl_fc_documents WHERE doc_id = ?').bind(row.doc_id).first<DocRow>();
  return ok({ document: present(updated!), authority_sync: sync });
});

// soft delete
router.on('DELETE', '/v1/store/documents/:collection/:id', async ({ env, params }) => {
  const document_path = `${params.collection}/${params.id}`;
  const ts = nowSec();
  const res = await db(env).prepare(`UPDATE mrl_fc_documents SET deleted = 1, dl580_sync_state = 'pending', updated_at = ? WHERE document_path = ? AND deleted = 0`).bind(ts, document_path).run();
  if (!res.meta.changes) return fail('document_not_found', 404, { path: document_path });
  await audit(env.MRL_FC_STORE_DB, 'mrl_fc_store_audit', { audit_id: uuid(), document_path, action: 'soft_delete', origin_signature: 'MrLiouWord', created_at: ts });
  const sync = await dl580Handoff('store.soft_delete', { document_path });
  return ok({ path: document_path, deleted: true, authority_sync: sync });
});

// query a collection
router.post('/v1/store/query', async ({ req, env }) => {
  const body = await readJson(req);
  const collection = requireString(body, 'collection');
  const limit = Math.min(Number(body.limit) > 0 ? Number(body.limit) : 50, 200);
  const rows = await db(env)
    .prepare('SELECT * FROM mrl_fc_documents WHERE collection_path = ? AND deleted = 0 ORDER BY updated_at DESC LIMIT ?')
    .bind(collection, limit)
    .all<DocRow>();
  return ok({ collection, count: rows.results.length, documents: rows.results.map(present) });
});

export default {
  async fetch(req: Request, env: Env): Promise<Response> {
    try {
      return await router.handle(req, env);
    } catch (err) {
      if (err instanceof EdgeUnbound) return fail('edge_store_unbound', 503, { hint: 'bind MRL_FC_STORE_DB (D1 mrliouword-db)' });
      return fail('internal_error', 500);
    }
  },
};
