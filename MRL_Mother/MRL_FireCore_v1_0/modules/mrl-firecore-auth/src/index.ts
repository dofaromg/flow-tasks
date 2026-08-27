// mrl-firecore-auth — Firebase Auth counterpart (edge identity layer).
// origin_signature: MrLiouWord
//
// Real edge behavior: password identity, PBKDF2 verification, refresh-token
// lifecycle, and audit — all backed by the D1 mirror (mrliouword-db).
// DL580 boundary: the authoritative *access token* (signed JWT / ed25519 origin
// signature) is never minted at the edge; signin/refresh return a typed DL580
// signing hand-off. The opaque refresh token IS minted at the edge (only its
// hash is stored) so sessions are usable without leaking signing authority.

import {
  Router,
  type FireCoreBaseEnv,
  ok,
  fail,
  readJson,
  requireEmail,
  requireString,
  optionalString,
  hashPassword,
  verifyPassword,
  issueToken,
  sha256Hex,
  uuid,
  nowSec,
  audit,
  hashClient,
  hasD1,
  dl580Handoff,
} from '../../../shared/firecore_runtime';

export interface Env extends FireCoreBaseEnv {
  MRL_FC_AUTH_DB?: D1Database;
}

const REFRESH_TTL_SEC = 60 * 60 * 24 * 30; // 30 days

interface UserRow {
  uid: string;
  email: string;
  email_verified: number;
  password_hash: string;
  disabled: number;
  display_name: string | null;
}

function db(env: Env): D1Database {
  if (!hasD1(env.MRL_FC_AUTH_DB)) throw new EdgeUnbound();
  return env.MRL_FC_AUTH_DB;
}

class EdgeUnbound extends Error {}

async function getUserByEmail(env: Env, email: string): Promise<UserRow | null> {
  return db(env)
    .prepare('SELECT uid, email, email_verified, password_hash, disabled, display_name FROM mrl_fc_users WHERE email = ?')
    .bind(email)
    .first<UserRow>();
}

const router = new Router<Env>('mrl-firecore-auth', 'Firebase Auth', [
  '/health',
  '/v1/auth/signup',
  '/v1/auth/signin',
  '/signin',
  '/v1/auth/refresh',
  '/v1/auth/verify',
]);

// --- signup -----------------------------------------------------------------
router.post('/v1/auth/signup', async ({ req, env }) => {
  const body = await readJson(req);
  const email = requireEmail(body);
  const password = requireString(body, 'password', { min: 8, max: 200 });
  const displayName = optionalString(body, 'display_name');

  const existing = await getUserByEmail(env, email);
  if (existing) return fail('email_already_registered', 409);

  const uid = uuid();
  const ts = nowSec();
  const password_hash = await hashPassword(password);
  await db(env)
    .prepare(
      `INSERT INTO mrl_fc_users
       (uid, email, email_verified, password_hash, password_salt, display_name, disabled, provider, origin_signature, created_at, updated_at)
       VALUES (?, ?, 0, ?, ?, ?, 0, 'password', 'MrLiouWord', ?, ?)`,
    )
    .bind(uid, email, password_hash, 'embedded', displayName, ts, ts)
    .run();

  const client = await hashClient(req);
  await audit(env.MRL_FC_AUTH_DB, 'mrl_fc_auth_audit', {
    audit_id: uuid(), uid, action: 'signup', ip_hash: client.ip_hash, user_agent_hash: client.ua_hash,
    origin_signature: 'MrLiouWord', created_at: ts,
  });

  // Canonical identity provisioning is mirrored here; DL580 confirms authority.
  const handoff = await dl580Handoff('auth.provision_identity', { uid, email });
  return ok({ uid, email, email_verified: false, canonical_sync: handoff }, 201);
});

// --- signin -----------------------------------------------------------------
async function signin({ req, env }: { req: Request; env: Env }): Promise<Response> {
  const body = await readJson(req);
  const email = requireEmail(body);
  const password = requireString(body, 'password');

  const user = await getUserByEmail(env, email);
  const client = await hashClient(req);
  if (!user || user.disabled) {
    await audit(env.MRL_FC_AUTH_DB, 'mrl_fc_auth_audit', {
      audit_id: uuid(), uid: user?.uid ?? null, action: 'signin_denied', ip_hash: client.ip_hash,
      user_agent_hash: client.ua_hash, origin_signature: 'MrLiouWord', created_at: nowSec(),
    });
    return fail('invalid_credentials', 401);
  }
  if (!(await verifyPassword(password, user.password_hash))) {
    await audit(env.MRL_FC_AUTH_DB, 'mrl_fc_auth_audit', {
      audit_id: uuid(), uid: user.uid, action: 'signin_denied', ip_hash: client.ip_hash,
      user_agent_hash: client.ua_hash, origin_signature: 'MrLiouWord', created_at: nowSec(),
    });
    return fail('invalid_credentials', 401);
  }

  const { token, tokenHash, tokenId } = await issueToken('mrlrt');
  const ts = nowSec();
  await db(env)
    .prepare(
      `INSERT INTO mrl_fc_refresh_tokens (token_id, uid, token_hash, revoked, expires_at, origin_signature, created_at)
       VALUES (?, ?, ?, 0, ?, 'MrLiouWord', ?)`,
    )
    .bind(tokenId, user.uid, tokenHash, ts + REFRESH_TTL_SEC, ts)
    .run();
  await audit(env.MRL_FC_AUTH_DB, 'mrl_fc_auth_audit', {
    audit_id: uuid(), uid: user.uid, action: 'signin', ip_hash: client.ip_hash,
    user_agent_hash: client.ua_hash, origin_signature: 'MrLiouWord', created_at: ts,
  });

  const accessHandoff = await dl580Handoff('auth.sign_access_token', { uid: user.uid, email: user.email });
  return ok({
    uid: user.uid,
    email: user.email,
    email_verified: !!user.email_verified,
    refresh_token: token,
    refresh_expires_at: ts + REFRESH_TTL_SEC,
    access_token: accessHandoff, // DL580 signs the real JWT
  });
}
router.post('/v1/auth/signin', (ctx) => signin(ctx));
router.post('/signin', (ctx) => signin(ctx)); // legacy alias, preserved

// --- refresh ----------------------------------------------------------------
router.post('/v1/auth/refresh', async ({ req, env }) => {
  const body = await readJson(req);
  const presented = requireString(body, 'refresh_token');
  const presentedHash = await sha256Hex(presented);

  const row = await db(env)
    .prepare('SELECT token_id, uid, revoked, expires_at FROM mrl_fc_refresh_tokens WHERE token_hash = ?')
    .bind(presentedHash)
    .first<{ token_id: string; uid: string; revoked: number; expires_at: number }>();

  if (!row || row.revoked || row.expires_at < nowSec()) return fail('invalid_refresh_token', 401);

  // Rotate: revoke the presented token, mint a fresh one (refresh-token rotation).
  const ts = nowSec();
  const next = await issueToken('mrlrt');
  await db(env).prepare('UPDATE mrl_fc_refresh_tokens SET revoked = 1 WHERE token_id = ?').bind(row.token_id).run();
  await db(env)
    .prepare(
      `INSERT INTO mrl_fc_refresh_tokens (token_id, uid, token_hash, revoked, expires_at, origin_signature, created_at)
       VALUES (?, ?, ?, 0, ?, 'MrLiouWord', ?)`,
    )
    .bind(next.tokenId, row.uid, next.tokenHash, ts + REFRESH_TTL_SEC, ts)
    .run();
  await audit(env.MRL_FC_AUTH_DB, 'mrl_fc_auth_audit', {
    audit_id: uuid(), uid: row.uid, action: 'refresh', ip_hash: null, user_agent_hash: null,
    origin_signature: 'MrLiouWord', created_at: ts,
  });

  const accessHandoff = await dl580Handoff('auth.sign_access_token', { uid: row.uid });
  return ok({ uid: row.uid, refresh_token: next.token, refresh_expires_at: ts + REFRESH_TTL_SEC, access_token: accessHandoff });
});

// --- verify email -----------------------------------------------------------
router.post('/v1/auth/verify', async ({ req, env }) => {
  const body = await readJson(req);
  const uid = requireString(body, 'uid');
  const res = await db(env)
    .prepare('UPDATE mrl_fc_users SET email_verified = 1, updated_at = ? WHERE uid = ?')
    .bind(nowSec(), uid)
    .run();
  if (!res.meta.changes) return fail('user_not_found', 404);
  await audit(env.MRL_FC_AUTH_DB, 'mrl_fc_auth_audit', {
    audit_id: uuid(), uid, action: 'email_verified', ip_hash: null, user_agent_hash: null,
    origin_signature: 'MrLiouWord', created_at: nowSec(),
  });
  return ok({ uid, email_verified: true });
});

export default {
  async fetch(req: Request, env: Env): Promise<Response> {
    try {
      return await router.handle(req, env);
    } catch (err) {
      if (err instanceof EdgeUnbound) return fail('edge_store_unbound', 503, { hint: 'bind MRL_FC_AUTH_DB (D1 mrliouword-db)' });
      return fail('internal_error', 500);
    }
  },
};
