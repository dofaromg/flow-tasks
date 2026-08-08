# MRL_AI_SYSTEM — 延伸建構路線圖

> Origin Signature: MrLiouWord  
> 基準版本：v2.0.0（PR #12 merged 2026-05-04）  
> 目的：記錄 v2.0.0 合併後的後續延伸方向，依優先序排列。

---

## 現況摘要（v2.0.0 已完成）

| 類別 | 已完成 |
|------|--------|
| 核心子系統 | 15 個（merkle_chain、world_module、vector_store、tool_registry、template_registry、eval_pipeline、plugin_manager、config_manager、conversation_manager、llm_gateway、context_manager、scheduler、guardrail、metrics、host_guard） |
| API Gateway | `/chat`、`/chat/stream`（SSE）、`/metrics`、`/guard`、`/export/{sid}` |
| 安全 | CORS + Origin 注入防護、rate limiter、DL580-only 學習閘門 |
| 測試 | 248 tests（pytest）|
| CI/CD | `deploy.yml`：push→test；tag→test+release zip |
| 記憶 | Merkle chain tracing、`MRL_memory_integration.py` |
| 任務引擎 | `MRL_task_orchestrator.py`（QUEUED→RUNNING→DONE/FAILED→SEALED）|
| 結果分層 | `MRL_result_gating.py`（partial / full + entitlements）|

---

## P1 — 立即可做（1–2 週）

### P1-1 打 v2.0.0 tag + 建立 Release

```bash
git tag v2.0.0
git push origin v2.0.0
```

- `deploy.yml` 自動打包 `MRL_AI_SYSTEM-v2.0.0.zip` 並建立 GitHub Release。
- 完成後 MRL_AI_SYSTEM 即有第一個正式可交付版本。

### P1-2 MRL_Auth_Account（使用者認證）

目前 API 無 token 驗證，生產環境必補：

- 新增 `MRL_auth.py`：Bearer token 驗證（JWT 或 simple API key）
- `api_gateway.py` `/chat`、`/agent/run`、`/result/full` 全部加 `Authorization` header 檢查
- `user_id` 綁定 `session_id` / `task_id`

驗收：未帶 token 時 401；帶合法 token 時正常回應。

### P1-3 /agent/run 接通 MRL_task_orchestrator

`MRL_task_orchestrator.py` 已實作但 `api_gateway.py` 尚未暴露對應端點：

- 新增 `POST /agent/run`：建立 task_id、QUEUED 狀態
- 新增 `GET  /agent/status/{task_id}`：查詢任務狀態
- 新增 `GET  /result/partial/{task_id}` / `GET /result/full/{task_id}`：對接 `MRL_result_gating`

驗收：`/agent/run` 可執行多步任務並產出 task_id、status、result、trace。

---

## P2 — 產品體驗（2–4 週）

### P2-1 MRL_Product_Entry_UI

`ui/` 目錄已有初步 Streamlit UI，需升級為產品級入口：

- 大輸入框 + 新會話 / 歷史會話列表
- 串接 `/chat/stream`（SSE）顯示生成中狀態
- 顯示 trace_id、engine、origin_signature（右下角）
- 支援中斷 / 重新生成

### P2-2 MRL_Billing_Ledger（計費帳本）

對接 `MRL_result_gating` 的 entitlements：

- 新增 `MRL_billing.py`：ledger 記錄（SQLite / JSON）
- 支援單次付費、內部 credit
- payment_status 解鎖 full_result 存取

### P2-3 MRL_Admin_Console

- 任務 / 使用者 / 付款查詢端點
- 健康狀態整合（`MRL_health_monitor.py`）
- 錯誤 trace 查詢（`MRL_memory_integration.py`）

---

## P3 — MRL 主權與證據鏈（持續）

### P3-1 全量 origin_signature 驗證

- `MRL_runtime_config.py` 已在 `/chat` 注入 `origin_signature`、`trace_id`
- 延伸至所有 `/agent/run`、`/result/*`、`/export/*` 回應
- `seal` 端點寫入 checksum / merkle_root（`MRL_memory_integration.py`）

### P3-2 v2.x Release Cycle

| Tag | 里程碑 |
|-----|--------|
| v2.0.0 | P0 完整（現在）|
| v2.1.0 | P1-2 + P1-3（Auth + /agent/run）|
| v2.2.0 | P2-1（Product UI）|
| v2.3.0 | P2-2（Billing）|
| v3.0.0 | 多主線 Orchestrator（multi-pipeline build）|

### P3-3 文件補齊

- `README_ENGINEERING.md`：工程版（架構、端點、環境變數、測試）
- `DEPLOY_DL580.md`：DL580 一鍵部署腳本
- `SECURITY.md`：安全邊界聲明
- `LICENSE / NOTICE`：MrLiouWord 版權聲明對齊

---

## P4 — 多主線 Orchestrator（4–8 週）

### P4-1 MRL_Orchestrator（spec → product bundle）

基於已有 `MotherAssembly` 的 `build` 子命令概念：

```bash
python -m 09_workflow.MRL_mother_assembly build --spec specs/product.md --out runs/
```

- `spec.md` → `spec.json`（heading 切段）
- 依序呼叫多個 builder（planner / backend / frontend / docs）
- 合併 artifacts → `MRL_AI_SYSTEM-{run_id}.flpkg`（用 `fltnz_parser.pack()`）

### P4-2 Builder Plugin 介面

每個 builder 遵守：

```python
def run(spec: dict, context_dir: Path) -> BuildResult:
    # input: spec.json + shared context/
    # output: artifacts/ + result.json + trace.log
```

---

## 下一個立即動作

```bash
# 1. 打 v2.0.0 tag（觸發自動 Release）
git tag v2.0.0 && git push origin v2.0.0

# 2. 驗證 CI 通過
# .github/workflows/deploy.yml → test job → pytest tests/ -v

# 3. 開始 P1-2（MRL_auth.py）
```
