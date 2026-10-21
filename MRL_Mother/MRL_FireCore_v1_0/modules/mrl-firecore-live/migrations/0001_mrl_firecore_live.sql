-- mrl-firecore-live / Firestore Listeners
-- origin_signature: MrLiouWord
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
