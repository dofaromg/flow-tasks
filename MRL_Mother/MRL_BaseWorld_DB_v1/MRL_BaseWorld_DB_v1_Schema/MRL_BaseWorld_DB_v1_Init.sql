-- =========================================================
-- MRL_BaseWorld_DB_v1_Init.sql
-- version: v1.0
-- purpose: Initialize ROOT, Closure Law, and first Canon State
-- =========================================================

-- Insert ROOT
INSERT INTO MRL_Identity_Signature_Root (
  root_id, origin_signature, authority_owner, naming_law_version, closure_law_version, created_at, updated_at
) VALUES (
  'root:mrl:mrliou',
  'MrLiouWord',
  'MrLiou',
  'MRL_Naming_Law_v2',
  'MRL_Closure_Law_v1',
  datetime('now'),
  datetime('now')
);

-- Insert Closure Law
INSERT INTO MRL_Closure_Law_Root (
  law_id, root_ref, observe_enabled, resolve_enabled, mirror_enabled, verify_enabled, loop_enabled,
  authority_invariance, no_delete_law, additive_resolution, created_at, updated_at
) VALUES (
  'law:mrl:closure:v1',
  'root:mrl:mrliou',
  1,1,1,1,1,
  1,1,1,
  datetime('now'),
  datetime('now')
);

-- Insert first Canon State
INSERT INTO MRL_Canon_State (
  canon_state_id, state_hash, state_version, state_class, resolve_status, conflict_count, proof_status, created_at, updated_at
) VALUES (
  'canon:baseworld:v1',
  'pending',
  'v1.0.0',
  'baseworld',
  'initialized',
  0,
  'pending',
  datetime('now'),
  datetime('now')
);
