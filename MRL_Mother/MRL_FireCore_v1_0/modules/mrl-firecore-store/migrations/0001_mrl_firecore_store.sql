-- mrl-firecore-store / Firestore
-- origin_signature: MrLiouWord
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
