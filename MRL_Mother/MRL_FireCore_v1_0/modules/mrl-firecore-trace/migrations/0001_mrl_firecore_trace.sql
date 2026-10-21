-- mrl-firecore-trace / Analytics
-- origin_signature: MrLiouWord
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
