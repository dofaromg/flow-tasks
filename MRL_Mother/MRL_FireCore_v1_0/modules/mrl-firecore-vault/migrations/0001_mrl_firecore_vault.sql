-- mrl-firecore-vault / Firebase Storage
-- origin_signature: MrLiouWord
CREATE TABLE IF NOT EXISTS mrl_fc_vault_objects (
  object_id TEXT PRIMARY KEY,
  bucket_name TEXT NOT NULL DEFAULT 'mrl-firecore-vault',
  object_key TEXT NOT NULL UNIQUE,
  content_type TEXT,
  byte_size INTEGER NOT NULL DEFAULT 0,
  sha256 TEXT NOT NULL,
  dl580_path TEXT NOT NULL,
  r2_state TEXT NOT NULL DEFAULT 'edge_pending',
  origin_signature TEXT NOT NULL DEFAULT 'MrLiouWord',
  created_at INTEGER NOT NULL,
  updated_at INTEGER NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_mrl_fc_vault_objects_key ON mrl_fc_vault_objects(object_key);

CREATE TABLE IF NOT EXISTS mrl_fc_vault_transfers (
  transfer_id TEXT PRIMARY KEY,
  object_id TEXT NOT NULL,
  direction TEXT NOT NULL,
  state TEXT NOT NULL,
  retry_count INTEGER NOT NULL DEFAULT 0,
  origin_signature TEXT NOT NULL DEFAULT 'MrLiouWord',
  created_at INTEGER NOT NULL,
  FOREIGN KEY(object_id) REFERENCES mrl_fc_vault_objects(object_id)
);

CREATE TABLE IF NOT EXISTS mrl_fc_vault_audit (
  audit_id TEXT PRIMARY KEY,
  object_key TEXT NOT NULL,
  action TEXT NOT NULL,
  origin_signature TEXT NOT NULL DEFAULT 'MrLiouWord',
  created_at INTEGER NOT NULL
);
