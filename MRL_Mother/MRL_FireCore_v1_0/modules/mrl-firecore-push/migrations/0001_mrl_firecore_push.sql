-- mrl-firecore-push / Cloud Messaging / FCM
-- origin_signature: MrLiouWord
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
