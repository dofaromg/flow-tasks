-- ============================================================================
--  01_MRL_BaseWorld_DB_v1_Init.sql
--  origin_signature: MrLiouWord
--  歸屬: MRL母體工程架構中心
--  內容: ROOT 記錄 + Closure Law + 系統通行證 + 17 FX 註冊 + 控制中心 ROOT
-- ============================================================================

-- ═══════════════════════════════════════════════════════════════
-- 1. Origin ROOT 記錄
-- ═══════════════════════════════════════════════════════════════

INSERT INTO mrl_origin (origin_key, origin_type, payload, reversible, frozen, origin_signature)
VALUES (
    'ROOT',
    'absolute_origin',
    '{"description": "MRL系統絕對原點", "creator": "MrLiou", "role": "CEO / 創辦人 / 最終裁定", "principle": "怎麼過去，就怎麼回來", "engine": "MRL Particle Collapse Engine v2.1", "phi": 1.618033988749895, "schumann": 7.83}'::jsonb,
    TRUE,
    FALSE,
    'MrLiouWord'
);

-- ═══════════════════════════════════════════════════════════════
-- 2. 三大不可違反律（Closure Law）
-- ═══════════════════════════════════════════════════════════════

INSERT INTO mrl_closure_law (law_name, law_key, description, enforced) VALUES
('Authority Invariance', 'AUTHORITY_INVARIANCE', 'ROOT 不可被轉移、代理、隱藏', TRUE),
('No Delete',            'NO_DELETE',            '任何刪除都是對衝突的掩蓋，不構成解決', TRUE),
('Additive Resolution',  'ADDITIVE_RESOLUTION',  '所有修正必須以堆疊方式保留歷史', TRUE);

-- ═══════════════════════════════════════════════════════════════
-- 3. 系統通行證
-- ═══════════════════════════════════════════════════════════════

INSERT INTO mrl_passport_system (hexsig, issuer, source_type, permissions, active)
VALUES (
    'LIOU-CORE-FLOW-PASS-UNBOUND-20250804',
    'MrLiouWord.System',
    'system',
    ARRAY['jump_point_bypass', 'module_resonance_sync', 'persona_switch_approve', 'cross_layer_traverse', 'metaenv_control', 'snapshot_create', 'lockdown_execute', 'internal_rpc'],
    TRUE
);

-- ═══════════════════════════════════════════════════════════════
-- 4. 控制中心 ROOT 模組
-- ═══════════════════════════════════════════════════════════════

INSERT INTO mrl_control_center (module_name, module_type, entry_point, status, layer, payload)
VALUES (
    'MRL_ControlCenter',
    'root_controller',
    'MRL_ControlCenter.run()',
    'active',
    'MRL_State',
    '{"description": "唯一合法入口，所有模組註冊、資料流轉、執行與回寫都必須經過此處", "rules": ["所有最終模組必須 MRL_ 前綴", "所有世界模組必須註冊到 MRL_ControlCenter", "所有執行必須經過 MRL_ControlCenter.run()", "所有資料必須落在三基層之一", "所有外部能力必須先映射成 MRL_ 模組", "禁止第三方名稱直接作為最終母體名稱"]}'::jsonb
);

-- ═══════════════════════════════════════════════════════════════
-- 5. 世界模組映射（初始 5 模組）
-- ═══════════════════════════════════════════════════════════════

INSERT INTO mrl_world_module (module_name, entry, structure, interaction, data_flow, execution, status) VALUES
('MRL_World_Workbench',    '/workbench',    '{"source": "Claude Artifacts"}'::jsonb,    '{}'::jsonb, '{}'::jsonb, '{}'::jsonb, 'registered'),
('MRL_World_Chat',         '/chat',         '{"source": "Chat 對話"}'::jsonb,           '{}'::jsonb, '{}'::jsonb, '{}'::jsonb, 'registered'),
('MRL_World_Knowledge',    '/knowledge',    '{"source": "Notion 頁面/資料庫"}'::jsonb,  '{}'::jsonb, '{}'::jsonb, '{}'::jsonb, 'registered'),
('MRL_World_Research',     '/research',     '{"source": "搜尋/引用"}'::jsonb,           '{}'::jsonb, '{}'::jsonb, '{}'::jsonb, 'registered'),
('MRL_World_SystemAssist', '/system-assist','{"source": "系統整合"}'::jsonb,             '{}'::jsonb, '{}'::jsonb, '{}'::jsonb, 'registered');

-- ═══════════════════════════════════════════════════════════════
-- 6. 17 FX 粒子註冊表
-- ═══════════════════════════════════════════════════════════════

INSERT INTO mrl_fx_registry (fx_number, fx_name, description, status) VALUES
('fx01', 'Identity',  '身份識別與認證',       'registered'),
('fx02', 'Data',      '數據處理與轉換',       'registered'),
('fx03', 'Reference', '引用解析與鏈接',       'registered'),
('fx04', 'Compute',   '運算與推理執行',       'registered'),
('fx05', 'Storage',   '存儲與檢索',           'registered'),
('fx06', 'Network',   '網絡通訊與路由',       'registered'),
('fx07', 'Security',  '安全驗證與加密',       'registered'),
('fx08', 'Transform', '格式轉換與映射',       'registered'),
('fx09', 'Validate',  '輸入驗證與檢查',       'registered'),
('fx10', 'Route',     '路由決策與分發',       'registered'),
('fx11', 'Cache',     '快取管理與優化',       'registered'),
('fx12', 'Queue',     '佇列處理與排程',       'registered'),
('fx13', 'Event',     '事件觸發與處理',       'registered'),
('fx14', 'State',     '狀態管理與追蹤',       'registered'),
('fx15', 'Config',    '配置管理與動態調整',   'registered'),
('fx16', 'Log',       '日誌記錄與分析',       'registered'),
('fx17', 'Meta',      '元數據管理與內省',     'registered');

-- ═══════════════════════════════════════════════════════════════
-- 7. 顯化分支註冊
-- ═══════════════════════════════════════════════════════════════

INSERT INTO mrl_control_center (module_name, module_type, entry_point, status, layer, payload) VALUES
('MRL_Desktop_Branch', 'deploy_branch', '/desktop', 'registered', 'MRL_Projection', '{"note": "顯化部署分支，不是母體本體"}'::jsonb),
('MRL_Web_Branch',     'deploy_branch', '/web',     'registered', 'MRL_Projection', '{"note": "顯化部署分支，不是母體本體"}'::jsonb),
('MRL_ARM_Branch',     'deploy_branch', '/arm',     'registered', 'MRL_Projection', '{"note": "顯化部署分支，不是母體本體"}'::jsonb),
('MRL_NAS_Branch',     'deploy_branch', '/nas',     'registered', 'MRL_Projection', '{"note": "顯化部署分支，不是母體本體"}'::jsonb),
('MRL_OEM_Branch',     'deploy_branch', '/oem',     'registered', 'MRL_Projection', '{"note": "顯化部署分支，不是母體本體"}'::jsonb);

-- ═══════════════════════════════════════════════════════════════
-- 8. MetaEnv 初始環境
-- ═══════════════════════════════════════════════════════════════

INSERT INTO mrl_metaenv (env_id, role, shape, policy, status)
VALUES (
    'env_dl580_canonical',
    'canonical',
    '{"cpu": 4, "ram": "128G", "gpu": 0, "host": "DL580"}'::jsonb,
    'Mr.liou.MetaCode.Guard.v1',
    'active'
);
