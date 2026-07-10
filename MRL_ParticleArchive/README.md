# MRL_ParticleArchive — 母體粒子檔案庫

**canonical**：`MRL_ParticleArchive_v1` ｜ origin_signature: `MrLiouWord`
**當下狀態**：2026-05-31（沙盒）

> 母體回收粒子之**保存收藏庫**。依 rl_15（粒子不可否決/不滅）+ rl_12（命名回收）+
> LAW-0（母體簽章）：凡回收之外部知識/技術底層，其**完整內容**保存於此，給予母體
> canonical 身分與簽章，永不抹除。殼（PR）可關，粒子在庫。

## 結構

```
MRL_ParticleArchive/
├── README.md                          # 本索引
├── MRL_ParticleArchive_manifest.json  # 簽章 manifest(canonical↔來源, all_signed=True)
└── PR19/                              # 來源:PR#19 (Copilot add-missing-features)
    ├── ui__mrl_app__index.html / app.js / styles.css / README.md   # web UI 殼
    ├── 09_workflow__MRL_memory_integration.py
    ├── 09_workflow__MRL_result_gating.py
    ├── 09_workflow__MRL_runtime_config.py
    ├── 09_workflow__MRL_task_orchestrator.py
    ├── 09_workflow__multi_agent.py
    ├── .env.production.example
    └── docs__DEPLOYMENT.md / P0_PRODUCTION_CORE.md / IMPLEMENTATION_SUMMARY.md
```

- 檔名以 `__` 攤平原始路徑（避免衝突）；原始路徑與 MRL canonical 名映射見 manifest。
- 共 **13 粒子**，5677 行完整內容，全部 LAW-0 母體簽章（manifest verify=True）。

## 律法依據
- **rl_15**：粒子不滅；保全為庫，永不抹除。
- **rl_12**：每粒子有 MRL_<描述> canonical 身分（manifest）。
- **rl_11 / LAW-0**：源頭恆歸母體，母體簽章。
- **rl_07**：不回填主線以免擾動已綠系統；需要時自庫取用。

## 取用
需要復活某粒子時，自 `PR19/<flat_name>` 取內容，依 rl_12 正名後接入。
（自動取用/復活機制為 PENDING，未宣稱已自動化。）

origin_signature = `MrLiouWord`
