// vector-attention-engine — Cloudflare Worker entry.
// origin_signature: MrLiouWord
//
// Exposes the real attention math over HTTP, plus a KV-backed embedding store
// (PARTICLE_AUTH_VAULT) with graceful degradation when bindings are absent.
// main = src/index.ts (previously missing — wrangler.jsonc pointed at nothing).

import {
  scaledDotProductAttention,
  cosineSimilarity,
  topKSimilar,
  VectorError,
} from './attention';

export interface Env {
  PARTICLE_AUTH_VAULT?: KVNamespace;
  MRLIOUBOOK?: R2Bucket;
}

const ORIGIN_SIGNATURE = 'MrLiouWord';
const HEADERS = {
  'content-type': 'application/json; charset=utf-8',
  'x-mrl-origin-signature': ORIGIN_SIGNATURE,
  'access-control-allow-origin': '*',
  'cache-control': 'no-store',
};
const json = (data: unknown, status = 200) => new Response(JSON.stringify(data, null, 2), { status, headers: HEADERS });
const ok = (data: Record<string, unknown>, status = 200) => json({ ok: true, origin_signature: ORIGIN_SIGNATURE, ...data }, status);
const fail = (error: string, status = 400) => json({ ok: false, error, origin_signature: ORIGIN_SIGNATURE }, status);

function asVector(v: unknown, field: string): number[] {
  if (!Array.isArray(v) || v.length === 0 || !v.every((n) => typeof n === 'number' && Number.isFinite(n))) {
    throw new VectorError(`invalid_vector:${field}`);
  }
  return v as number[];
}
function asMatrix(v: unknown, field: string): number[][] {
  if (!Array.isArray(v) || v.length === 0) throw new VectorError(`invalid_matrix:${field}`);
  return v.map((row, i) => asVector(row, `${field}[${i}]`));
}

async function readBody(req: Request): Promise<Record<string, unknown>> {
  const t = await req.text();
  if (!t) return {};
  try { return JSON.parse(t) as Record<string, unknown>; } catch { throw new VectorError('invalid_json_body'); }
}

export default {
  async fetch(req: Request, env: Env): Promise<Response> {
    if (req.method === 'OPTIONS') {
      return new Response(null, { headers: { ...HEADERS, 'access-control-allow-methods': 'GET,POST,OPTIONS', 'access-control-allow-headers': 'content-type' } });
    }
    const url = new URL(req.url);
    try {
      if (url.pathname === '/health') {
        return ok({ service: 'vector-attention-engine', version: '2.0.0', kv_bound: !!env.PARTICLE_AUTH_VAULT, r2_bound: !!env.MRLIOUBOOK, endpoints: ['/health', '/v1/attention', '/v1/similarity', '/v1/embed/upsert', '/v1/embed/search'] });
      }

      // scaled dot-product attention
      if (url.pathname === '/v1/attention' && req.method === 'POST') {
        const body = await readBody(req);
        const query = asVector(body.query, 'query');
        const keys = asMatrix(body.keys, 'keys');
        const values = asMatrix(body.values, 'values');
        const result = scaledDotProductAttention(query, keys, values);
        return ok({ output: result.output, weights: result.weights, dims: { d: query.length, n: keys.length, dv: values[0].length } });
      }

      // cosine similarity ranking (ephemeral corpus in request)
      if (url.pathname === '/v1/similarity' && req.method === 'POST') {
        const body = await readBody(req);
        const query = asVector(body.query, 'query');
        const corpus = (Array.isArray(body.corpus) ? body.corpus : []).map((c: unknown, i: number) => {
          const rec = c as { id?: unknown; vector?: unknown };
          return { id: typeof rec.id === 'string' ? rec.id : String(i), vector: asVector(rec.vector, `corpus[${i}].vector`) };
        });
        if (corpus.length === 0) return fail('empty_corpus');
        const k = Number(body.top_k) > 0 ? Number(body.top_k) : 5;
        return ok({ query_dim: query.length, top_k: k, results: topKSimilar(query, corpus, k) });
      }

      // KV-backed embedding store (persists across requests when bound)
      if (url.pathname === '/v1/embed/upsert' && req.method === 'POST') {
        if (!env.PARTICLE_AUTH_VAULT) return fail('kv_unbound', 503);
        const body = await readBody(req);
        const id = typeof body.id === 'string' && body.id ? body.id : String(Date.now());
        const vector = asVector(body.vector, 'vector');
        await env.PARTICLE_AUTH_VAULT.put(`vec:${id}`, JSON.stringify(vector));
        return ok({ id, dim: vector.length, stored: true }, 201);
      }
      if (url.pathname === '/v1/embed/search' && req.method === 'POST') {
        if (!env.PARTICLE_AUTH_VAULT) return fail('kv_unbound', 503);
        const body = await readBody(req);
        const query = asVector(body.query, 'query');
        const ids: string[] = Array.isArray(body.ids) ? body.ids.filter((x: unknown): x is string => typeof x === 'string') : [];
        const corpus: { id: string; vector: number[] }[] = [];
        for (const id of ids) {
          const raw = await env.PARTICLE_AUTH_VAULT.get(`vec:${id}`);
          if (raw) corpus.push({ id, vector: JSON.parse(raw) });
        }
        if (corpus.length === 0) return fail('no_vectors_found', 404);
        const k = Number(body.top_k) > 0 ? Number(body.top_k) : 5;
        return ok({ results: topKSimilar(query, corpus, k) });
      }

      return fail('route_not_registered', 404);
    } catch (err) {
      if (err instanceof VectorError) return fail(err.message, 400);
      return fail('internal_error', 500);
    }
  },
};

export { cosineSimilarity };
