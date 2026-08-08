-- ============================================================================
--  00_MRL_BaseWorld_DB_v1.sql
--  origin_signature: MrLiouWord
--  歸屬: MRL母體工程架構中心
--  分支: MRL_Branch_06_BaseWorld_DB_Deploy_DL580
--  版本: v1.0
--  內容: 27 tables + 8 indexes
--
--  三基層: MRL_Origin / MRL_State / MRL_Projection
--  怎麼過去，就怎麼回來
-- ============================================================================

-- 啟用擴展
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- ═══════════════════════════════════════════════════════════════
-- 第一組：三基層（Origin / State / Projection）
-- ═══════════════════════════════════════════════════════════════

-- T01: 起源層
CREATE TABLE mrl_origin (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    origin_key      TEXT NOT NULL UNIQUE,
    origin_type     TEXT NOT NULL DEFAULT 'seed',
    payload         JSONB NOT NULL DEFAULT '{}',
    simhash64       TEXT,
    reversible      BOOLEAN NOT NULL DEFAULT TRUE,
    frozen          BOOLEAN NOT NULL DEFAULT FALSE,
    origin_signature TEXT NOT NULL DEFAULT 'MrLiouWord',
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- T02: 現行狀態層
CREATE TABLE mrl_state (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    state_key       TEXT NOT NULL UNIQUE,
    state_type      TEXT NOT NULL DEFAULT 'active',
    origin_id       UUID REFERENCES mrl_origin(id),
    payload         JSONB NOT NULL DEFAULT '{}',
    observable      BOOLEAN NOT NULL DEFAULT TRUE,
    verifiable      BOOLEAN NOT NULL DEFAULT TRUE,
    origin_signature TEXT NOT NULL DEFAULT 'MrLiouWord',
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- T03: 投影生成層
CREATE TABLE mrl_projection (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    projection_key  TEXT NOT NULL UNIQUE,
    projection_type TEXT NOT NULL DEFAULT 'pending',
    origin_id       UUID REFERENCES mrl_origin(id),
    state_id        UUID REFERENCES mrl_state(id),
    payload         JSONB NOT NULL DEFAULT '{}',
    branch_tag      TEXT,
    can_generate    BOOLEAN NOT NULL DEFAULT TRUE,
    can_branch      BOOLEAN NOT NULL DEFAULT TRUE,
    origin_signature TEXT NOT NULL DEFAULT 'MrLiouWord',
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ═══════════════════════════════════════════════════════════════
-- 第二組：控制中心與世界模組
-- ═══════════════════════════════════════════════════════════════

-- T04: 控制中心（唯一入口）
CREATE TABLE mrl_control_center (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    module_name     TEXT NOT NULL UNIQUE,
    module_type     TEXT NOT NULL,
    entry_point     TEXT,
    status          TEXT NOT NULL DEFAULT 'registered',
    layer           TEXT NOT NULL DEFAULT 'MRL_State',
    payload         JSONB NOT NULL DEFAULT '{}',
    origin_signature TEXT NOT NULL DEFAULT 'MrLiouWord',
    registered_at   TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- T05: 世界模組
CREATE TABLE mrl_world_module (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    module_name     TEXT NOT NULL UNIQUE,
    entry           TEXT NOT NULL,
    structure       JSONB NOT NULL DEFAULT '{}',
    interaction     JSONB NOT NULL DEFAULT '{}',
    data_flow       JSONB NOT NULL DEFAULT '{}',
    execution       JSONB NOT NULL DEFAULT '{}',
    control_id      UUID REFERENCES mrl_control_center(id),
    status          TEXT NOT NULL DEFAULT 'active',
    origin_signature TEXT NOT NULL DEFAULT 'MrLiouWord',
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ═══════════════════════════════════════════════════════════════
-- 第三組：粒子崩塌引擎核心
-- ═══════════════════════════════════════════════════════════════

-- T06: 人格
CREATE TABLE mrl_persona (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    persona_key     TEXT NOT NULL UNIQUE,
    persona_type    TEXT NOT NULL DEFAULT 'Observer',
    state           TEXT NOT NULL DEFAULT 'active',
    parent_id       UUID REFERENCES mrl_persona(id),
    children        UUID[] DEFAULT '{}',
    consistency_key TEXT,
    simhash64       TEXT,
    payload         JSONB NOT NULL DEFAULT '{}',
    origin_signature TEXT NOT NULL DEFAULT 'MrLiouWord',
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    last_active     TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- T07: 記憶體（.fltnz 格式）
CREATE TABLE mrl_memory (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    memory_key      TEXT NOT NULL UNIQUE,
    format          TEXT NOT NULL DEFAULT '.fltnz',
    version         TEXT NOT NULL DEFAULT 'v2',
    persona_id      UUID REFERENCES mrl_persona(id),
    persona_type    TEXT,
    jump_count      INTEGER DEFAULT 0,
    compressed      BOOLEAN NOT NULL DEFAULT FALSE,
    simhash64       TEXT,
    scan_session    JSONB,
    signature_hash  TEXT NOT NULL DEFAULT 'MRSIG-FULLSTACK-LOGIC-SEED-X93D1F',
    origin_signature TEXT NOT NULL DEFAULT 'MrLiouWord',
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- T08: 粒子
CREATE TABLE mrl_particle (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    particle_key    TEXT NOT NULL UNIQUE,
    particle_type   TEXT NOT NULL,
    frequency       DOUBLE PRECISION NOT NULL DEFAULT 7.83,
    resonance       DOUBLE PRECISION DEFAULT 1.0,
    layer           INTEGER DEFAULT 0,
    payload         JSONB NOT NULL DEFAULT '{}',
    origin_signature TEXT NOT NULL DEFAULT 'MrLiouWord',
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- T09: 節奏跳點
CREATE TABLE mrl_jump_point (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    jump_key        TEXT NOT NULL UNIQUE,
    jump_type       TEXT NOT NULL DEFAULT 'observe',
    frequency       DOUBLE PRECISION NOT NULL DEFAULT 7.83,
    resonance       DOUBLE PRECISION DEFAULT 1.0,
    data            JSONB NOT NULL DEFAULT '{}',
    origin_signature TEXT NOT NULL DEFAULT 'MrLiouWord',
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- T10: 靜止態
CREATE TABLE mrl_stasis (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    stasis_key      TEXT NOT NULL UNIQUE,
    entropy         DOUBLE PRECISION,
    is_static       BOOLEAN NOT NULL DEFAULT FALSE,
    simhash64       TEXT,
    jump_point_id   UUID REFERENCES mrl_jump_point(id),
    payload         JSONB NOT NULL DEFAULT '{}',
    origin_signature TEXT NOT NULL DEFAULT 'MrLiouWord',
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ═══════════════════════════════════════════════════════════════
-- 第四組：簽名與通行證
-- ═══════════════════════════════════════════════════════════════

-- T11: 簽名紀錄
CREATE TABLE mrl_signature (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    entity_type     TEXT NOT NULL,
    entity_id       UUID NOT NULL,
    layer           INTEGER NOT NULL DEFAULT 0,
    signature_value TEXT NOT NULL DEFAULT 'MrLiouWord',
    enhanced        TEXT,
    valid           BOOLEAN NOT NULL DEFAULT TRUE,
    verified_at     TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    origin_signature TEXT NOT NULL DEFAULT 'MrLiouWord'
);

-- T12: 系統通行證
CREATE TABLE mrl_passport_system (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    hexsig          TEXT NOT NULL UNIQUE,
    issuer          TEXT NOT NULL DEFAULT 'MrLiouWord.System',
    source_type     TEXT NOT NULL DEFAULT 'system',
    permissions     TEXT[] NOT NULL DEFAULT '{}',
    active          BOOLEAN NOT NULL DEFAULT TRUE,
    origin_signature TEXT NOT NULL DEFAULT 'MrLiouWord',
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- T13: 用戶通行證
CREATE TABLE mrl_passport_user (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    hexsig          TEXT NOT NULL UNIQUE,
    user_id         TEXT NOT NULL,
    issuer          TEXT NOT NULL DEFAULT 'Mr.Liou',
    source_type     TEXT NOT NULL DEFAULT 'user',
    permissions     TEXT[] NOT NULL DEFAULT '{}',
    active          BOOLEAN NOT NULL DEFAULT TRUE,
    origin_signature TEXT NOT NULL DEFAULT 'MrLiouWord',
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ═══════════════════════════════════════════════════════════════
-- 第五組：壓縮/還原/掃描
-- ═══════════════════════════════════════════════════════════════

-- T14: 種子（壓縮態）
CREATE TABLE mrl_seed (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    seed_key        TEXT NOT NULL UNIQUE,
    format          TEXT NOT NULL DEFAULT '.flseed',
    memory_id       UUID REFERENCES mrl_memory(id),
    genesis         JSONB NOT NULL DEFAULT '{}',
    magnitude       INTEGER DEFAULT 0,
    compressed      BOOLEAN NOT NULL DEFAULT TRUE,
    reversible      BOOLEAN NOT NULL DEFAULT TRUE,
    loss_model      JSONB,
    origin_signature TEXT NOT NULL DEFAULT 'MrLiouWord',
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- T15: 掃描會話
CREATE TABLE mrl_scan_session (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_key     TEXT NOT NULL UNIQUE,
    status          TEXT NOT NULL DEFAULT 'active',
    start_time      BIGINT NOT NULL,
    end_time        BIGINT,
    duration        BIGINT,
    frames          INTEGER NOT NULL DEFAULT 0,
    quality_sum     DOUBLE PRECISION DEFAULT 0,
    quality_count   INTEGER DEFAULT 0,
    quality_average DOUBLE PRECISION DEFAULT 0,
    metadata        JSONB NOT NULL DEFAULT '{}',
    collapse_persona_id UUID REFERENCES mrl_persona(id),
    collapse_memory_id  UUID REFERENCES mrl_memory(id),
    origin_signature TEXT NOT NULL DEFAULT 'MrLiouWord',
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ═══════════════════════════════════════════════════════════════
-- 第六組：MetaEnv 控制
-- ═══════════════════════════════════════════════════════════════

-- T16: MetaEnv 環境
CREATE TABLE mrl_metaenv (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    env_id          TEXT NOT NULL UNIQUE,
    role            TEXT NOT NULL DEFAULT 'core',
    shape           JSONB,
    policy          TEXT,
    status          TEXT NOT NULL DEFAULT 'starting',
    origin_signature TEXT NOT NULL DEFAULT 'MrLiouWord',
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- T17: Guard.v1 策略
CREATE TABLE mrl_policy (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    env_id          TEXT NOT NULL,
    policy_name     TEXT NOT NULL,
    policy_body     JSONB NOT NULL DEFAULT '{}',
    applied_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    origin_signature TEXT NOT NULL DEFAULT 'MrLiouWord'
);

-- T18: 快照
CREATE TABLE mrl_snapshot (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    snapshot_key    TEXT NOT NULL UNIQUE,
    env_id          TEXT NOT NULL,
    encrypted       BOOLEAN NOT NULL DEFAULT TRUE,
    exportable      BOOLEAN NOT NULL DEFAULT FALSE,
    label           TEXT,
    payload         JSONB NOT NULL DEFAULT '{}',
    origin_signature TEXT NOT NULL DEFAULT 'MrLiouWord',
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- T19: 通道地圖
CREATE TABLE mrl_channel_map (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    revert_token    TEXT NOT NULL UNIQUE,
    app             TEXT NOT NULL,
    mode            TEXT NOT NULL DEFAULT 'dry-run',
    from_path       TEXT,
    to_path         TEXT NOT NULL,
    changes         TEXT[] DEFAULT '{}',
    origin_signature TEXT NOT NULL DEFAULT 'MrLiouWord',
    executed_at     TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- T20: 鎖死紀錄
CREATE TABLE mrl_lockdown_log (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    reason          TEXT,
    scope           TEXT NOT NULL DEFAULT 'env',
    env_id          TEXT,
    actions         TEXT[] DEFAULT '{}',
    origin_signature TEXT NOT NULL DEFAULT 'MrLiouWord',
    executed_at     TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- T21: 回溯報告
CREATE TABLE mrl_backtrace_log (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    backtrace_key   TEXT NOT NULL UNIQUE,
    report          JSONB NOT NULL DEFAULT '{}',
    origin_signature TEXT NOT NULL DEFAULT 'MrLiouWord',
    received_at     TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ═══════════════════════════════════════════════════════════════
-- 第七組：跨維度同步與審計
-- ═══════════════════════════════════════════════════════════════

-- T22: 跨維度同步紀錄
CREATE TABLE mrl_dimension_sync (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    entity_id       UUID NOT NULL,
    sync_pair       TEXT NOT NULL,
    pair_name       TEXT,
    pair_type       TEXT,
    from_valid      BOOLEAN DEFAULT FALSE,
    to_valid        BOOLEAN DEFAULT FALSE,
    synced          BOOLEAN DEFAULT FALSE,
    origin_signature TEXT NOT NULL DEFAULT 'MrLiouWord',
    synced_at       TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- T23: 審計日誌
CREATE TABLE mrl_audit_log (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    operation       TEXT NOT NULL,
    entity_type     TEXT,
    entity_id       UUID,
    input_hash      TEXT,
    layers          TEXT[] DEFAULT '{}',
    elapsed_ms      INTEGER,
    detail          JSONB NOT NULL DEFAULT '{}',
    origin_signature TEXT NOT NULL DEFAULT 'MrLiouWord',
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ═══════════════════════════════════════════════════════════════
-- 第八組：Closure Law / FX Registry / FLTNZ Asset / Relation
-- ═══════════════════════════════════════════════════════════════

-- T24: 三大不可違反律
CREATE TABLE mrl_closure_law (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    law_name        TEXT NOT NULL UNIQUE,
    law_key         TEXT NOT NULL UNIQUE,
    description     TEXT NOT NULL,
    enforced        BOOLEAN NOT NULL DEFAULT TRUE,
    origin_signature TEXT NOT NULL DEFAULT 'MrLiouWord',
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- T25: 17 FX 粒子註冊表
CREATE TABLE mrl_fx_registry (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    fx_number       TEXT NOT NULL UNIQUE,
    fx_name         TEXT NOT NULL,
    description     TEXT,
    execute_spec    JSONB NOT NULL DEFAULT '{}',
    validate_spec   JSONB NOT NULL DEFAULT '{}',
    status          TEXT NOT NULL DEFAULT 'registered',
    origin_signature TEXT NOT NULL DEFAULT 'MrLiouWord',
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- T26: FLTNZ 資產
CREATE TABLE mrl_fltnz_asset (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    asset_key       TEXT NOT NULL UNIQUE,
    asset_name      TEXT NOT NULL,
    category        TEXT NOT NULL,
    format          TEXT NOT NULL DEFAULT '.fltnz',
    version         TEXT NOT NULL DEFAULT 'v1',
    payload         JSONB NOT NULL DEFAULT '{}',
    simhash64       TEXT,
    layer           INTEGER DEFAULT 0,
    origin_signature TEXT NOT NULL DEFAULT 'MrLiouWord',
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- T27: 關聯
CREATE TABLE mrl_relation (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    from_type       TEXT NOT NULL,
    from_id         UUID NOT NULL,
    to_type         TEXT NOT NULL,
    to_id           UUID NOT NULL,
    relation_type   TEXT NOT NULL DEFAULT 'link',
    weight          DOUBLE PRECISION DEFAULT 1.0,
    metadata        JSONB NOT NULL DEFAULT '{}',
    origin_signature TEXT NOT NULL DEFAULT 'MrLiouWord',
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ═══════════════════════════════════════════════════════════════
-- 索引（8 個）
-- ═══════════════════════════════════════════════════════════════

CREATE INDEX idx_persona_type ON mrl_persona(persona_type);
CREATE INDEX idx_memory_persona_id ON mrl_memory(persona_id);
CREATE INDEX idx_particle_type ON mrl_particle(particle_type);
CREATE INDEX idx_jump_point_type ON mrl_jump_point(jump_type);
CREATE INDEX idx_audit_operation ON mrl_audit_log(operation);
CREATE INDEX idx_metaenv_status ON mrl_metaenv(status);
CREATE INDEX idx_fltnz_asset_category ON mrl_fltnz_asset(category);
CREATE INDEX idx_scan_session_status ON mrl_scan_session(status);

-- ═══════════════════════════════════════════════════════════════
-- 完成
-- ═══════════════════════════════════════════════════════════════

-- 驗證: SELECT count(*) FROM information_schema.tables WHERE table_schema = 'public';
-- 預期: 27
-- 驗證: SELECT count(*) FROM pg_indexes WHERE schemaname = 'public' AND indexname LIKE 'idx_%';
-- 預期: 8
