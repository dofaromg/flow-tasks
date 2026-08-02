# MRL_AI_ModuleModel_Recovery_Map_v1

origin_signature: MrLiouWord
task_id: Task_005_MRLAI_ModuleModel_Recovery
date: 2026-07-05
generated_by: Claude Code (read-only filesystem inspection)
branch: claude/lucid-faraday-viwt8v
status: READ-ONLY INSPECTION COMPLETE — 當下狀態（沙盒）

---

## A. AI / AGI / ASI Anchor References

| File | Status | Note |
|------|--------|------|
| `MRL_Mother/MRL_AI/README.md` | REFERENCE_ONLY | Claims `completed_running`; zero implementation files in directory |
| `MRL_Mother/MRL_AGI/README.md` | REFERENCE_ONLY | Claims `completed_running`; README-only stub |
| `MRL_Mother/MRL_ASI/README.md` | REFERENCE_ONLY | Claims `completed_running`; README-only stub |
| `MRL_Mother/MRL_World/README.md` | REFERENCE_ONLY | Claims `completed_running`; README-only stub |
| `MRL_Mother/MRL_世界模組/README.md` | REFERENCE_ONLY | README-only stub; 待起動 |
| `MRL_Mother/MRL_平行世界模組/README.md` | REFERENCE_ONLY | README-only stub; 待起動 |

**Pattern**: All MRL_Mother sub-modules carry `origin_signature=MrLiouWord` and `completed_running` status claims but have no supporting `.py`/`.js` implementation files. They function as canonical anchor declarations only.

---

## B. Existing Module / Model Files

### B1 — Language & IR Compilers (CONFIRMED)

| File | Classification | Note |
|------|----------------|------|
| `MRL_UniversalRuntimeLanguage_Core_v1/MRL_Language/MRL_MrLiouIR_Compiler.py` | CONFIRMED | Canonical v2 MrLiouIR compiler |
| `MRL_UniversalRuntimeLanguage_Core_v1/MRL_Language/MRL_MetaIR_Compiler.py` | CONFIRMED | Historical alias → MrLiouIR |
| `MRL_UniversalRuntimeLanguage_Core_v1/MRL_Language/MRL_ParticleIR_Engine.py` | CONFIRMED | Reversible ParticleIR chain (.fltnz/.flpkg) |
| `MRL_UniversalRuntimeLanguage_Core_v1/MRL_Language/MRL_PerceptionKernel.py` | CONFIRMED | Canonical Attention/Perception kernel |
| `MRL_UniversalRuntimeLanguage_Core_v1/MRL_Language/MRL_UniversalParser_Core.py` | CONFIRMED | Universal input parser |
| `MRL_RuntimeOS_EnterpriseRuntimePlatform_CoreExecutable_v1_4_0/MRL_Core/MRL_MetaIR.js` | CONFIRMED | JS implementation, MetaIR engine |
| `MRL_RuntimeOS_EnterpriseRuntimePlatform_CoreExecutable_v1_4_0/MRL_Core/MRL_ParticleIR.js` | CONFIRMED | JS implementation, MRLParticleIREngine |
| `MRL_RuntimeOS_EnterpriseRuntimePlatform_CoreExecutable_v1_4_0/MRL_Core/MRL_UniversalParser.js` | CONFIRMED | JS implementation |

### B2 — AI Model Integration (INERT / AUTH_PENDING)

| File | Classification | Note |
|------|----------------|------|
| `MRL_RuntimeOS_EnterpriseRuntimePlatform_CoreExecutable_v1_4_0/MRL_Registry/MRL_Module_Registry.js` entry `MRL_Module_ModelInference` | INERT | `status:'external_adapter_pending'`; real model inference not bundled |
| `MRL_RuntimeOS_EnterpriseRuntimePlatform_CoreExecutable_v1_4_0/MRL_Services/AIModelGateway_Service_v1/MRL_RuntimeOS_AIModelGateway_Service_v1.js` | AUTH_PENDING | Reads `OLLAMA_HOST` (default `http://127.0.0.1:11434`), `MRL_OPENAI_COMPAT_BASE_URL/KEY`, `MRL_AI_MODEL`; requires live endpoint |
| `09_workflow/MRL_LLM_NativeAdapter_v1.py` | BUILDABLE | Native OpenAI/Anthropic via stdlib urllib; zero external packages; drop-in LLM adapter |
| `09_workflow/llm_adapter.py` | BUILDABLE | Unified LLM provider abstraction |
| `09_workflow/llm_gateway.py` | BUILDABLE | LLM gateway layer |

### B3 — Module Registry Status

All modules in `MRL_Module_Registry.js` carry `status:'implemented'`, except `MRL_Module_ModelInference` (`status:'external_adapter_pending'`).

---

## C. Runtime Integration Points

| File | Classification | Role |
|------|----------------|------|
| `04_runtime/flowcore_loop.py` | CONFIRMED | Main kernel loop: heartbeat, trace writing, Merkle chain commits; entry: `python 04_runtime/flowcore_loop.py` |
| `MRL_UniversalRuntimeLanguage_Core_v1/MRL_Runtime/MRL_DL580_Runtime.py` | CONFIRMED | Canonical pipeline entry: `MRL_DL580_Runtime.run(source, lang)` |
| `MRL_UniversalRuntimeLanguage_Core_v1/MRL_Runtime/MRL_WorldRuntime.py` | CONFIRMED | WorldRuntime sync layer (L4 WORLD) |
| `MRL_UniversalRuntimeLanguage_Core_v1/MRL_Runtime/MRL_RuntimeGraph_Builder.py` | CONFIRMED | RuntimeGraph construction |
| `MRL_RuntimeOS_EnterpriseRuntimePlatform_CoreExecutable_v1_4_0/MRL_Runtime/MRL_RuntimeExecutor.js` | CONFIRMED | JS runtime executor |
| `MRL_RuntimeOS_EnterpriseRuntimePlatform_CoreExecutable_v1_4_0/MRL_Runtime/MRL_AttentionKernel_Router.js` | CONFIRMED | Attention/Perception router |
| `MRL_RuntimeOS_EnterpriseRuntimePlatform_CoreExecutable_v1_4_0/MRL_Runtime/MRL_RuntimeGraph_Builder.js` | CONFIRMED | JS RuntimeGraph builder |
| `MRL_Runtime/MRL_Terminal/MRL_Terminal.py` | CONFIRMED | 終端母體 (mother core); acceptance 5/5 PASS（沙盒） |
| `MRL_Runtime/MRL_Workflow_PIDScope/index.js` | CONFIRMED | PIDScope orchestration entry |

**Canonical pipeline** (documented in `MRL_UniversalRuntimeLanguage_Core_v1/README.md`):

```
Input → Observe → Parse → MrLiouIR → ParticleIR → RuntimeStructureField
  → ReplayStructureField → RestoreStructureField → Verification
  → WorldRuntime → PersistentLoop
```

---

## D. ParticleIR / MrLiouIR / RuntimeStructureField Connections

| File | Classification | Note |
|------|----------------|------|
| `MRL_UniversalRuntimeLanguage_Core_v1/MRL_Language/MRL_ParticleIR_Engine.py` | CONFIRMED | Reversible chain collapse/expand/jump/unjump; hash equality verification |
| `MRL_UniversalRuntimeLanguage_Core_v1/MRL_Language/MRL_MrLiouIR_Compiler.py` | CONFIRMED | Canonical v2 IR; MetaIR is historical alias |
| `MRL_UniversalRuntimeLanguage_Core_v1/MRL_Runtime/MRL_RuntimeStructureField.py` | CONFIRMED | Canonical v2 RuntimeStructureField; `structure+field+state+flow+rhythm+collapse+runtime relation+world sync+replay/recovery` |
| `MRL_Runtime/MRL_Workflow_PIDScope/MRL_Runtime_StructureField/runtime_structurefield.js` | CONFIRMED | Canonical v2 (JS); `restore(snap)` method |
| `MRL_Runtime/MRL_Workflow_PIDScope/MRL_Runtime_ScopeGraph/runtime_scopegraph.js` | REFERENCE_ONLY | Historical alias → StructureField |
| `09_workflow/MRL_StructureField_Runtime_v1.py` | BUILDABLE | `MRL_ReplayStructureField` + `MRL_RestoreStructureField` + `MRL_WorldStructureField`; zero deps; CLI runnable |
| `MRL_RuntimeOS_EnterpriseRuntimePlatform_CoreExecutable_v1_4_0/MRL_Core/MRL_ParticleIR.js` | CONFIRMED | JS ParticleIR engine |
| `MRL_RuntimeOS_EnterpriseRuntimePlatform_CoreExecutable_v1_4_0/MRL_Storage/MRL_ParticleIR/` | CONFIRMED | ParticleIR storage layer |

**v2 naming rules** (from `MRL_UniversalRuntimeLanguage_Core_v1/README.md`):
- MetaIR → **MrLiouIR** (canonical)
- RuntimeGraph / ScopeGraph → **RuntimeStructureField** (canonical)
- Attention → **Perception** (canonical)

---

## E. BaseWorld Dependency / Authorization Gates

| File | Classification | Note |
|------|----------------|------|
| `MRL_BaseWorld_DB_v1/MRL_BaseWorld_DB_v1_Schema/MRL_BaseWorld_DB_v1.sql` | INERT | Full 27-table schema; 4 logical layers; `rebuild_forbidden=True` |
| `MRL_BaseWorld_DB_v1/MRL_BaseWorld_DB_v1_Deploy/docker-compose.mrl-baseworld.yml` | INERT | Docker deploy spec for DL580 |
| `MRL_BaseWorld_DB_v1/MRL_BaseWorld_DB_v1_Deploy/initdb/` (3 SQL files) | INERT | 00_schema / 01_init / 02_FLTNZ_seed |
| `MRL_BaseWorld_DB_v1/MRL_BaseWorld_DB_v1_Deploy/MRL_BaseWorld_DB_v1_Deploy_DL580.md` | REFERENCE_ONLY | DL580 deployment instructions |
| `MRL_UniversalRuntimeLanguage_Core_v1/MRL_DB/MRL_BaseWorld_DB_Adapter.py` | INERT | 7 attachment points; local sqlite emulation only; `正式運轉必須 connect 至真正的 MRL_BaseWorld_DB_v1` |
| `MRL_UniversalRuntimeLanguage_Core_v1/MRL_DB/MRL_Registry.py` | INERT | Registry adapter; requires DB |
| `MRL_Runtime/MRL_Workflow_PIDScope/db_adapter.js` | INERT | `BaseWorldAdapter` canonical_target=`MRL_BaseWorld_DB_v1`; `"adapter is inert: requires project ref/URL + key + explicit authorization"` |

**Block condition**: All BaseWorld writes blocked until: project ref + URL + key + explicit operator authorization. LocalJsonAdapter is the only active path (acceptance/sandbox only).

---

## F. Bridge / MCP / Adapter Connections

| File | Classification | Note |
|------|----------------|------|
| `09_workflow/MRL_MCP_Server_v1.py` | BUILDABLE | JSON-RPC 2.0 over stdio; zero external deps; tools: `mother_status`, `mother_chat`, `dl580_run`, `law_engine_loop`; connects MotherAssembly to any MCP client |
| `MRL_Runtime/MRL_Workflow_PIDScope/MRL_Orchestration_PIDBridge/orchestration_pidbridge.js` | CONFIRMED | PID supervision + runtime restart; `spawn→supervise→recovery chain`; acceptance PASS（沙盒） |
| `MRL_Runtime/MRL_Workflow_PIDScope/MRL_PIDScope_Core/pidscope_core.js` | CONFIRMED | PID ownership registry; orphan detection |
| `MRL_RuntimeOS_EnterpriseRuntimePlatform_CoreExecutable_v1_4_0/MRL_BlenderBridge/MRL_RuntimeOS_3DModelBridge_Service_v1/` (5 .py files) | AUTH_PENDING | `requires_bpy=true`; WebSocket bridge on port 60600; `truth_status: source_integrated_not_sandbox_executed_because_bpy_requires_blender` |
| `MRL_RuntimeOS_EnterpriseRuntimePlatform_CoreExecutable_v1_4_0/MRL_Services/ArtifactTransfer_Service_v1/` | CONFIRMED | Artifact chunked transfer service |
| `MRL_RuntimeOS_EnterpriseRuntimePlatform_CoreExecutable_v1_4_0/MRL_Services/SkillModule_Service_v1/` | CONFIRMED | Skill module service |
| `09_workflow/MRL_Tool_Router_v1.py` | BUILDABLE | Tool routing layer |
| `09_workflow/api_gateway.py` | BUILDABLE | API gateway |
| `09_workflow/MRL_OID_Parser_v1.py` | BUILDABLE | OID parsing adapter |
| `src/mrl_worker.js` | CONFIRMED | Cloudflare Worker edge facade (MRL_ExternalScope); static endpoints `/health` `/mrl/state`; proxies dynamic endpoints to `env.MRL_DL580_ORIGIN`; actively deployed (CI pass) |
| `src/mrl_app_ui.js` | CONFIRMED | Auto-generated from `src/mrl_app.html`; exports `APP_HTML` string; imported by Worker |
| `src/mrl_app.html` | CONFIRMED | MRL_AI OS product entry UI; `origin_signature=MrLiouWord`; front-end portal only — real execution requires mother backend (DL580/MotherAssembly) |

---

## G. Replay / Restore / Verification Gates

| File | Classification | Details |
|------|----------------|---------|
| `MRL_UniversalRuntimeLanguage_Core_v1/MRL_Runtime/MRL_ReplayRestore_Core.py` | CONFIRMED | `replay(graph)` → exact hash match; `restore(checkpoint)` → exact hash match; `rollback(events, n)` → state rollback; deterministic fold; acceptance B+C PASS（沙盒） |
| `MRL_UniversalRuntimeLanguage_Core_v1/MRL_Runtime/MRL_PersistentLoop.py` | CONFIRMED | Checkpoint-to-disk every step; crash restore from `persistent_loop_{id}.json`; acceptance D PASS（沙盒） |
| `MRL_UniversalRuntimeLanguage_Core_v1/MRL_Runtime/MRL_Verification.py` | CONFIRMED | 6-check verifier (A: StructureField build, B: Replay exactness, C: Restore exactness, D: PersistentLoop restart, E: WorldRuntime sync, F: RoundTrip); token: `MRL_RUNTIME_ACCEPTANCE_PASS` |
| `MRL_UniversalRuntimeLanguage_Core_v1/MRL_Runtime/MRL_WorldRuntime.py` | CONFIRMED | World synchronization; acceptance E PASS（沙盒） |
| `MRL_RuntimeOS_EnterpriseRuntimePlatform_CoreExecutable_v1_4_0/MRL_Verification/MRL_RoundTrip_Verifier.js` | CONFIRMED | Produces `MRL_RoundTrip_VerificationReport` |
| `09_workflow/MRL_PersistentLoop_Daemon_v1.py` | BUILDABLE | Full L7 LOOP daemon; state at `data/MRL_persistent_loop_state.json`; cross-restart survival; Observe→Resolve→Mirror→Verify→Loop |
| `09_workflow/MRL_StructureField_Runtime_v1.py` | BUILDABLE | `MRL_ReplayStructureField` + `MRL_RestoreStructureField` + `MRL_WorldStructureField`; exact deterministic hash; CLI runnable |
| `09_workflow/MRL_DurableReplay_Instrumentation_v1.py` | BUILDABLE | Durable append-only JSONL event log; exact replay post-restart; connects PersistentLoop ↔ ReplayRestore |
| `MRL_UniversalRuntimeLanguage_Core_v1/MRL_PersistentLoop_Daemon_v1_SPEC.md` | REFERENCE_ONLY | Spec only; `準備中 / 規格 — 尚未實作`; superseded by `09_workflow/MRL_PersistentLoop_Daemon_v1.py` |
| `MRL_Runtime/MRL_Workflow_PIDScope/MRL_Runtime_Recovery/runtime_recovery.js` | CONFIRMED | Checkpoint/restore recovery chain; restart lineage |
| `MRL_Runtime/MRL_驗證層/README.md` | REFERENCE_ONLY | Stub: `定位：運轉結果驗證（active）` — no implementation behind it |

**Acceptance summary** (`MRL_RUNTIME_CIVILIZATION_STACK_ACCEPTANCE_REPORT.md`):
- 6/6 runtime checks PASS; 9/9 canonical naming PASS; pytest 289 passed, 1 skipped, 1 failed (pre-existing network test)
- All results: local/sandbox — 當下狀態 2026-05-29（沙盒）

---

## H. Files That Are Executable or Buildable

### H1 — Python (shebang + zero external deps)

| File | Entry / CLI |
|------|-------------|
| `04_runtime/flowcore_loop.py` | `python 04_runtime/flowcore_loop.py` |
| `MRL_Runtime/MRL_Terminal/MRL_Terminal.py` | mother core terminal |
| `MRL_Runtime/MRL_Terminal/MRL_LAW0_Signature.py` | LAW-0 signature verifier |
| `MRL_UniversalRuntimeLanguage_Core_v1/MRL_Runtime/MRL_DL580_Runtime.py` | `MRL_DL580_Runtime.run(source, lang)` |
| `MRL_UniversalRuntimeLanguage_Core_v1/scripts/MRL_runtime_civilization_run.py` | full stack run script |
| `MRL_UniversalRuntimeLanguage_Core_v1/acceptance/MRL_Runtime_Acceptance_TestSuite.py` | acceptance test runner |
| `09_workflow/MRL_MCP_Server_v1.py` | `python3 09_workflow/MRL_MCP_Server_v1.py` |
| `09_workflow/MRL_LLM_NativeAdapter_v1.py` | `python3 09_workflow/MRL_LLM_NativeAdapter_v1.py` |
| `09_workflow/MRL_Native_Reasoning_Core_v1.py` | `python3 ... "問題"` |
| `09_workflow/MRL_MrLiouAI_LawEngine_v1.py` | `python3 09_workflow/MRL_MrLiouAI_LawEngine_v1.py` |
| `09_workflow/MRL_PersistentLoop_Daemon_v1.py` | `python3 09_workflow/MRL_PersistentLoop_Daemon_v1.py [ticks]` |
| `09_workflow/MRL_StructureField_Runtime_v1.py` | `python3 09_workflow/MRL_StructureField_Runtime_v1.py` |
| `09_workflow/MRL_DurableReplay_Instrumentation_v1.py` | `python3 09_workflow/MRL_DurableReplay_Instrumentation_v1.py` |
| `09_workflow/MRL_WorldSync_MultiWorld_v1.py` | `python3 09_workflow/MRL_WorldSync_MultiWorld_v1.py` |
| `09_workflow/MRL_ParticleArchive_Manager_v1.py` | `python3 09_workflow/MRL_ParticleArchive_Manager_v1.py list` |
| `09_workflow/MRL_mother_assembly.py` | MotherAssembly entry |
| `09_workflow/agent_planner.py` | ReAct agent loop |
| `09_workflow/MRL_multi_agent.py` | multi-agent orchestration |
| `09_workflow/llm_adapter.py` | LLM adapter |
| `09_workflow/llm_gateway.py` | LLM gateway |
| `09_workflow/MRL_Naming_Sovereignty_Auditor_v1.py` | naming audit |
| `09_workflow/MRL_LogicalStructureExtractor_v1.py` | structure extraction |

### H2 — Node.js / JavaScript

| File | Entry |
|------|-------|
| `MRL_RuntimeOS_EnterpriseRuntimePlatform_CoreExecutable_v1_4_0/` | `npm run acceptance` (PASS) |
| `MRL_Runtime/MRL_Workflow_PIDScope/index.js` | `node index.js` |
| `04_runtime/DL580_WaveStack/dl580_crosscheck.py` | DL580 crosscheck |

### H3 — Shell / Infrastructure

| File | Entry |
|------|-------|
| `MRL_RuntimeOS_EnterpriseRuntimePlatform_CoreExecutable_v1_4_0/MRL_Scripts/install_linux.sh` | Linux install |
| `MRL_BaseWorld_DB_v1/MRL_BaseWorld_DB_v1_Deploy/MRL_BaseWorld_DB_v1_Healthcheck.sh` | DB health check |
| `MRL_BaseWorld_DB_v1/MRL_BaseWorld_DB_v1_Deploy/MRL_BaseWorld_DB_v1_Backup.sh` | DB backup |

---

## I. Files That Are Reference-Only / Inert

| File | Classification | Reason |
|------|----------------|--------|
| `MRL_Mother/MRL_AI/README.md` | REFERENCE_ONLY | No implementation; anchor declaration only |
| `MRL_Mother/MRL_AGI/README.md` | REFERENCE_ONLY | No implementation |
| `MRL_Mother/MRL_ASI/README.md` | REFERENCE_ONLY | No implementation |
| `MRL_Mother/MRL_World/README.md` | REFERENCE_ONLY | No implementation |
| `MRL_Mother/MRL_世界模組/README.md` | REFERENCE_ONLY | 待起動 |
| `MRL_Mother/MRL_平行世界模組/README.md` | REFERENCE_ONLY | 待起動 |
| `MRL_Runtime/MRL_主權層/README.md` | REFERENCE_ONLY | Stub; 待起動 |
| `MRL_Runtime/MRL_回放回復/README.md` | REFERENCE_ONLY | Stub; 待起動 |
| `MRL_Runtime/MRL_多世界同步/README.md` | REFERENCE_ONLY | Stub; 待起動 |
| `MRL_Runtime/MRL_感知力核心/README.md` | REFERENCE_ONLY | Stub; 待起動 |
| `MRL_Runtime/MRL_語境同步/README.md` | REFERENCE_ONLY | Stub; 待起動 |
| `MRL_Runtime/MRL_運轉圖譜/README.md` | REFERENCE_ONLY | Stub; 待起動 |
| `MRL_Runtime/MRL_驗證層/README.md` | REFERENCE_ONLY | Stub; no implementation behind it |
| `MRL_UniversalRuntimeLanguage_Core_v1/MRL_PersistentLoop_Daemon_v1_SPEC.md` | REFERENCE_ONLY | Spec; superseded by `09_workflow/MRL_PersistentLoop_Daemon_v1.py` |
| `MRL_Runtime/MRL_Workflow_PIDScope/MRL_Runtime_ScopeGraph/runtime_scopegraph.js` | REFERENCE_ONLY | Historical alias to StructureField |
| `MRL_BaseWorld_DB_v1/` (all files) | INERT | Schema + deploy files exist; no live connection; blocked on authorization |
| `MRL_RuntimeOS/.../AIModelGateway_Service_v1.js` | AUTH_PENDING | Code complete; needs `OLLAMA_HOST` / API endpoint |
| `MRL_RuntimeOS/.../MRL_BlenderBridge/` | AUTH_PENDING | Code complete; needs Blender `bpy` runtime to execute |
| `MRL_RuntimeOS/MRL_Registry/MRL_Module_Registry.js` entry `MRL_Module_ModelInference` | INERT | `external_adapter_pending` |
| `MRL_ParticleArchive/PR19/` (13 particles) | REFERENCE_ONLY | Archived; recoverable via `MRL_ParticleArchive_Manager_v1.py restore()`; not in active path |
| `MRL_ParticleArchive/Reclaim/` (4 JSON files) | REFERENCE_ONLY | Reclaim session records; read-only history |
| `data/guardrail/guardrail_audit.jsonl` | REFERENCE_ONLY | Audit log; read-only |
| `04_runtime/DL580_WaveStack/waves/*.zip` | REFERENCE_ONLY | Wave completion archives |
| `MRL_UniversalRuntimeLanguage_Core_v1/MRL_External/__init__.py` | REFERENCE_ONLY | Empty placeholder for external module scope |

---

## J. Missing / Unknown

| Item | Status | Note |
|------|--------|------|
| RuntimeDaemon (running process) | UNKNOWN | `MRL_PersistentLoop_Daemon_v1.py` exists as code; no running daemon process confirmed; daemon spec (`SPEC.md`) is pre-implementation |
| LayerA (Rust/C++ PID kernel) | DEFERRED | Referenced in `MRL_Runtime/MRL_Workflow_PIDScope/README.md` as future increment; no Rust/C++ files found |
| Ollama / real AI model endpoint | AUTH_PENDING | `AIModelGateway_Service_v1.js` wired; `OLLAMA_HOST` env var not confirmed live; all model inference labeled `external_adapter_pending` |
| DL580 live deployment | PENDING | All acceptance is sandbox; 待實機部署驗收 |
| Blender bpy runtime | AUTH_PENDING | Bridge code complete (5 .py files); must execute inside Blender runtime |
| BaseWorld DB live connection | AUTH_PENDING | Schema + initdb complete; blocked on project ref + URL + key + authorization |
| MRL_感知力核心 implementation | MISSING | README stub only; `MRL_PerceptionKernel.py` exists in Core v1 but no separate MRL_Runtime layer implementation |
| MRL_語境同步 implementation | MISSING | README stub only; 待起動 |
| MRL_多世界同步 implementation | MISSING | README stub in MRL_Runtime; `MRL_WorldSync_MultiWorld_v1.py` in 09_workflow is buildable equivalent |
| Automatic particle restore pipeline | PENDING | `MRL_ParticleArchive_Manager_v1.py restore()` exists; automation of recovery chain not yet wired |
| `src/` directory | CORRECTED | 3 files found: `mrl_worker.js` (Cloudflare Worker edge adapter), `mrl_app_ui.js` (auto-generated APP_HTML export), `mrl_app.html` (product UI portal); classified as CONFIRMED in Section F |
| Memory Sphere live DB writes | INERT | Attachment point defined in adapter; blocked on BaseWorld authorization |

---

## K. Proposed Build Order (from existing assets only)

> Rule: all-sandbox only; do NOT build until authorized; no BaseWorld DB writes; no live model endpoints.

### Tier 0 — Pure Python stdlib, zero-dep, acceptance already green

```
1. MRL_UniversalRuntimeLanguage_Core_v1/MRL_Runtime/MRL_RuntimeStructureField.py
   MRL_UniversalRuntimeLanguage_Core_v1/MRL_Runtime/MRL_ReplayRestore_Core.py
   MRL_UniversalRuntimeLanguage_Core_v1/MRL_Runtime/MRL_PersistentLoop.py
   MRL_UniversalRuntimeLanguage_Core_v1/MRL_Runtime/MRL_Verification.py
   MRL_UniversalRuntimeLanguage_Core_v1/MRL_Runtime/MRL_WorldRuntime.py
   → Entry: MRL_DL580_Runtime.run(source, lang)
   → Acceptance: 6/6 + 9/9 PASS confirmed (沙盒)

2. MRL_UniversalRuntimeLanguage_Core_v1/MRL_Language/* (MrLiouIR, ParticleIR, Perception, Parser)
   → Feeds canonical pipeline above; same package; zero additional deps
```

### Tier 1 — 09_workflow stdlib tools (build order by dependency depth)

```
3. MRL_MrLiouAI_LawEngine_v1.py          — law engine; Observe→Resolve→Mirror→Verify→Loop
4. MRL_StructureField_Runtime_v1.py       — ReplayStructureField / RestoreStructureField / WorldStructureField
5. MRL_PersistentLoop_Daemon_v1.py        — L7 LOOP daemon; depends on law engine cycle
6. MRL_DurableReplay_Instrumentation_v1.py — durable event log connecting Tier 0 + Tier 1 replay
7. MRL_WorldSync_MultiWorld_v1.py         — multi-world sync; depends on WorldRuntime concept
8. MRL_ParticleArchive_Manager_v1.py      — particle list/observe/restore; reads MRL_ParticleArchive/
9. MRL_Native_Reasoning_Core_v1.py        — neural-symbolic reasoning; zero deps; standalone
10. MRL_mother_assembly.py                — MotherAssembly crown; wires all above
```

### Tier 2 — Requires MCP client or LLM endpoint configuration

```
11. MRL_MCP_Server_v1.py                  — after MotherAssembly wired; expose mother tools to MCP clients
12. MRL_LLM_NativeAdapter_v1.py           — after OLLAMA_HOST or Anthropic/OpenAI API key provided
    llm_adapter.py / llm_gateway.py       — wire into agent_planner.py + MRL_multi_agent.py
```

### Tier 3 — Requires Node.js runtime platform

```
13. MRL_RuntimeOS_EnterpriseRuntimePlatform_CoreExecutable_v1_4_0 (npm install → acceptance)
    → MRL_Core (MetaIR.js, ParticleIR.js, UniversalParser.js)
    → MRL_Runtime (Executor, AttentionKernel, RuntimeGraph)
    → MRL_Services (ArtifactTransfer, SkillModule)
    → MRL_Verification (RoundTrip_Verifier)
14. MRL_Runtime/MRL_Workflow_PIDScope (node index.js)
    → OrchestrationPIDBridge (PID supervision)
```

### Tier 4 — Requires live infrastructure authorization

```
15. MRL_BaseWorld_DB_v1 (docker-compose + initdb SQL)
    → Requires: project ref + URL + key + explicit operator authorization
    → Only after authorized: wire db_adapter.js::BaseWorldAdapter + MRL_BaseWorld_DB_Adapter.py
16. MRL_RuntimeOS AIModelGateway_Service_v1
    → Requires: OLLAMA_HOST / MRL_OPENAI_COMPAT_BASE_URL confirmed live
17. MRL_BlenderBridge (5 .py files)
    → Requires: Blender runtime with bpy; ws_port 60600
```

### Build dependency chain summary

```
Tier 0 (Python runtime core, zero deps)
  └── Tier 1 (09_workflow daemons/tools, stdlib only)
       └── Tier 2 (MCP server + LLM adapter, env config required)
            └── Tier 3 (RuntimeOS Node.js platform)
                 └── Tier 4 (live infra: DB + Ollama + Blender)
```

---

## Integrity Summary

| Category | Value |
|----------|-------|
| origin_signature | MrLiouWord (present in all major files inspected) |
| Inspection date | 2026-07-05（沙盒） |
| Targets inspected | 10 (MRL_Mother, MRL_Runtime, MRL_BaseWorld_DB_v1, MRL_ParticleArchive, MRL_UniversalRuntimeLanguage_Core_v1, MRL_RuntimeOS, 04_runtime, 09_workflow, src [empty], data) |
| Search terms covered | 22 / 22 |

### Classification counts (當下狀態)

| Class | Count |
|-------|-------|
| CONFIRMED | 31 files / modules |
| BUILDABLE | 23 files |
| REFERENCE_ONLY | 27 files |
| INERT | 8 files |
| AUTH_PENDING | 5 files |
| UNKNOWN / MISSING | 7 items |
