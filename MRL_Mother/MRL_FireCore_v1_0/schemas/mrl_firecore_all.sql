-- MRL FireCore v1.0 combined schema
-- origin_signature: MrLiouWord


-- ============================================================
-- mrl-firecore-auth / Firebase Auth
-- ============================================================
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


-- ============================================================
-- mrl-firecore-store / Firestore
-- ============================================================
CREATE TABLE IF NOT EXISTS mrl_fc_documents (
  doc_id TEXT PRIMARY KEY,
  collection_path TEXT NOT NULL,
  document_path TEXT NOT NULL UNIQUE,
  payload_json TEXT NOT NULL,
  version INTEGER NOT NULL DEFAULT 1,
  deleted INTEGER NOT NULL DEFAULT 0,
  origin_signature TEXT NOT NULL DEFAULT 'MrLiouWord',
  dl580_sync_state TEXT NOT NULL DEFAULT 'pending',
  created_at INTEGER NOT NULL,
  updated_at INTEGER NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_mrl_fc_documents_collection ON mrl_fc_documents(collection_path);
CREATE INDEX IF NOT EXISTS idx_mrl_fc_documents_sync ON mrl_fc_documents(dl580_sync_state);

CREATE TABLE IF NOT EXISTS mrl_fc_document_versions (
  version_id TEXT PRIMARY KEY,
  doc_id TEXT NOT NULL,
  version INTEGER NOT NULL,
  payload_json TEXT NOT NULL,
  origin_signature TEXT NOT NULL DEFAULT 'MrLiouWord',
  created_at INTEGER NOT NULL,
  FOREIGN KEY(doc_id) REFERENCES mrl_fc_documents(doc_id)
);

CREATE TABLE IF NOT EXISTS mrl_fc_store_audit (
  audit_id TEXT PRIMARY KEY,
  document_path TEXT NOT NULL,
  action TEXT NOT NULL,
  origin_signature TEXT NOT NULL DEFAULT 'MrLiouWord',
  created_at INTEGER NOT NULL
);


-- ============================================================
-- mrl-firecore-vault / Firebase Storage
-- ============================================================
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


-- ============================================================
-- mrl-firecore-live / Firestore Listeners
-- ============================================================
CREATE TABLE IF NOT EXISTS mrl_fc_live_topics (
  topic_id TEXT PRIMARY KEY,
  topic_path TEXT NOT NULL UNIQUE,
  source_kind TEXT NOT NULL DEFAULT 'dl580_pg_notify',
  origin_signature TEXT NOT NULL DEFAULT 'MrLiouWord',
  created_at INTEGER NOT NULL,
  updated_at INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS mrl_fc_live_events (
  event_id TEXT PRIMARY KEY,
  topic_id TEXT NOT NULL,
  event_type TEXT NOT NULL,
  payload_json TEXT NOT NULL,
  sequence_no INTEGER NOT NULL,
  origin_signature TEXT NOT NULL DEFAULT 'MrLiouWord',
  created_at INTEGER NOT NULL,
  FOREIGN KEY(topic_id) REFERENCES mrl_fc_live_topics(topic_id)
);
CREATE INDEX IF NOT EXISTS idx_mrl_fc_live_events_topic_seq ON mrl_fc_live_events(topic_id, sequence_no);

CREATE TABLE IF NOT EXISTS mrl_fc_live_clients (
  client_id TEXT PRIMARY KEY,
  topic_path TEXT NOT NULL,
  transport TEXT NOT NULL,
  last_seen_at INTEGER NOT NULL,
  origin_signature TEXT NOT NULL DEFAULT 'MrLiouWord'
);


-- ============================================================
-- mrl-firecore-push / Cloud Messaging / FCM
-- ============================================================
CREATE TABLE IF NOT EXISTS mrl_fc_push_devices (
  device_id TEXT PRIMARY KEY,
  uid TEXT,
  platform TEXT NOT NULL,
  token_hash TEXT NOT NULL,
  enabled INTEGER NOT NULL DEFAULT 1,
  origin_signature TEXT NOT NULL DEFAULT 'MrLiouWord',
  created_at INTEGER NOT NULL,
  updated_at INTEGER NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_mrl_fc_push_devices_uid ON mrl_fc_push_devices(uid);

CREATE TABLE IF NOT EXISTS mrl_fc_push_topics (
  topic_id TEXT PRIMARY KEY,
  topic_name TEXT NOT NULL UNIQUE,
  origin_signature TEXT NOT NULL DEFAULT 'MrLiouWord',
  created_at INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS mrl_fc_push_jobs (
  job_id TEXT PRIMARY KEY,
  topic_name TEXT,
  device_id TEXT,
  payload_json TEXT NOT NULL,
  state TEXT NOT NULL DEFAULT 'queued',
  origin_signature TEXT NOT NULL DEFAULT 'MrLiouWord',
  created_at INTEGER NOT NULL,
  sent_at INTEGER
);


-- ============================================================
-- mrl-firecore-trace / Analytics
-- ============================================================
CREATE TABLE IF NOT EXISTS mrl_fc_trace_events (
  event_id TEXT PRIMARY KEY,
  session_id TEXT,
  event_name TEXT NOT NULL,
  payload_json TEXT NOT NULL,
  client_ts INTEGER,
  origin_signature TEXT NOT NULL DEFAULT 'MrLiouWord',
  created_at INTEGER NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_mrl_fc_trace_events_name ON mrl_fc_trace_events(event_name);
CREATE INDEX IF NOT EXISTS idx_mrl_fc_trace_events_session ON mrl_fc_trace_events(session_id);

CREATE TABLE IF NOT EXISTS mrl_fc_trace_sessions (
  session_id TEXT PRIMARY KEY,
  uid TEXT,
  started_at INTEGER NOT NULL,
  ended_at INTEGER,
  origin_signature TEXT NOT NULL DEFAULT 'MrLiouWord'
);

CREATE TABLE IF NOT EXISTS mrl_fc_trace_rollups (
  rollup_id TEXT PRIMARY KEY,
  window_start INTEGER NOT NULL,
  window_end INTEGER NOT NULL,
  metric_name TEXT NOT NULL,
  metric_value REAL NOT NULL,
  origin_signature TEXT NOT NULL DEFAULT 'MrLiouWord',
  created_at INTEGER NOT NULL
);
