// MRL FireCore — shared edge runtime.
// origin_signature: MrLiouWord
//
// Design boundary (do not violate):
//   Cloudflare edge  = validation, D1 mirror reads, non-authoritative intent
//                      recording, audit, routing. This layer is REAL and runs here.
//   DL580 authority  = ed25519 origin signing, PostgreSQL authoritative writes,
//                      NAS object custody, event-bus fan-out. The edge never
//                      forges these; it records a pending intent and returns a
//                      typed DL580 hand-off descriptor.
//
// This file replaces the previous "return 202 accepted:false" template with a
// working edge implementation while preserving the sovereignty boundary above.

export const ORIGIN_SIGNATURE = 'MrLiouWord';

export interface FireCoreBaseEnv {
  MRL_ORIGIN_SIGNATURE?: string;
  MRL_FIRECORE_MODE?: string;
  MRL_FIRECORE_NO_DEPLOY?: string;
  MRL_FIREBASE_COUNTERPART?: string;
  MRL_DL580_SIGNING_URL?: string;
}

const JSON_HEADERS: Record<string, string> = {
  'content-type': 'application/json; charset=utf-8',
  'x-mrl-origin-signature': ORIGIN_SIGNATURE,
  'access-control-allow-origin': '*',
  'access-control-expose-headers': 'x-mrl-origin-signature',
  'cache-control': 'no-store',
};

export function json(data: unknown, status = 200, extra?: Record<string, string>): Response {
  return new Response(JSON.stringify(data, null, 2), {
    status,
    headers: { ...JSON_HEADERS, ...(extra ?? {}) },
  });
}

export function ok(data: Record<string, unknown>, status = 200): Response {
  return json({ ok: true, origin_signature: ORIGIN_SIGNATURE, ...data }, status);
}

export function fail(error: string, status = 400, extra?: Record<string, unknown>): Response {
  return json({ ok: false, error, origin_signature: ORIGIN_SIGNATURE, ...(extra ?? {}) }, status);
}

export function preflight(): Response {
  return new Response(null, {
    headers: {
      'access-control-allow-origin': '*',
      'access-control-allow-methods': 'GET,POST,PUT,PATCH,DELETE,OPTIONS',
      'access-control-allow-headers': 'content-type, authorization, x-mrl-origin-signature',
      'access-control-max-age': '86400',
    },
  });
}

// ---------------------------------------------------------------------------
// Body parsing + validation
// ---------------------------------------------------------------------------

export async function readJson(req: Request): Promise<Record<string, unknown>> {
  const text = await req.text();
  if (!text) return {};
  try {
    const parsed = JSON.parse(text);
    return parsed && typeof parsed === 'object' ? (parsed as Record<string, unknown>) : { value: parsed };
  } catch {
    throw new ValidationError('invalid_json_body');
  }
}

export class ValidationError extends Error {}

export function requireString(body: Record<string, unknown>, field: string, opts?: { min?: number; max?: number }): string {
  const v = body[field];
  if (typeof v !== 'string' || v.length === 0) throw new ValidationError(`missing_or_empty:${field}`);
  if (opts?.min && v.length < opts.min) throw new ValidationError(`too_short:${field}`);
  if (opts?.max && v.length > opts.max) throw new ValidationError(`too_long:${field}`);
  return v;
}

export function optionalString(body: Record<string, unknown>, field: string): string | null {
  const v = body[field];
  return typeof v === 'string' && v.length > 0 ? v : null;
}

const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
export function requireEmail(body: Record<string, unknown>, field = 'email'): string {
  const v = requireString(body, field).toLowerCase();
  if (!EMAIL_RE.test(v)) throw new ValidationError(`invalid_email:${field}`);
  return v;
}

// ---------------------------------------------------------------------------
// Crypto helpers (WebCrypto — available on Workers and Node 22)
// ---------------------------------------------------------------------------

export function uuid(): string {
  return crypto.randomUUID();
}

export async function sha256Hex(input: string): Promise<string> {
  const data = new TextEncoder().encode(input);
  const digest = await crypto.subtle.digest('SHA-256', data);
  return hex(new Uint8Array(digest));
}

function hex(bytes: Uint8Array): string {
  let out = '';
  for (const b of bytes) out += b.toString(16).padStart(2, '0');
  return out;
}

function randomHex(byteLen: number): string {
  const b = new Uint8Array(byteLen);
  crypto.getRandomValues(b);
  return hex(b);
}

const PBKDF2_ITERATIONS = 120_000;

// Returns "salt$iterations$derivedHex" — self-describing, DL580 can re-verify.
export async function hashPassword(password: string): Promise<string> {
  const salt = randomHex(16);
  const derived = await pbkdf2(password, salt, PBKDF2_ITERATIONS);
  return `${salt}$${PBKDF2_ITERATIONS}$${derived}`;
}

export async function verifyPassword(password: string, stored: string): Promise<boolean> {
  const parts = stored.split('$');
  if (parts.length !== 3) return false;
  const [salt, iterStr, expected] = parts;
  const iterations = Number(iterStr);
  if (!Number.isFinite(iterations) || iterations <= 0) return false;
  const derived = await pbkdf2(password, salt, iterations);
  return timingSafeEqual(derived, expected);
}

async function pbkdf2(password: string, salt: string, iterations: number): Promise<string> {
  const key = await crypto.subtle.importKey('raw', new TextEncoder().encode(password), 'PBKDF2', false, ['deriveBits']);
  const bits = await crypto.subtle.deriveBits(
    { name: 'PBKDF2', salt: new TextEncoder().encode(salt), iterations, hash: 'SHA-256' },
    key,
    256,
  );
  return hex(new Uint8Array(bits));
}

export function timingSafeEqual(a: string, b: string): boolean {
  if (a.length !== b.length) return false;
  let diff = 0;
  for (let i = 0; i < a.length; i++) diff |= a.charCodeAt(i) ^ b.charCodeAt(i);
  return diff === 0;
}

// A random, opaque bearer token plus its stored hash (only the hash is persisted).
export async function issueToken(prefix: string): Promise<{ token: string; tokenHash: string; tokenId: string }> {
  const tokenId = uuid();
  const secret = randomHex(32);
  const token = `${prefix}_${tokenId}.${secret}`;
  const tokenHash = await sha256Hex(token);
  return { token, tokenHash, tokenId };
}

// ---------------------------------------------------------------------------
// DL580 authoritative hand-off (edge never forges authority)
// ---------------------------------------------------------------------------

export interface DL580Handoff {
  authority: 'DL580';
  status: 'pending_dl580';
  operation: string;
  intent_id: string;
  payload_sha256: string;
  contract: string;
  issued_at: number;
}

// Records that the edge has accepted an intent and is deferring the
// authoritative step to DL580. `payload` is hashed so DL580 can bind the
// signature to exactly what the edge saw.
export async function dl580Handoff(operation: string, payload: unknown): Promise<DL580Handoff> {
  const payload_sha256 = await sha256Hex(JSON.stringify(payload ?? null));
  return {
    authority: 'DL580',
    status: 'pending_dl580',
    operation,
    intent_id: uuid(),
    payload_sha256,
    contract: 'runtime/dl580-signing-service/signature_contract.json',
    issued_at: nowSec(),
  };
}

export function nowSec(): number {
  return Math.floor(Date.now() / 1000);
}

// ---------------------------------------------------------------------------
// D1 helpers + audit
// ---------------------------------------------------------------------------

export function hasD1(db: D1Database | undefined): db is D1Database {
  return !!db && typeof db.prepare === 'function';
}

// Best-effort audit insert. Never throws into the request path.
export async function audit(
  db: D1Database | undefined,
  table: string,
  row: Record<string, unknown>,
): Promise<void> {
  if (!hasD1(db)) return;
  const cols = Object.keys(row);
  const placeholders = cols.map(() => '?').join(', ');
  const sql = `INSERT INTO ${table} (${cols.join(', ')}) VALUES (${placeholders})`;
  try {
    await db.prepare(sql).bind(...cols.map((c) => row[c])).run();
  } catch {
    // Audit is advisory at the edge; the authoritative trail lives on DL580.
  }
}

export async function hashClient(req: Request): Promise<{ ip_hash: string | null; ua_hash: string | null }> {
  const ip = req.headers.get('cf-connecting-ip') ?? req.headers.get('x-forwarded-for');
  const ua = req.headers.get('user-agent');
  return {
    ip_hash: ip ? await sha256Hex(ip) : null,
    ua_hash: ua ? await sha256Hex(ua) : null,
  };
}

// ---------------------------------------------------------------------------
// Router — small, dependency-free, supports :params
// ---------------------------------------------------------------------------

export type Handler<E> = (ctx: RouteContext<E>) => Promise<Response> | Response;

export interface RouteContext<E> {
  req: Request;
  env: E;
  params: Record<string, string>;
  url: URL;
}

interface Route<E> {
  method: string;
  parts: string[];
  handler: Handler<E>;
}

export class Router<E extends FireCoreBaseEnv> {
  private routes: Route<E>[] = [];

  constructor(
    private readonly moduleName: string,
    private readonly firebaseCounterpart: string,
    private readonly endpoints: string[],
  ) {}

  on(method: string, pattern: string, handler: Handler<E>): this {
    this.routes.push({ method, parts: split(pattern), handler });
    return this;
  }

  get(p: string, h: Handler<E>): this { return this.on('GET', p, h); }
  post(p: string, h: Handler<E>): this { return this.on('POST', p, h); }

  async handle(req: Request, env: E): Promise<Response> {
    if (req.method === 'OPTIONS') return preflight();

    const url = new URL(req.url);
    if (url.pathname === '/health') return this.health(env);

    const reqParts = split(url.pathname);
    for (const route of this.routes) {
      if (route.method !== req.method) continue;
      const params = match(route.parts, reqParts);
      if (!params) continue;
      try {
        return await route.handler({ req, env, params, url });
      } catch (err) {
        if (err instanceof ValidationError) return fail(err.message, 400, { module: this.moduleName });
        return fail('internal_error', 500, { module: this.moduleName });
      }
    }
    return fail('route_not_registered', 404, { module: this.moduleName, path: url.pathname });
  }

  private health(env: E): Response {
    return ok({
      service: this.moduleName,
      firebase_counterpart: env.MRL_FIREBASE_COUNTERPART || this.firebaseCounterpart,
      mode: env.MRL_FIRECORE_MODE || 'local_backfill',
      deploy_guard: env.MRL_FIRECORE_NO_DEPLOY || '1',
      authority_boundary: 'edge_mirror + DL580_authority',
      endpoints: this.endpoints,
    });
  }
}

function split(path: string): string[] {
  return path.split('/').filter((s) => s.length > 0);
}

// Returns the extracted :params if the pattern matches, else null.
function match(pattern: string[], actual: string[]): Record<string, string> | null {
  if (pattern.length !== actual.length) return null;
  const params: Record<string, string> = {};
  for (let i = 0; i < pattern.length; i++) {
    const p = pattern[i];
    if (p.startsWith(':')) params[p.slice(1)] = decodeURIComponent(actual[i]);
    else if (p !== actual[i]) return null;
  }
  return params;
}
