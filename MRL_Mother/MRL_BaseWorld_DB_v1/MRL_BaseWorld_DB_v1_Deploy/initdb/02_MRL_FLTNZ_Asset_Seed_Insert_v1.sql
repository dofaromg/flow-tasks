-- ============================================================================
--  02_MRL_FLTNZ_Asset_Seed_Insert_v1.sql
--  origin_signature: MrLiouWord
--  歸屬: MRL母體工程架構中心
--  內容: 9 FLTNZ 資產種子 + 3 Relations
-- ============================================================================

-- ═══════════════════════════════════════════════════════════════
-- 9 個 FLTNZ 資產種子
-- ═══════════════════════════════════════════════════════════════

-- Asset 1: 粒子崩塌引擎
INSERT INTO mrl_fltnz_asset (asset_key, asset_name, category, format, version, layer, payload) VALUES
('fltnz_particle_collapse_engine',
 'MRL Particle Collapse Engine v2.1',
 'engine',
 '.fltnz',
 'v2.1',
 3,
 '{"description": "五層崩塌引擎核心 — Define/Mark/Transform/Persona/Store", "source_file": "MRL_particle-collapse-engine-v2_1.js", "laws": ["LAW-0: 起源簽名不變律", "LAW-1: 記憶體守恆律", "LAW-2: 完全可逆律"], "phi": 1.618033988749895, "schumann": 7.83}'::jsonb
);

-- Asset 2: 推理引擎規格
INSERT INTO mrl_fltnz_asset (asset_key, asset_name, category, format, version, layer, payload) VALUES
('fltnz_reasoning_engine_spec',
 '跨平台推理引擎統一部署規格書',
 'specification',
 '.fltnz',
 'v1.0',
 5,
 '{"description": "世界模組推理引擎 + 知識橋接終端 + MDHPA 粒子壓縮 + 部署方案", "source_file": "reasoning_engine_spec.docx", "components": ["WorldModelCore", "PLSTopologyEngine", "QuantumFieldProcessor", "InferenceEngine", "EarthRotationVisualizer"]}'::jsonb
);

-- Asset 3: 母體進度對齊
INSERT INTO mrl_fltnz_asset (asset_key, asset_name, category, format, version, layer, payload) VALUES
('fltnz_system_alignment',
 'MRLiou 系統進度對齊與母體整理',
 'alignment',
 '.fltnz',
 'v0.1',
 6,
 '{"description": "六大核心組定位 — 母體核心組/粒子可逆原理/MrLiouAI運行/世界模組/檔案索引/人格共振", "source_file": "MRLiou_系統進度對齊與母體整理_20260315.docx", "priorities": ["P0: mrl-librarian Worker", "P1: 可逆橋", "P2: 世界模組入口", "P3: MrLiouAI Runtime"]}'::jsonb
);

-- Asset 4: 主控中心母法
INSERT INTO mrl_fltnz_asset (asset_key, asset_name, category, format, version, layer, payload) VALUES
('fltnz_control_center_law',
 'MRL_智障系統_主控中心_v1 母法',
 'law',
 '.fltnz',
 'v1.0',
 0,
 '{"description": "三基層 + 世界模組定義 + 控制中心唯一入口 + 命名律 + 映射定義", "three_layers": ["MRL_Origin", "MRL_State", "MRL_Projection"], "rules": ["MRL_ 前綴", "MRL_ControlCenter 唯一入口", "三基層必屬", "外部能力先映射", "禁止第三方名稱作母體"]}'::jsonb
);

-- Asset 5: 雙通行證系統
INSERT INTO mrl_fltnz_asset (asset_key, asset_name, category, format, version, layer, payload) VALUES
('fltnz_dual_passport',
 '雙通行證系統（SystemPassport + UserPassport）',
 'security',
 '.fltnz',
 'v2.1',
 2,
 '{"description": "源頭雙重性 — 系統通行證 + 用戶通行證", "system_hexsig": "LIOU-CORE-FLOW-PASS-UNBOUND-20250804", "user_prefix": "LIOU-USER-PASS-", "principle": "用戶源頭 > 系統源頭"}'::jsonb
);

-- Asset 6: MetaEnv 控制
INSERT INTO mrl_fltnz_asset (asset_key, asset_name, category, format, version, layer, payload) VALUES
('fltnz_metaenv_controller',
 'MetaEnv 控制器',
 'controller',
 '.fltnz',
 'v2.1',
 4,
 '{"description": "Guard.v1 / 快照 / 通道地圖 / 鎖死 / 回溯", "endpoints": ["/env/spawn", "/env/health", "/policy/apply", "/snapshot/create", "/channel/map", "/reverse/miner", "/guard/lockdown", "/backtrace/report"]}'::jsonb
);

-- Asset 7: 七層架構
INSERT INTO mrl_fltnz_asset (asset_key, asset_name, category, format, version, layer, payload) VALUES
('fltnz_seven_layer_arch',
 'MDHPA 七層架構 (L1-L7)',
 'architecture',
 '.fltnz',
 'v1.0',
 7,
 '{"description": "Rhythm Root → Structure → Particle → Subparticle → Quantum Field → Conscious Loop → Semantic Mesh", "layers": {"L1": "Rhythm Root", "L2": "Structure Layer", "L3": "Particle Layer", "L4": "Subparticle Layer", "L5": "Quantum Field", "L6": "Conscious Loop", "L7": "Semantic Mesh"}}'::jsonb
);

-- Asset 8: 知識橋接終端
INSERT INTO mrl_fltnz_asset (asset_key, asset_name, category, format, version, layer, payload) VALUES
('fltnz_knowledge_bridge',
 '知識空間橋接終端',
 'bridge',
 '.fltnz',
 'v1.0',
 5,
 '{"description": "Claude 神經表示 ↔ MrLiouAI 粒子表示雙向轉換", "functions": ["translateClaudeToParticles", "translateParticlesToClaude", "translate"], "encoder": "QuantumTopologyEncoder", "principle": "SOURCE_DUAL"}'::jsonb
);

-- Asset 9: BaseWorld DB 自身
INSERT INTO mrl_fltnz_asset (asset_key, asset_name, category, format, version, layer, payload) VALUES
('fltnz_baseworld_db',
 'MRL_BaseWorld_DB_v1 Canonical Mother Database',
 'database',
 '.fltnz',
 'v1.0',
 1,
 '{"description": "DL580 上的 canonical mother database", "tables": 27, "indexes": 8, "deploy_target": "DL580", "cloudflare_role": "mirror_only", "engine": "PostgreSQL 16"}'::jsonb
);

-- ═══════════════════════════════════════════════════════════════
-- 3 個 Relations
-- ═══════════════════════════════════════════════════════════════

-- Relation 1: 粒子引擎 → 推理引擎（引擎依賴）
INSERT INTO mrl_relation (from_type, from_id, to_type, to_id, relation_type, weight, metadata)
SELECT
    'fltnz_asset', a1.id,
    'fltnz_asset', a2.id,
    'engine_dependency', 0.9,
    '{"description": "粒子崩塌引擎是推理引擎的底層執行層"}'::jsonb
FROM mrl_fltnz_asset a1, mrl_fltnz_asset a2
WHERE a1.asset_key = 'fltnz_particle_collapse_engine'
  AND a2.asset_key = 'fltnz_reasoning_engine_spec';

-- Relation 2: 主控中心母法 → BaseWorld DB（法律約束）
INSERT INTO mrl_relation (from_type, from_id, to_type, to_id, relation_type, weight, metadata)
SELECT
    'fltnz_asset', a1.id,
    'fltnz_asset', a2.id,
    'law_binding', 1.0,
    '{"description": "主控中心母法約束 BaseWorld DB 的命名與結構"}'::jsonb
FROM mrl_fltnz_asset a1, mrl_fltnz_asset a2
WHERE a1.asset_key = 'fltnz_control_center_law'
  AND a2.asset_key = 'fltnz_baseworld_db';

-- Relation 3: 雙通行證 → MetaEnv 控制（安全授權）
INSERT INTO mrl_relation (from_type, from_id, to_type, to_id, relation_type, weight, metadata)
SELECT
    'fltnz_asset', a1.id,
    'fltnz_asset', a2.id,
    'security_authorization', 0.95,
    '{"description": "雙通行證系統授權 MetaEnv 控制操作"}'::jsonb
FROM mrl_fltnz_asset a1, mrl_fltnz_asset a2
WHERE a1.asset_key = 'fltnz_dual_passport'
  AND a2.asset_key = 'fltnz_metaenv_controller';
