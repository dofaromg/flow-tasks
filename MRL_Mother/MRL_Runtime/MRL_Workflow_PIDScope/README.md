# MRL_Workflow_PIDScope — Runtime Workflow Ownership Layer

origin_signature = `MrLiouWord`
runtime_layer = `MRL_Mother_Runtime`

DL580 Runtime 的 **PID / Workflow Ownership / Scope Isolation / Recovery** 收斂層。
非 PM2 wrapper、非 systemd sample、非 process demo —— 為 MRL Runtime 的 workflow ownership 層。

---

## 語言分層（本增量範圍）

| Layer | 語言 | 狀態 | 說明 |
|---|---|---|---|
| A — Kernel / PID | Rust / C++ | **未交付(下一增量)** | 不假裝一次做完並驗過;待獨立增量 |
| **B — Orchestration** | **Node.js** | **本增量已交付且本地驗收 PASS** | 本目錄 |
| C — Semantic / AI | Python | 既有 `04_runtime` 等,不在本增量 | — |

> 誠實聲明:Layer A(Rust/C++ PID kernel:scheduler binding / crash restore)是大工程,
> 本增量先交付 Layer B 可運作的 ownership 層 + 可實跑驗收;Layer A 列為下一步,不以空殼或概念充數。

---

## 模組

| 模組 | 檔案 | 功能 |
|---|---|---|
| MRL_PIDScope_Core | `MRL_PIDScope_Core/pidscope_core.js` | runtime PID ownership;拒絕 anonymous;orphan 偵測 |
| MRL_Workflow_Registry | `MRL_Workflow_Registry/workflow_registry.js` | workflow 註冊、runtime 綁定、排序執行 trace、replay |
| MRL_Runtime_ScopeGraph | `MRL_Runtime_ScopeGraph/runtime_scopegraph.js` | scope graph、節點/邊、snapshot/restore |
| MRL_ProcessLineage | `MRL_ProcessLineage/process_lineage.js` | parent/child 程序血緣 |
| MRL_ScopeIsolation | `MRL_ScopeIsolation/scope_isolation.js` | scope 污染偵測(multi_scope / mismatch / external_ownership) |
| MRL_Runtime_Recovery | `MRL_Runtime_Recovery/runtime_recovery.js` | checkpoint / restore（recovery chain）+ restart 血緣 |
| MRL_Orchestration_PIDBridge | `MRL_Orchestration_PIDBridge/orchestration_pidbridge.js` | persistent loop 監督 + 重啟編排（僅作用於本層 spawn 的 PID） |

facade:`index.js` → `createPIDScopeLayer({ dbTarget })`。

---

## Scope

`MRL_RuntimeScope` / `MRL_ReplayScope` / `MRL_WorldScope` / `MRL_ExternalScope`。
規則:`MRL_ExternalScope`（cloudflared / xoopz / github_mirror）**不得擁有 runtime**,只能 adapter/ingress/mirror。

---

## DB 接線

- 正式目標:**`MRL_BaseWorld_DB_v1`**(`db_adapter.js` 的 `BaseWorldAdapter`)。
- **未取得專案 ref + key + 明確授權前,遠端 adapter 保持 inert**(拒絕連線/寫入),不誤連、不誤寫遠端共享 DB。
- 本地驗收使用 `LocalJsonAdapter`,明確標示 **acceptance-only,非正式平行 DB**。
- 邏輯表(對齊規格):`runtime_pidscope`、`workflow_registry`、`runtime_recovery_chain`、`runtime_process_lineage`、`runtime_scope_isolation`。

---

## 驗收

```bash
npm run MRL_pidscope_acceptance
# 或
node acceptance/MRL_PIDScope_Acceptance/run.js
```

涵蓋 A 所有 runtime 有 owner、B restart 後 graph 可恢復、C replay exactness、
D scope 無污染(且能偵測污染)、E orphan 偵測、F runtime 重啟存活。
本地實跑結果:`MRL_PIDSCOPE_ACCEPTANCE_PASS`。

> DL580 host 真實 orchestration 穩定性只能在 DL580 主機上驗,本層在此環境只做本地驗收。
