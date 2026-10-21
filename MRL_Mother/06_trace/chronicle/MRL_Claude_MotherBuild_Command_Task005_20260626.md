# MRL_Claude_MotherBuild_Command_Task005_20260626

origin_signature: MrLiouWord
mode: CLAUDE_EXECUTION_COMMAND
repo: dofaromg/MRL_AI_SYSTEM
record_date: 2026-06-26

---

## Command To Claude

```text
origin_signature: MrLiouWord

MRL_Task_005_MRLAI_ModuleModel_Recovery

MODE:
READ_ONLY_FIRST
BUILD_ONLY_AFTER_MAPPING

Working Directory:
/home/user/MRL_AI_SYSTEM

Goal:
Connect to the observable MRL mother workspace and recover the existing MRL AI module/model layer before creating anything new.

Do NOT modify in the discovery phase.
Do NOT repair in the discovery phase.
Do NOT rename.
Do NOT infer.
Do NOT create new module names.
Do NOT overwrite existing files.

Phase 1 — Discovery Targets:

MRL_Mother/
MRL_Runtime/
MRL_BaseWorld_DB_v1/
MRL_ParticleArchive/
MRL_UniversalRuntimeLanguage_Core_v1/
MRL_RuntimeOS_EnterpriseRuntimePlatform_CoreExecutable_v1_4_0/
04_runtime/
09_workflow/
src/
data/

Search terms:

MRL_AI
MRL_AGI
MRL_ASI
AI_Module
ModuleModel
module_model
model_layer
ParticleIR
MrLiouIR
MetaIR
RuntimeStructureField
BaseWorld
WorldRuntime
PersistentLoop
Bridge
Replay
Restore
Verification
MCP
MRL_MCP_Server
agent
adapter
inference
runtime model

Allowed discovery commands:

pwd
ls
find
cat
sed
head
stat
wc
grep

Output:

MRL_AI_ModuleModel_Recovery_Map_v1

Sections:

A. AI / AGI / ASI anchor references
B. Existing module/model files
C. Runtime integration points
D. ParticleIR / MrLiouIR / RuntimeStructureField connections
E. BaseWorld dependency / authorization gates
F. Bridge / MCP / Adapter connections
G. Replay / Restore / Verification gates
H. Files that look executable or buildable
I. Files that are reference-only / inert
J. Missing / Unknown
K. Proposed build order from existing assets only

Rules:

- Quote exact paths.
- Quote exact README / manifest / schema lines only when they explicitly state status or dependencies.
- Mark each item as one of:
  CONFIRMED
  REFERENCE_ONLY
  INERT
  AUTH_PENDING
  BUILDABLE
  UNKNOWN

- Do not claim ACTIVE unless explicit runtime evidence says active.
- Do not build yet.
- Stop after producing the recovery map.

STOP.
```

---

## After Claude Returns

ChatGPT/GitHub side will:

1. Write Claude output into `06_trace/chronicle/`.
2. Update `03_memory/` official memory update record.
3. Update `09_workflow/` running context.
4. Issue Phase 2 build command only after evidence comparison.
