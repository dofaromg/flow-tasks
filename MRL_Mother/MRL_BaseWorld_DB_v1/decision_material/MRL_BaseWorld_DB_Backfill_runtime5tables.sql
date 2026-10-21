CREATE TABLE IF NOT EXISTS MRL_MetaIR_Record (
  record_id TEXT PRIMARY KEY,
  input_hash TEXT NOT NULL,
  primary_intent TEXT NOT NULL,
  node_count INTEGER NOT NULL,
  created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS MRL_ParticleIR_Node (
  particle_id TEXT PRIMARY KEY,
  particle_type TEXT NOT NULL,
  source_node TEXT NOT NULL,
  layer_name TEXT NOT NULL,
  weight REAL NOT NULL,
  signature TEXT NOT NULL,
  payload TEXT NOT NULL,
  created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS MRL_RuntimeGraph_Edge (
  edge_id TEXT PRIMARY KEY,
  from_particle_id TEXT NOT NULL,
  to_particle_id TEXT NOT NULL,
  relation_name TEXT NOT NULL,
  weight REAL NOT NULL,
  created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS MRL_Attention_Route (
  route_id TEXT PRIMARY KEY,
  particle_id TEXT NOT NULL,
  target_module TEXT NOT NULL,
  attention_score REAL NOT NULL,
  reason TEXT NOT NULL,
  created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS MRL_Verification_Report (
  report_id TEXT PRIMARY KEY,
  original_hash TEXT NOT NULL,
  reconstructed_hash TEXT NOT NULL,
  lossless_text_roundtrip INTEGER NOT NULL,
  particle_signatures_ok INTEGER NOT NULL,
  status TEXT NOT NULL,
  created_at TEXT NOT NULL
);
