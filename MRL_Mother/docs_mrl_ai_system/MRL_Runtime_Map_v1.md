# MRL_Runtime_Map_v1

origin_signature: MrLiouWord
task_id: Task_004_Runtime_Map
date: 2026-06-25
generated_by: Claude Code (read-only filesystem inspection)
branch: claude/lucid-faraday-viwt8v
status: READ-ONLY INSPECTION COMPLETE — 當下狀態（沙盒）

---

## Inspected Targets

| Target | Files | Dirs | Last Modified (UTC) |
|--------|-------|------|----------------------|
| `04_runtime/` | 12 | 3 | 2026-06-25 15:21:23 |
| `MRL_Runtime/` | 22 | 18 | 2026-06-25 15:21:24 |
| `MRL_RuntimeOS_EnterpriseRuntimePlatform_CoreExecutable_v1_4_0/` | 321 | 36 | 2026-06-25 15:21:24 |

---

## A. 04_runtime

### Top-level tree

```
04_runtime/
├── README.md
├── runtime_manifest.yaml
├── flowcore_loop.py
└── DL580_WaveStack/
    ├── MRL Engineering Manifest.json
    ├── MRL Runtime Stack Manifest.json
    ├── MRL Runtime Stack DL580 Fill Report.md
    ├── MRL Wave01 DL580 Native Gate Receipt.txt
    ├── dl580_crosscheck.py
    └── waves/
        ├── Mrliou_MRL_Runtime_Wave01_Completed_v1.zip
        ├── Mrliou_MRL_Runtime_Wave02_Completed_v1.zip
        ├── Mrliou_MRL_Runtime_Wave03_Completed_v1.zip
        └── Mrliou_MRL_Runtime_Wave04_Completed_v1.zip
```

### README / Manifest files

- `README.md`
- `runtime_manifest.yaml`
- `DL580_WaveStack/MRL Engineering Manifest.json`
- `DL580_WaveStack/MRL Runtime Stack Manifest.json`

### Runtime-related files

- `flowcore_loop.py` — main kernel loop: heartbeat, trace writing, Merkle chain commits
- `dl580_crosscheck.py` — DL580 verification crosscheck
- 4 Wave completion ZIP archives (Wave01–Wave04)

### Loop cycle (from README.md)

`Observe → Resolve → Mirror → Project → Verify → Iterate`

### Execution tiers (from README.md)

| Tier | Description |
|------|-------------|
| TotalCore | All six core groups loaded and cross-linked |
| Runtime | Minimal kernel: loop + Merkle chain + trace |
| Container | FlowCoreLoop HTTP control plane + Vault |
| CLI | Day-to-day operator commands |

### Dependency references (manifest/README only)

- `Verify`: "Verify L0 signature", "Verify Merkle chain integrity", "Verify world module" (runtime_manifest.yaml)
- `Restore`: "Restore world state from the most recent valid snapshot" (runtime_manifest.yaml)
- `PersistentLoop`: NOT FOUND in 04_runtime; referenced via MRL_Runtime hierarchy

---

## B. MRL_Runtime

### Top-level tree

```
MRL_Runtime/
├── MRL_Terminal/
│   ├── README.md
│   ├── MRL_LAW0_Signature.py
│   ├── MRL_Terminal.py
│   └── Terminal_StereoscopicSeed_Spec.md
├── MRL_Workflow_PIDScope/
│   ├── README.md
│   ├── index.js
│   ├── db_adapter.js
│   ├── MRL_Orchestration_PIDBridge/
│   │   └── orchestration_pidbridge.js
│   ├── MRL_PIDScope_Core/
│   │   └── pidscope_core.js
│   ├── MRL_ProcessLineage/
│   │   └── process_lineage.js
│   ├── MRL_Runtime_Recovery/
│   │   └── runtime_recovery.js
│   ├── MRL_Runtime_ScopeGraph/
│   │   └── runtime_scopegraph.js (歷史相容 alias → StructureField)
│   ├── MRL_Runtime_StructureField/
│   │   └── runtime_structurefield.js (canonical v2)
│   ├── MRL_ScopeIsolation/
│   │   └── scope_isolation.js
│   └── MRL_Workflow_Registry/
│       └── workflow_registry.js
├── MRL_主權層/      └── README.md
├── MRL_回放回復/    └── README.md
├── MRL_多世界同步/  └── README.md
├── MRL_感知力核心/  └── README.md
├── MRL_語境同步/    └── README.md
├── MRL_運轉圖譜/    └── README.md
└── MRL_驗證層/      └── README.md
```

### README / Manifest files

- `MRL_Terminal/README.md`
- `MRL_Workflow_PIDScope/README.md`
- `MRL_主權層/README.md`
- `MRL_回放回復/README.md`
- `MRL_多世界同步/README.md`
- `MRL_感知力核心/README.md`
- `MRL_語境同步/README.md`
- `MRL_運轉圖譜/README.md`
- `MRL_驗證層/README.md`

### Key modules

| Module | File | Function |
|--------|------|----------|
| MRL_Orchestration_PIDBridge | `orchestration_pidbridge.js` | persistent loop supervision + runtime restart orchestration |
| MRL_PIDScope_Core | `pidscope_core.js` | runtime PID ownership; reject anonymous; orphan detection |
| MRL_Workflow_Registry | `workflow_registry.js` | workflow registration, runtime binding, trace replay |
| MRL_Runtime_Recovery | `runtime_recovery.js` | checkpoint/restore (recovery chain) + restart lineage |
| MRL_Runtime_StructureField | `runtime_structurefield.js` | runtime structure field (canonical v2) |
| MRL_Terminal | `MRL_Terminal.py` | 終端系統立體種子（mother core）|

### Dependency references (README/manifest only)

- `PersistentLoop`: MRL_Terminal/README.md "WorldRuntime→PersistentLoop"; MRL_Orchestration_PIDBridge "persistent loop 監督 + 重啟編排"
- `Bridge`: MRL_Orchestration_PIDBridge (PIDBridge)
- `Replay`: MRL_Workflow_Registry "trace、replay"; MRL_Runtime_StructureField MRL_ReplayScope ["checkpoint", "restore", "rollback", "replay"]
- `Restore`: MRL_Runtime_Recovery "checkpoint / restore（recovery chain）"; runtime_structurefield.js `restore(snap)` method
- `Verification`: MRL_驗證層/README.md "定位：運轉結果驗證（active）"
- `MrLiouIR`: MRL_Terminal/README.md "MrLiouIR/ParticleIR/StructureField"; MRL_Runtime_StructureField "MetaIR→MrLiouIR"
- `ParticleIR`: MRL_Terminal/README.md; MRL_Runtime_StructureField canonical scope list
- `RuntimeStructureField`: runtime_structurefield.js "canonical v2：StructureField 為主體"
- `BaseWorld`: db_adapter.js — adapter target `MRL_BaseWorld_DB_v1` (NOT runtime implementation)
- `RuntimeDaemon`: NOT FOUND
- `LayerA`: Referenced as future work (Rust/C++ PID kernel) — not delivered in this increment

---

## C. MRL_RuntimeOS_EnterpriseRuntimePlatform_CoreExecutable_v1_4_0

### Top-level tree

```
MRL_RuntimeOS_EnterpriseRuntimePlatform_CoreExecutable_v1_4_0/
├── README.md
├── START_HERE.md
├── MRL_STATUS.md
├── Dockerfile
├── docker-compose.yml
├── package.json
├── START_MRL.ps1
├── MRL_API/              → MRL_RuntimeServer.js
├── MRL_Acceptance/       → MRL_Acceptance_TestSuite.js, MRL_Smoke_Dl580.js
├── MRL_BlenderBridge/    → MRL_RuntimeOS_3DModelBridge_Service_v1/
├── MRL_Context/          → MRL_ContextGraph_Builder.js
├── MRL_Core/             → MRL_MetaIR.js, MRL_ParticleIR.js, MRL_UniversalParser.js
├── MRL_Deploy/           → MRL_DL580_DEPLOYMENT.md
├── MRL_Docs/             → 3 report/handoff .md files
├── MRL_Registry/         → MRL_Module_Registry.js
├── MRL_Runtime/          → MRL_AttentionKernel_Router.js, MRL_RuntimeExecutor.js, MRL_RuntimeGraph_Builder.js
├── MRL_RuntimeMesh/      → MRL_RuntimeMesh_Controller.js
├── MRL_RuntimeNode/      → MRL_RuntimeNode_Manager.js
├── MRL_Scripts/          → MRL_CLI.js, install_linux.sh, install_windows.ps1
├── MRL_Security/         → MRL_AuthGate.js
├── MRL_Services/         → AIModelGateway_Service_v1, ArtifactTransfer_Service_v1, SkillModule_Service_v1
├── MRL_Storage/          → MRL_Artifacts/, MRL_Attention/, MRL_Audit/, MRL_ContextGraph/,
│                           MRL_MetaIR/, MRL_ParticleIR/, MRL_RuntimeGraph/, MRL_RuntimeNodes/
└── MRL_Verification/     → MRL_RoundTrip_Verifier.js
```

### README / Manifest files

- `README.md`
- `START_HERE.md`
- `MRL_STATUS.md`
- `MRL_BlenderBridge/MRL_RuntimeOS_3DModelBridge_Service_v1/MRL_BlenderBridge_MANIFEST.json`
- `MRL_Deploy/MRL_DL580_DEPLOYMENT.md`
- `MRL_Docs/MRL_CrossCompare_Completion_Report.md`
- `MRL_Docs/MRL_RuntimeNode_Mesh_Handoff_v1.md`
- `MRL_Docs/MRL_RuntimeOS_Product_Module_Addition_Report_v1_4_0.md`

### Dependency references (README/manifest only)

- `Bridge`: MRL_RuntimeOS_3DModelBridge_Service_v1 (Blender 3D Model Bridge)
- `Verification`: MRL_RoundTrip_Verifier.js produces `MRL_RoundTrip_VerificationReport`
- `ParticleIR`: MRL_Core/MRL_ParticleIR.js (MRLParticleIREngine); MRL_Storage/MRL_ParticleIR/; acceptance checks
- `BaseWorld`: MRL_STATUS.md "BaseWorld DB write adapter"; MRL_Docs/MRL_CrossCompare_Completion_Report.md
- `PersistentLoop`: NOT FOUND in this package
- `MrLiouIR`: NOT FOUND in this package
- `RuntimeStructureField`: NOT FOUND in this package (defined in MRL_Runtime parent layer)
- `RuntimeDaemon`: NOT FOUND
- `LayerA`: NOT FOUND (referenced only in parent MRL_Runtime layer)

---

## D. Cross References & Integration Points

| Term | Found | Location | Status |
|------|-------|----------|--------|
| PersistentLoop | ✓ | MRL_Runtime/MRL_Terminal, MRL_Orchestration_PIDBridge | ACTIVE |
| Bridge (PID) | ✓ | MRL_Runtime/MRL_Workflow_PIDScope/MRL_Orchestration_PIDBridge | PASS (本地驗收) |
| Bridge (3D) | ✓ | MRL_RuntimeOS/MRL_BlenderBridge/MRL_RuntimeOS_3DModelBridge_Service_v1 | Pending Blender runtime |
| Replay | ✓ | MRL_Runtime/MRL_Workflow_PIDScope/MRL_Workflow_Registry | ACTIVE |
| Restore | ✓ | MRL_Runtime/MRL_Workflow_PIDScope/MRL_Runtime_Recovery | ACTIVE (LocalJsonAdapter only) |
| Verification | ✓ | MRL_Runtime/MRL_驗證層; MRL_RuntimeOS/MRL_Verification | ACTIVE |
| MrLiouIR | ✓ | MRL_Runtime/MRL_Terminal → MRL_Runtime_StructureField | Defined; MetaIR alias |
| ParticleIR | ✓ | MRL_Runtime_StructureField + MRL_RuntimeOS/MRL_Core/MRL_ParticleIR.js | ACTIVE |
| RuntimeStructureField | ✓ | MRL_Runtime/MRL_Workflow_PIDScope/MRL_Runtime_StructureField | Canonical v2 |
| BaseWorld | ✓ | MRL_Runtime/db_adapter.js (adapter target) | INERT (awaiting authorization) |
| RuntimeDaemon | ✗ | NOT FOUND across all three targets | UNDEFINED |
| LayerA (Kernel) | ✗ | Referenced in MRL_Workflow_PIDScope/README.md | DEFERRED (Rust/C++) |

### Integration chain (documented)

```
04_runtime (flowcore_loop.py / L7)
  └── MRL_Runtime/MRL_Terminal (observe→advance→reify mother core)
       └── MRL_Runtime/MRL_Workflow_PIDScope (PID ownership / recovery)
            └── MRL_RuntimeOS_EnterpriseRuntimePlatform_CoreExecutable_v1_4_0
                 ├── MRL_Core (MrLiouIR/ParticleIR/UniversalParser)
                 ├── MRL_Runtime (Executor, AttentionKernel, RuntimeGraph)
                 ├── MRL_Services (AIModelGateway, SkillModule, ArtifactTransfer)
                 └── MRL_Verification (RoundTrip_Verifier)
```

---

## E. Missing / Unknown

| Item | Status | Note |
|------|--------|------|
| RuntimeDaemon | NOT FOUND | Undefined across all targets; possibly external |
| LayerA (Kernel) | DEFERRED | Future increment — Rust/C++ PID scheduler binding + crash restore |
| Restore checkpoint storage | PARTIAL | Method exists; persistent storage blocked on BaseWorld authorization |
| MRL_感知力核心 (impl) | STUB | README-only; implementation not delivered |
| MRL_主權層 (impl) | STUB | README-only; marked 待起動 |
| MRL_語境同步 (impl) | STUB | README-only; marked 待起動 |
| MRL_多世界同步 (impl) | STUB | README-only; marked 待起動 |
| MRL_運轉圖譜 (impl) | STUB | README-only; marked 待起動 |

---

## Integrity Summary

| Category | Value |
|----------|-------|
| origin_signature | MrLiouWord (present in all major README files) |
| Version | v1_4_0 (MRL_RuntimeOS) |
| Inspection date | 2026-06-25 (沙盒) |

### Acceptance Status (沙盒)

| Component | Status |
|-----------|--------|
| 04_runtime (flowcore_loop) | Local run OK |
| MRL_Runtime/MRL_Terminal | 5/5 PASS (MRL_TERMINAL_ACCEPTANCE_PASS) |
| MRL_Runtime/MRL_Workflow_PIDScope | PASS (MRL_PIDSCOPE_ACCEPTANCE_PASS) |
| MRL_RuntimeOS (npm run acceptance) | PASS |

### Deployment Status (真實 / Production)

| Component | Status |
|-----------|--------|
| DL580 host | 待實機部署驗收 (pending real deployment) |
| Blender 3D Bridge | bpy 需在 Blender runtime 內驗收 |
| BaseWorld DB | INERT — awaiting project ref + key + authorization |
