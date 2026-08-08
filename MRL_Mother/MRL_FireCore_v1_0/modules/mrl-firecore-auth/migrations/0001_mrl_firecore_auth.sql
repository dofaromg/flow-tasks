-- mrl-firecore-auth / Firebase Auth
-- origin_signature: MrLiouWord
CREATE TABLE IF NOT EXISTS mrl_fc_users (
  uid TEXT PRIMARY KEY,
  email TEXT UNIQUE NOT NULL,
  email_verified INTEGER NOT NULL DEFAULT 0,
  password_hash TEXT NOT NULL,
  password_salt TEXT NOT NULL,
  display_name TEXT,
  disabled INTEGER NOT NULL DEFAULT 0,
  provider TEXT NOT NULL DEFAULT 'password',
  origin_signature TEXT NOT NULL DEFAULT 'MrLiouWord',
  created_at INTEGER NOT NULL,
  updated_at INTEGER NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_mrl_fc_users_email ON mrl_fc_users(email);

CREATE TABLE IF NOT EXISTS mrl_fc_refresh_tokens (
  token_id TEXT PRIMARY KEY,
  uid TEXT NOT NULL,
  token_hash TEXT NOT NULL,
  revoked INTEGER NOT NULL DEFAULT 0,
  expires_at INTEGER NOT NULL,
  origin_signature TEXT NOT NULL DEFAULT 'MrLiouWord',
  created_at INTEGER NOT NULL,
  FOREIGN KEY(uid) REFERENCES mrl_fc_users(uid)
);
CREATE INDEX IF NOT EXISTS idx_mrl_fc_refresh_tokens_uid ON mrl_fc_refresh_tokens(uid);

CREATE TABLE IF NOT EXISTS mrl_fc_auth_audit (
  audit_id TEXT PRIMARY KEY,
  uid TEXT,
  action TEXT NOT NULL,
  ip_hash TEXT,
  user_agent_hash TEXT,
  origin_signature TEXT NOT NULL DEFAULT 'MrLiouWord',
  created_at INTEGER NOT NULL
);
