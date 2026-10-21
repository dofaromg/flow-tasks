-- =========================================================
-- MRL_BaseWorld_DB_v1.sql
-- version: v1.0
-- owner: MrLiou / MRL System
-- purpose: BaseWorld canonical registry + fltnz asset layer
-- =========================================================

PRAGMA foreign_keys = ON;

-- =========================================================
-- 0. ROOT / LAW
-- =========================================================

CREATE TABLE IF NOT EXISTS MRL_Identity_Signature_Root (
    root_id TEXT PRIMARY KEY,
    origin_signature TEXT NOT NULL,
    authority_owner TEXT NOT NULL,
    naming_law_version TEXT,
    closure_law_version TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS MRL_Closure_Law_Root (
    law_id TEXT PRIMARY KEY,
    root_ref TEXT NOT NULL,
    observe_enabled INTEGER NOT NULL DEFAULT 1,
    resolve_enabled INTEGER NOT NULL DEFAULT 1,
    mirror_enabled INTEGER NOT NULL DEFAULT 1,
    verify_enabled INTEGER NOT NULL DEFAULT 1,
    loop_enabled INTEGER NOT NULL DEFAULT 1,
    authority_invariance INTEGER NOT NULL DEFAULT 1,
    no_delete_law INTEGER NOT NULL DEFAULT 1,
    additive_resolution INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY (root_ref) REFERENCES MRL_Identity_Signature_Root(root_id)
);

-- =========================================================
-- 1. CANON / SOURCE / CONFLICT
-- =========================================================

CREATE TABLE IF NOT EXISTS MRL_Canon_State (
    canon_state_id TEXT PRIMARY KEY,
    state_hash TEXT NOT NULL,
    state_version TEXT NOT NULL,
    state_class TEXT,
    resolve_status TEXT NOT NULL,
    conflict_count INTEGER NOT NULL DEFAULT 0,
    proof_status TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS MRL_Canon_Source (
    source_id TEXT PRIMARY KEY,
    canon_state_ref TEXT,
    source_type TEXT NOT NULL,
    source_name TEXT NOT NULL,
    source_locator TEXT,
    source_hash TEXT,
    source_priority INTEGER DEFAULT 0,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY (canon_state_ref) REFERENCES MRL_Canon_State(canon_state_id)
);

CREATE TABLE IF NOT EXISTS MRL_Canon_Conflict (
    conflict_id TEXT PRIMARY KEY,
    canon_state_ref TEXT NOT NULL,
    conflict_type TEXT NOT NULL,
    conflict_scope TEXT,
    repair_operator TEXT,
    repair_status TEXT NOT NULL,
    note TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY (canon_state_ref) REFERENCES MRL_Canon_State(canon_state_id)
);

-- =========================================================
-- 2. PACKAGE / QUARANTINE / VERIFY / INSTALL
-- =========================================================

CREATE TABLE IF NOT EXISTS MRL_Package_Quarantine (
    quarantine_id TEXT PRIMARY KEY,
    package_name TEXT NOT NULL,
    package_type TEXT NOT NULL,
    marker_slot TEXT,
    package_hash TEXT,
    ingest_status TEXT NOT NULL,
    source_file TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS MRL_Gate_Verifier (
    verification_id TEXT PRIMARY KEY,
    quarantine_ref TEXT NOT NULL,
    marker_slot_valid INTEGER NOT NULL DEFAULT 0,
    principle_valid INTEGER NOT NULL DEFAULT 0,
    required_fields_valid INTEGER NOT NULL DEFAULT 0,
    five_step_valid INTEGER NOT NULL DEFAULT 0,
    install_allowed INTEGER NOT NULL DEFAULT 0,
    verification_note TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY (quarantine_ref) REFERENCES MRL_Package_Quarantine(quarantine_id)
);

CREATE TABLE IF NOT EXISTS MRL_Install_Record (
    install_id TEXT PRIMARY KEY,
    package_ref TEXT NOT NULL,
    old_version TEXT,
    new_version TEXT,
    sandbox_entry TEXT,
    install_trace_id TEXT,
    install_status TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY (package_ref) REFERENCES MRL_Package_Quarantine(quarantine_id)
);

-- =========================================================
-- 3. MODULE REGISTRY / COMPOSER
-- =========================================================

CREATE TABLE IF NOT EXISTS MRL_Module_Registry (
    module_id TEXT PRIMARY KEY,
    module_name TEXT NOT NULL,
    module_layer TEXT,
    module_domain TEXT,
    entry_point TEXT,
    file_hash TEXT,
    capabilities TEXT,
    dependencies TEXT,
    module_status TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS MRL_Composer_Spec (
    spec_id TEXT PRIMARY KEY,
    intent_summary TEXT,
    required_capabilities TEXT,
    constraints_json TEXT,
    missing_fields TEXT,
    confidence REAL DEFAULT 0,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS MRL_Composer_Manifest (
    manifest_id TEXT PRIMARY KEY,
    spec_ref TEXT NOT NULL,
    selected_modules TEXT,
    dependency_closure TEXT,
    routing_plan TEXT,
    execution_plan TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY (spec_ref) REFERENCES MRL_Composer_Spec(spec_id)
);

-- =========================================================
-- 4. FLTNZ ASSET LAYER
-- =========================================================

CREATE TABLE IF NOT EXISTS MRL_FLTNZ_Asset (
    fltnz_id TEXT PRIMARY KEY,
    asset_name TEXT NOT NULL,
    asset_family TEXT NOT NULL,
    asset_role TEXT,
    asset_version TEXT,
    asset_variant TEXT,
    asset_hash TEXT,
    storage_location TEXT,
    canonical_status TEXT NOT NULL,
    source_file TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS MRL_FLTNZ_Lineage (
    lineage_id TEXT PRIMARY KEY,
    parent_asset_id TEXT,
    child_asset_id TEXT NOT NULL,
    relation_type TEXT NOT NULL,
    generation_order INTEGER DEFAULT 0,
    derivation_note TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY (parent_asset_id) REFERENCES MRL_FLTNZ_Asset(fltnz_id),
    FOREIGN KEY (child_asset_id) REFERENCES MRL_FLTNZ_Asset(fltnz_id)
);

CREATE TABLE IF NOT EXISTS MRL_FLTNZ_Manifest (
    manifest_id TEXT PRIMARY KEY,
    asset_ref TEXT NOT NULL,
    embedded_particles TEXT,
    embedded_structures TEXT,
    related_txt TEXT,
    related_zip TEXT,
    related_trace TEXT,
    related_map TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY (asset_ref) REFERENCES MRL_FLTNZ_Asset(fltnz_id)
);

CREATE TABLE IF NOT EXISTS MRL_FLTNZ_Canonical_Select (
    select_id TEXT PRIMARY KEY,
    family_key TEXT NOT NULL,
    selected_asset_id TEXT NOT NULL,
    selection_reason TEXT,
    duplicate_group_id TEXT,
    recovery_score REAL DEFAULT 0,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY (selected_asset_id) REFERENCES MRL_FLTNZ_Asset(fltnz_id)
);

-- =========================================================
-- 5. MOTHER MEMORY SPHERE
-- =========================================================

CREATE TABLE IF NOT EXISTS MRL_Structural_Memory (
    structural_memory_id TEXT PRIMARY KEY,
    canon_state_ref TEXT,
    memory_name TEXT NOT NULL,
    structure_type TEXT,
    structure_payload TEXT,
    status TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY (canon_state_ref) REFERENCES MRL_Canon_State(canon_state_id)
);

CREATE TABLE IF NOT EXISTS MRL_Particle_Memory (
    particle_memory_id TEXT PRIMARY KEY,
    fltnz_ref TEXT,
    reality_scope TEXT,
    layer_scope TEXT,
    jump_type TEXT,
    packet_hash TEXT,
    packet_payload TEXT,
    status TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY (fltnz_ref) REFERENCES MRL_FLTNZ_Asset(fltnz_id)
);

CREATE TABLE IF NOT EXISTS MRL_PersonaField_Rhythm (
    persona_rhythm_id TEXT PRIMARY KEY,
    module_ref TEXT,
    persona_name TEXT NOT NULL,
    rhythm_type TEXT,
    anchor_key TEXT,
    resonance_payload TEXT,
    status TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY (module_ref) REFERENCES MRL_Module_Registry(module_id)
);

-- =========================================================
-- 6. MIRROR / PROOF / TRACE
-- =========================================================

CREATE TABLE IF NOT EXISTS MRL_Mirror_Record (
    mirror_id TEXT PRIMARY KEY,
    canon_state_ref TEXT NOT NULL,
    projection_target TEXT,
    projection_hash TEXT,
    mirror_status TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY (canon_state_ref) REFERENCES MRL_Canon_State(canon_state_id)
);

CREATE TABLE IF NOT EXISTS MRL_Proof_Merkle (
    proof_id TEXT PRIMARY KEY,
    mirror_ref TEXT,
    merkle_root TEXT,
    proof_payload TEXT,
    proof_status TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY (mirror_ref) REFERENCES MRL_Mirror_Record(mirror_id)
);

CREATE TABLE IF NOT EXISTS MRL_Trace_Log (
    trace_id TEXT PRIMARY KEY,
    trace_type TEXT NOT NULL,
    trace_scope TEXT,
    related_entity_type TEXT,
    related_entity_id TEXT,
    event_payload TEXT,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS MRL_Fork_Branch (
    branch_id TEXT PRIMARY KEY,
    source_trace_ref TEXT,
    branch_name TEXT NOT NULL,
    branch_status TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY (source_trace_ref) REFERENCES MRL_Trace_Log(trace_id)
);

CREATE TABLE IF NOT EXISTS MRL_Collapse_Record (
    collapse_id TEXT PRIMARY KEY,
    branch_ref TEXT NOT NULL,
    target_canon_state_ref TEXT,
    collapse_reason TEXT,
    collapse_status TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY (branch_ref) REFERENCES MRL_Fork_Branch(branch_id),
    FOREIGN KEY (target_canon_state_ref) REFERENCES MRL_Canon_State(canon_state_id)
);

-- =========================================================
-- 7. LIBRARIAN / RELATION / RECOVERY
-- =========================================================

CREATE TABLE IF NOT EXISTS MRL_File_Index (
    file_index_id TEXT PRIMARY KEY,
    file_name TEXT NOT NULL,
    file_type TEXT,
    file_hash TEXT,
    source_locator TEXT,
    canonical_ref_type TEXT,
    canonical_ref_id TEXT,
    file_status TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS MRL_Relation_Graph (
    relation_id TEXT PRIMARY KEY,
    from_entity_type TEXT NOT NULL,
    from_entity_id TEXT NOT NULL,
    relation_type TEXT NOT NULL,
    to_entity_type TEXT NOT NULL,
    to_entity_id TEXT NOT NULL,
    relation_note TEXT,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS MRL_Recovery_Plan (
    recovery_plan_id TEXT PRIMARY KEY,
    plan_name TEXT NOT NULL,
    target_scope TEXT,
    minimal_seed_set TEXT,
    restore_path TEXT,
    recovery_status TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS MRL_Cleanup_Decision (
    cleanup_id TEXT PRIMARY KEY,
    file_index_ref TEXT,
    cleanup_action TEXT NOT NULL,
    cleanup_reason TEXT,
    recovery_safe INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY (file_index_ref) REFERENCES MRL_File_Index(file_index_id)
);

-- =========================================================
-- 8. BASE INDEXES
-- =========================================================

CREATE INDEX IF NOT EXISTS idx_canon_state_hash ON MRL_Canon_State(state_hash);
CREATE INDEX IF NOT EXISTS idx_fltnz_family ON MRL_FLTNZ_Asset(asset_family);
CREATE INDEX IF NOT EXISTS idx_fltnz_hash ON MRL_FLTNZ_Asset(asset_hash);
CREATE INDEX IF NOT EXISTS idx_particle_reality_scope ON MRL_Particle_Memory(reality_scope);
CREATE INDEX IF NOT EXISTS idx_relation_from ON MRL_Relation_Graph(from_entity_type, from_entity_id);
CREATE INDEX IF NOT EXISTS idx_relation_to ON MRL_Relation_Graph(to_entity_type, to_entity_id);
CREATE INDEX IF NOT EXISTS idx_file_hash ON MRL_File_Index(file_hash);
CREATE INDEX IF NOT EXISTS idx_trace_related ON MRL_Trace_Log(related_entity_type, related_entity_id);
