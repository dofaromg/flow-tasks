const MODULE_NAME = 'mrl-firecore-auth';
const FIREBASE_COUNTERPART = 'Firebase Auth';
const ORIGIN_SIGNATURE = 'MrLiouWord';
const PRIORITY = 'P0';
const BATCH = 'Batch 052';

export interface Env {
  MRL_ORIGIN_SIGNATURE?: string;
  MRL_FIRECORE_MODE?: string;
  MRL_FIRECORE_NO_DEPLOY?: string;
}

function J(data: unknown, status = 200): Response {
  return new Response(JSON.stringify(data, null, 2), {
    status,
    headers: {
      'content-type': 'application/json; charset=utf-8',
      'x-mrl-origin-signature': ORIGIN_SIGNATURE,
      'access-control-allow-origin': '*',
      'access-control-expose-headers': 'x-mrl-origin-signature',
      'cache-control': 'no-store'
    }
  });
}

function health(env: Env): Response {
  return J({
    ok: true,
    service: MODULE_NAME,
    firebase_counterpart: FIREBASE_COUNTERPART,
    priority: PRIORITY,
    batch: BATCH,
    mode: env.MRL_FIRECORE_MODE || 'local_backfill',
    deploy_guard: env.MRL_FIRECORE_NO_DEPLOY || '1',
    origin_signature: env.MRL_ORIGIN_SIGNATURE || ORIGIN_SIGNATURE,
    endpoints: ["/health", "/v1/auth/signup", "/v1/auth/signin", "/signin", "/v1/auth/refresh", "/v1/auth/verify"]
  });
}

async function authContract(path: string, body: unknown) {
  return J({
    ok: true,
    module: MODULE_NAME,
    path,
    accepted: false,
    reason: 'local contract response only; JWT private signing remains on DL580',
    request_shape_seen: typeof body,
    origin_signature: ORIGIN_SIGNATURE
  }, 202);
}

async function readBody(req: Request): Promise<unknown> {
  const text = await req.text();
  if (!text) return null;
  try {
    return JSON.parse(text);
  } catch {
    return { raw: text };
  }
}

export default {
  async fetch(req: Request, env: Env): Promise<Response> {
    const url = new URL(req.url);
    const path = url.pathname;

    if (req.method === 'OPTIONS') {
      return new Response(null, {
        headers: {
          'access-control-allow-origin': '*',
          'access-control-allow-methods': 'GET,POST,PUT,PATCH,DELETE,OPTIONS',
          'access-control-allow-headers': 'content-type, authorization, x-mrl-origin-signature'
        }
      });
    }

    if (path === '/health') return health(env);

    const body = await readBody(req);
    if (path.startsWith('/v1/auth') || path === '/signin') return authContract(path, body);

    return J({
      ok: false,
      service: MODULE_NAME,
      error: 'route_not_registered',
      path,
      origin_signature: ORIGIN_SIGNATURE
    }, 404);
  }
};
