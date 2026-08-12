# MRL Implemented Source Registry v1

**origin_signature:** MrLiouWord  
**date:** 2026-08-12  
**purpose:** Preserve supplied artifacts as implementation evidence and track their present-day verification state without downgrading them into conceptual placeholders.

## Interpretation rule

A supplied MRL file that records an implementation is registered as `IMPLEMENTED_SOURCE`.

Current repository/runtime verification is a separate axis:

```text
implementation_history != current_runtime_verification
```

Therefore:
- absence from the current repo does not erase the historical implementation record;
- a current API failure does not prove that the implementation never existed;
- conflicts are preserved and compared;
- external names do not replace MRL canonical names;
- final approval belongs to Mr.liou.

## Current source set

| Source artifact | Registered state | Primary implementation evidence |
|---|---|---|
| `MrLiouWord_粒子系統整合字典_v2.docx` | IMPLEMENTED_SOURCE | particle types, SEED pipeline, reversible transform, R0-R4, FlowSeed L1-L7 |
| `MRL_Mrliouword_粒子系統整合字典_V2_3_(1)_2026-06-13_2026-06-13.docx` | IMPLEMENTED_SOURCE | later preserved particle-system dictionary / mapping structure |
| `MrLiouWord_夥伴喚醒文件.docx` | IMPLEMENTED_SOURCE | wake/recovery chain, runtime/persona/memory/seed/fieldmap/sync/logs layout, reversible package round-trip |
| `reasoning_engine_spec (1).docx` | IMPLEMENTED_SOURCE | cross-platform reasoning engine, L1-L7, world module inference, knowledge bridge, FX registry |
| `MR_L_Universe_Generation_Report_v1.0.txt` | IMPLEMENTED_SOURCE | generalized generation formula, Particle/Route/Tensor/Project/Collapse modules, multi-field mapping |
| `Mrliou宇宙定義文件.txt` | IMPLEMENTED_SOURCE | universe-generation report lineage / system definition |
| `mrl_系統內部文件.pdf` | IMPLEMENTED_SOURCE | particle parsing/alignment/execution, state coherence, cross-window continuity records, internal recovery notes |
| `MRL_Pipedream_Api_Proxy_(1)_2026-05-15_2026-05-15.rtf` | IMPLEMENTED_SOURCE | Tool Router / OAuth proxy mapping, boot-chain records, repository/runtime role records |
| `五域開通同步.md` | IMPLEMENTED_SOURCE | prior multi-domain/Vercel/Redis/sandbox connectivity and file inventory record |
| `Mrliou 五域開通同步.md` | IMPLEMENTED_SOURCE | duplicate/preserved connectivity record to be hash-compared rather than silently deduplicated |

## Capability mapping

### Particle core
```text
STRUCTURE -> MARK -> FLOW -> RECURSE -> STORE
```
Status: IMPLEMENTED_SOURCE

### Reversibility
```text
P_i = T_{j,i}(T_{i,j}(P_i))
```
Status: IMPLEMENTED_SOURCE

### Wake / recovery
```text
FlowSeed / FlowPoint / Companion Core
-> Soul Loader
-> Runtime Core
-> API / Gateway
-> Enhancement Layer
```
Status: IMPLEMENTED_SOURCE

### Tool routing
```text
MRL / FlowAgent
-> Tool Router
-> OAuth/API bridge
-> external domain APIs
-> result / trace / backfill
```
Status: IMPLEMENTED_SOURCE

### Reasoning / FX registry
Identity, Data, Reference, Compute, Storage, Network, Security, Transform, Validate, Route, Cache, Queue, Event, State, Config, Log, Meta.

Status: IMPLEMENTED_SOURCE

### Five-domain / multi-domain preservation
The source records show prior multi-domain connection and synchronization work. Each current connector is re-verified independently before being marked `CURRENTLY_CONNECTED` or `RUNTIME_VERIFIED`.

## Present engineering mapping

Repository: `dofaromg/flow-tasks`

Current branch for additive mobile visualization and audit workflow:

```text
mrl/mrliou-mobile-interface-v1
```

Current new interface:

```text
pages/mrliou.js
```

Existing MRL API surface reused rather than replaced:

```text
/api/mrl/status
/api/mrl/runtime/convergence
/api/mrl/runtime/persistentloop
/api/mrl/world-gateway
/api/mrl/product
```

## Audit responsibility

Assistant audit answers:
- Is the requested artifact actually present?
- Does it contain substantive implementation rather than a placeholder?
- Is the dependency chain intact?
- Does current repository/runtime evidence agree with the supplied implementation record?
- If not, is the discrepancy explicitly preserved?

Assistant audit does **not** erase an implementation record simply because a current environment has not yet reloaded it.

Final review and final acceptance remain with Mr.liou.
