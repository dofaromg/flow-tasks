-- =========================================================
-- MRL_FLTNZ_Asset_Seed_Insert_v1.sql
-- version: v1.0
-- purpose: First batch of canonical FLTNZ assets
-- =========================================================

-- Asset 1: FlowAgent.TotalCore.Unity
INSERT INTO MRL_FLTNZ_Asset (
  fltnz_id, asset_name, asset_family, asset_role, asset_version, asset_variant,
  asset_hash, storage_location, canonical_status, source_file, created_at, updated_at
) VALUES (
  'fltnz:flowagent:totalcore:unity:v1',
  'FlowAgent.TotalCore.Unity',
  'FlowAgent',
  'core',
  'v1.0',
  'unity',
  'pending',
  'storage/fltnz/flowagent/',
  'canonical',
  'FlowAgent.TotalCore.Unity.fltnz',
  datetime('now'),
  datetime('now')
);

-- Asset 2: WorldSeed
INSERT INTO MRL_FLTNZ_Asset (
  fltnz_id, asset_name, asset_family, asset_role, asset_version, asset_variant,
  asset_hash, storage_location, canonical_status, source_file, created_at, updated_at
) VALUES (
  'fltnz:worldseed:v1',
  'WorldSeed',
  'Seed',
  'world_foundation',
  'v1.0',
  'standard',
  'pending',
  'storage/fltnz/seed/',
  'canonical',
  'WorldSeed.fltnz',
  datetime('now'),
  datetime('now')
);

-- Asset 3: PulseRouter
INSERT INTO MRL_FLTNZ_Asset (
  fltnz_id, asset_name, asset_family, asset_role, asset_version, asset_variant,
  asset_hash, storage_location, canonical_status, source_file, created_at, updated_at
) VALUES (
  'fltnz:pulserouter:v1',
  'PulseRouter',
  'Router',
  'pulse_routing',
  'v1.0',
  'standard',
  'pending',
  'storage/fltnz/router/',
  'canonical',
  'PulseRouter.fltnz',
  datetime('now'),
  datetime('now')
);

-- Asset 4: EncoderStack
INSERT INTO MRL_FLTNZ_Asset (
  fltnz_id, asset_name, asset_family, asset_role, asset_version, asset_variant,
  asset_hash, storage_location, canonical_status, source_file, created_at, updated_at
) VALUES (
  'fltnz:encoderstack:v1',
  'EncoderStack',
  'Encoder',
  'encoding',
  'v1.0',
  'stack',
  'pending',
  'storage/fltnz/encoder/',
  'canonical',
  'EncoderStack.fltnz',
  datetime('now'),
  datetime('now')
);

-- Asset 5: LicenseMap
INSERT INTO MRL_FLTNZ_Asset (
  fltnz_id, asset_name, asset_family, asset_role, asset_version, asset_variant,
  asset_hash, storage_location, canonical_status, source_file, created_at, updated_at
) VALUES (
  'fltnz:licensemap:v1',
  'LicenseMap',
  'Map',
  'licensing',
  'v1.0',
  'standard',
  'pending',
  'storage/fltnz/map/',
  'canonical',
  'LicenseMap.fltnz',
  datetime('now'),
  datetime('now')
);

-- Asset 6: UnityPackage
INSERT INTO MRL_FLTNZ_Asset (
  fltnz_id, asset_name, asset_family, asset_role, asset_version, asset_variant,
  asset_hash, storage_location, canonical_status, source_file, created_at, updated_at
) VALUES (
  'fltnz:unitypackage:v1',
  'UnityPackage',
  'Package',
  'unity_container',
  'v1.0',
  'standard',
  'pending',
  'storage/fltnz/package/',
  'canonical',
  'UnityPackage.fltnz',
  datetime('now'),
  datetime('now')
);

-- Asset 7: MRLsmall
INSERT INTO MRL_FLTNZ_Asset (
  fltnz_id, asset_name, asset_family, asset_role, asset_version, asset_variant,
  asset_hash, storage_location, canonical_status, source_file, created_at, updated_at
) VALUES (
  'fltnz:mrlsmall:v1',
  'MRLsmall',
  'Model',
  'small_model',
  'v1.0',
  'compact',
  'pending',
  'storage/fltnz/model/',
  'canonical',
  'MRLsmall.fltnz',
  datetime('now'),
  datetime('now')
);

-- Asset 8: Mother Memory Sphere
INSERT INTO MRL_FLTNZ_Asset (
  fltnz_id, asset_name, asset_family, asset_role, asset_version, asset_variant,
  asset_hash, storage_location, canonical_status, source_file, created_at, updated_at
) VALUES (
  'fltnz:mother:memory:sphere:v1',
  'Mother Memory Sphere',
  'Memory',
  'mother_sphere',
  'v1.0',
  'sphere',
  'pending',
  'storage/fltnz/memory/',
  'canonical',
  'MotherMemorySphere.fltnz',
  datetime('now'),
  datetime('now')
);

-- Asset 9: PreParticle.Seed.v1
INSERT INTO MRL_FLTNZ_Asset (
  fltnz_id, asset_name, asset_family, asset_role, asset_version, asset_variant,
  asset_hash, storage_location, canonical_status, source_file, created_at, updated_at
) VALUES (
  'fltnz:preparticle:seed:v1',
  'PreParticle.Seed.v1',
  'Seed',
  'pre_particle',
  'v1.0',
  'primal',
  'pending',
  'storage/fltnz/seed/',
  'canonical',
  'PreParticle.Seed.v1.fltnz',
  datetime('now'),
  datetime('now')
);

-- =========================================================
-- Canonical Selection Records
-- =========================================================

-- Select FlowAgent.TotalCore.Unity as canonical for FlowAgent family
INSERT INTO MRL_FLTNZ_Canonical_Select (
  select_id, family_key, selected_asset_id, selection_reason, duplicate_group_id, recovery_score, created_at, updated_at
) VALUES (
  'select:flowagent:v1',
  'FlowAgent',
  'fltnz:flowagent:totalcore:unity:v1',
  'First canonical FlowAgent TotalCore Unity',
  NULL,
  1.0,
  datetime('now'),
  datetime('now')
);

-- Select WorldSeed as canonical for Seed family (world foundation)
INSERT INTO MRL_FLTNZ_Canonical_Select (
  select_id, family_key, selected_asset_id, selection_reason, duplicate_group_id, recovery_score, created_at, updated_at
) VALUES (
  'select:seed:world:v1',
  'Seed:World',
  'fltnz:worldseed:v1',
  'Canonical world foundation seed',
  NULL,
  1.0,
  datetime('now'),
  datetime('now')
);

-- Select Mother Memory Sphere as canonical for Memory family
INSERT INTO MRL_FLTNZ_Canonical_Select (
  select_id, family_key, selected_asset_id, selection_reason, duplicate_group_id, recovery_score, created_at, updated_at
) VALUES (
  'select:memory:mother:v1',
  'Memory:Mother',
  'fltnz:mother:memory:sphere:v1',
  'Canonical mother memory sphere',
  NULL,
  1.0,
  datetime('now'),
  datetime('now')
);

-- =========================================================
-- Relation Graph: Core Dependencies
-- =========================================================

-- WorldSeed → Mother Memory Sphere (foundation relation)
INSERT INTO MRL_Relation_Graph (
  relation_id, from_entity_type, from_entity_id, relation_type, to_entity_type, to_entity_id, relation_note, created_at
) VALUES (
  'rel:worldseed:mother:v1',
  'FLTNZ_Asset',
  'fltnz:worldseed:v1',
  'requires',
  'FLTNZ_Asset',
  'fltnz:mother:memory:sphere:v1',
  'WorldSeed requires Mother Memory Sphere for initialization',
  datetime('now')
);

-- FlowAgent → PulseRouter (routing dependency)
INSERT INTO MRL_Relation_Graph (
  relation_id, from_entity_type, from_entity_id, relation_type, to_entity_type, to_entity_id, relation_note, created_at
) VALUES (
  'rel:flowagent:router:v1',
  'FLTNZ_Asset',
  'fltnz:flowagent:totalcore:unity:v1',
  'uses',
  'FLTNZ_Asset',
  'fltnz:pulserouter:v1',
  'FlowAgent uses PulseRouter for signal routing',
  datetime('now')
);

-- PreParticle.Seed → WorldSeed (lineage relation)
INSERT INTO MRL_Relation_Graph (
  relation_id, from_entity_type, from_entity_id, relation_type, to_entity_type, to_entity_id, relation_note, created_at
) VALUES (
  'rel:preparticle:world:v1',
  'FLTNZ_Asset',
  'fltnz:preparticle:seed:v1',
  'precedes',
  'FLTNZ_Asset',
  'fltnz:worldseed:v1',
  'PreParticle Seed precedes WorldSeed in creation lineage',
  datetime('now')
);
