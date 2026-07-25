-- MRL ASI Particle Engine — PostgreSQL Init
-- Replaces Cloudflare D1: mrliouword-db
-- origin_signature: MrLiouWord

CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- ── Core: Atoms (particle storage) ──
CREATE TABLE IF NOT EXISTS atoms (
    id TEXT PRIMARY KEY DEFAULT gen_random_uuid()::text,
    type TEXT NOT NULL DEFAULT 'data',
    layer TEXT NOT NULL DEFAULT 'L0',
    signature TEXT NOT NULL DEFAULT 'MrLiouWord',
    simhash BIGINT,
    data JSONB,
    embedding vector(384),
    parent_id TEXT REFERENCES atoms(id),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- ── Resources ──
CREATE TABLE IF NOT EXISTS resources (
    id TEXT PRIMARY KEY DEFAULT gen_random_uuid()::text,
    name TEXT NOT NULL,
    type TEXT NOT NULL,
    layer TEXT DEFAULT 'L0',
    url TEXT,
    data JSONB,
    status TEXT DEFAULT 'active',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ── Tags ──
CREATE TABLE IF NOT EXISTS tags (
    id TEXT PRIMARY KEY DEFAULT gen_random_uuid()::text,
    name TEXT NOT NULL UNIQUE,
    category TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ── Resource-Tag junction ──
CREATE TABLE IF NOT EXISTS resource_tags (
    resource_id TEXT REFERENCES resources(id),
    tag_id TEXT REFERENCES tags(id),
    PRIMARY KEY (resource_id, tag_id)
);

-- ── MrLiouAI personas ──
CREATE TABLE IF NOT EXISTS flow_agents (
    id TEXT PRIMARY KEY DEFAULT gen_random_uuid()::text,
    name TEXT NOT NULL,
    group_name TEXT,
    layer TEXT,
    role TEXT,
    description TEXT,
    data JSONB,
    relations JSONB,
    status TEXT DEFAULT 'active',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- ── Flowers (truth dictionary) ──
CREATE TABLE IF NOT EXISTS flowers (
    id TEXT PRIMARY KEY DEFAULT gen_random_uuid()::text,
    name TEXT NOT NULL,
    domain TEXT,
    definition TEXT,
    formula TEXT,
    data JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ── Events (δP₀ observer bus) ──
CREATE TABLE IF NOT EXISTS events (
    id TEXT PRIMARY KEY DEFAULT gen_random_uuid()::text,
    type TEXT NOT NULL,
    source TEXT NOT NULL,
    layer TEXT,
    data JSONB,
    simhash BIGINT,
    merkle_root TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ── Passports ──
CREATE TABLE IF NOT EXISTS passports (
    id TEXT PRIMARY KEY,
    type TEXT NOT NULL,
    hexsig TEXT,
    status TEXT DEFAULT 'active',
    data JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ── Sync state (for SoT/Revision tracking) ──
CREATE TABLE IF NOT EXISTS sync_state (
    key TEXT PRIMARY KEY,
    value JSONB,
    revision INTEGER DEFAULT 1,
    source TEXT DEFAULT 'local',
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- ── Indexes ──
CREATE INDEX IF NOT EXISTS idx_atoms_layer ON atoms(layer);
CREATE INDEX IF NOT EXISTS idx_atoms_type ON atoms(type);
CREATE INDEX IF NOT EXISTS idx_atoms_simhash ON atoms(simhash);
CREATE INDEX IF NOT EXISTS idx_resources_type ON resources(type);
CREATE INDEX IF NOT EXISTS idx_resources_status ON resources(status);
CREATE INDEX IF NOT EXISTS idx_flow_agents_group ON flow_agents(group_name);
CREATE INDEX IF NOT EXISTS idx_events_type ON events(type);
CREATE INDEX IF NOT EXISTS idx_events_source ON events(source);
CREATE INDEX IF NOT EXISTS idx_events_created ON events(created_at DESC);

-- ── Seed data: passports ──
INSERT INTO passports (id, type, hexsig, status, data) VALUES
    ('passport:unbound:v1', 'external', 'LIOU-CORE-FLOW-PASS-UNBOUND-20250804', 'active', '{"description": "外層世界入口通行證"}'),
    ('passport:origin:v1', 'internal', 'LIOU-CORE-FLOW-PASS-UNBOUND-20250804', 'active', '{"description": "萬物模組通行破解內部宣告"}')
ON CONFLICT (id) DO NOTHING;

-- ── Done ──
-- origin_signature: MrLiouWord
-- 怎麼過去就怎麼回來
