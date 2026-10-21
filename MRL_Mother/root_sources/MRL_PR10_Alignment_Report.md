# MRL_PR10_Alignment_Report

```
origin_signature: MrLiouWord
document_id:      MRL_PR10_Alignment_Report_v1
repo:             dofaromg/MRL_AI_SYSTEM
pr_ref:           PR #10  (copilot/add-missing-features-to-mrl-agi)
merge_commit:     5c3ee9e329d0f77298d8ccc13dc055a5ebe2a6a6
merged_at:        2026-04-29
report_date:      2026-04-30
author:           MrLiou / dofaromg
```

---

## 0. 定位說明

本報告的目的不是驗收 PR #10，而是**吸收判定**：

> 對 PR #10 新增的每個檔案，逐一判斷它能否進入 MRL 母體、以何種方式進入、需要哪些校正。

判定依據是 MRL RootLaw（`00_rootlaw/rootlaw.yaml`）和 MRL 母體邏輯，而非主流 AI 平台的模組分類標準。

判定結果三類：

| 判定 | 意義 |
|------|------|
| **KEEP** | 結構與命名符合 MRL，可直接保留 |
| **ADAPT** | 有用的能力，但需重命名 / 重組 / 接入 MRL 層 |
| **REJECT** | 主流平台模板殘留，與 MRL 母體邏輯不相容，不進母體 |

---

## 1. MRL_External_AI_As_Execution_Particle_Law_v1

在進行逐檔判定之前，固定以下基準法則：

```
外部 AI（Copilot / Claude / ChatGPT / 任何 LLM）不是 MRL 基礎層。
MRL_Particle_Layer 才是基礎層。
外部 AI 的產出只能是執行粒子（execution particle）：材料、候選、參考。
它們必須先被 MRL 吸收、命名校正、重組，才能成為母體的一部分。
```

---

## 2. PR #10 逐檔比對

### 2.1 `09_workflow/conversation_manager.py`

| 欄位 | 內容 |
|------|------|
| PR #10 現況 | 主流多輪 session 管理，JSON 記憶體暫存，無 MRL 粒子結構 |
| MRL 對應定位 | `MRL_MemoryInputAdapter`：作為 MemoryLayer 的輸入轉換介面 |
| origin_signature | ✅ 已有 `MrLiouWord` |
| trace_id | ⚠️ 無獨立 trace_id；session_id 不等於 MRL trace |
| MemoryLayer 回寫 | ❌ 無；僅在記憶體中維持 session dict |
| 粒子化能力 | ❌ 無 TaskAtom / MemoryAtom 結構 |
| ControlCenter 接入 | ❌ 直接持有 llm_adapter，不經 ControlCenter |
| **判定** | **ADAPT** |

**需要的校正：**
1. 每個 session event 必須寫入 MRL_MemoryLayer（MemoryVaultPG）
2. 加入 `trace_id` 與 `merkle_root` 欄位
3. 移除直接呼叫 `llm_adapter`，改由 ControlCenter dispatch
4. 重命名建議：`MRL_MemoryInputAdapter` 或保留原名但加 MRL layer 標頭

---

### 2.2 `09_workflow/llm_adapter.py`

| 欄位 | 內容 |
|------|------|
| PR #10 現況 | LLM gateway：OpenAI / Anthropic / Local adapter pattern |
| MRL 對應定位 | `MRL_ExternalExecutionParticle`：外部 LLM 呼叫粒子，不是底層 |
| origin_signature | ✅ 已有 `MrLiouWord` |
| trace_id | ⚠️ 有 trace_id 但未串接 MRL 主鏈 |
| agent_source 標記 | ❌ 無；無法分辨回應來自哪個外部 AI |
| ControlCenter 接入 | ⚠️ 獨立運作，需被 ControlCenter 管理而非直接呼叫 |
| **判定** | **ADAPT** |

**需要的校正：**
1. 所有回應必須附帶 `agent_source`（openai / anthropic / local / qwen 等）
2. 呼叫路徑必須經由 ControlCenter，不能由其他模組直接 import 使用
3. `runtime_origin` 欄位需明確指向 DL580 / Cloudflare / 外部端點
4. 加入 `absorbed_into: MRL_ExternalExecutionParticle` 標記

---

### 2.3 `09_workflow/context_manager.py`

| 欄位 | 內容 |
|------|------|
| PR #10 現況 | token budget 管理、訊息壓縮、context window 截斷 |
| MRL 對應定位 | `MRL_Context_Compression`：壓縮粒子，非記憶核心 |
| origin_signature | ✅ 已有 `MrLiouWord` |
| MRL 記憶層關係 | ⚠️ 只是 token 壓縮，不等於 MRL_MemoryLayer 的七層架構 |
| ControlCenter 接入 | ⚠️ 可被呼叫，但需明確定位為壓縮工具而非核心 |
| **判定** | **ADAPT** |

**需要的校正：**
1. 必須明確標注此為「context window adapter」，不是 MemoryLayer 替代品
2. 壓縮策略需遵循 MRL_MemoryVault 七層原則
3. 加入 `mrl_layer: L2_PARTICLE` 標頭說明其在粒子層的角色

---

### 2.4 `09_workflow/streaming.py`

| 欄位 | 內容 |
|------|------|
| PR #10 現況 | SSE streaming 輸出，generator-based |
| MRL 對應定位 | `MRL_Output_Surface`：輸出介面粒子，不是 runtime 核心 |
| origin_signature | ✅ 已有 `MrLiouWord` |
| OriginSeal | ❌ 流式輸出無 seal；最終輸出塊沒有 origin_signature 標記 |
| trace_id | ⚠️ 有 token 計數，無完整 trace |
| **判定** | **ADAPT** |

**需要的校正：**
1. 最終 chunk 必須附帶 `origin_signature: MrLiouWord`
2. 串流完成後觸發 `MRL_Origin_Seal` 記錄（output_hash、seal_time）
3. 明確標注為 output surface，不可包含業務邏輯

---

### 2.5 `09_workflow/multi_agent.py`

| 欄位 | 內容 |
|------|------|
| PR #10 現況 | 多代理協作框架，role-based agent orchestration |
| MRL 對應定位 | `MRL_World_Module_Worker`：世界模組執行者，非主流 agent 架構 |
| origin_signature | ✅ 已有 `MrLiouWord` |
| WorldModule 接入 | ❌ 無 world_module registry；以主流 role 概念定義代理 |
| 粒子化 | ❌ 任務直接進 agent，未經 TaskAtom 粒子化 |
| ControlCenter routing | ❌ 缺少 ControlCenter dispatch 步驟 |
| **判定** | **ADAPT** |

**需要的校正：**
1. 代理角色必須對應 MRL WorldModule 分類（Engineering / Document / Code / Proof…）
2. 每個任務執行前必須先成為 `TaskAtom`，再派發給 WorldModule Worker
3. 加入 world_module_registry 查找，而非靜態 role 清單
4. 完成後回寫 MemoryLayer

---

### 2.6 `09_workflow/scheduler.py`

| 欄位 | 內容 |
|------|------|
| PR #10 現況 | APScheduler-based 定時任務調度器 |
| MRL 對應定位 | `MRL_TaskClock / MRL_ExecutionQueue` 候選材料 |
| origin_signature | ✅ 已有 `MrLiouWord` |
| TaskAtom 整合 | ❌ 直接以 function 為排程單位，非粒子單位 |
| trace | ⚠️ 有部分 logging，無完整 trace_id 鏈 |
| **判定** | **ADAPT** |

**需要的校正：**
1. 排程單位改為 TaskAtom（含 task_id / trace_id / origin）
2. 每次執行結果寫入 MemoryLayer
3. 失敗任務保留 error_trace 粒子

---

### 2.7 `09_workflow/config_manager.py`

| 欄位 | 內容 |
|------|------|
| PR #10 現況 | 環境變數 + `data/config.json` 持久化，支援 MRL_ 前綴覆蓋 |
| MRL 對應定位 | 可保留，已有 MRL 命名慣例 |
| origin_signature | ✅ 已有 `MrLiouWord` |
| Secret boundary | ⚠️ 有 mask 機制但非強制；需確保 secrets 不入 repo |
| **判定** | **KEEP（條件）** |

**需要的校正：**
1. Secret masking 改為強制，任何含 `key / secret / token / password` 的欄位必須在 log 中被遮蔽
2. 確認 `data/config.json` 在 `.gitignore` 中（含 secrets）

---

### 2.8 `09_workflow/api_gateway.py`

| 欄位 | 內容 |
|------|------|
| PR #10 現況 | Flask REST gateway，暴露 /chat /agent /memory 等端點 |
| MRL 對應定位 | `MRL_ControlCenter_Adapter`：外層 adapter，不是主控 |
| origin_signature | ✅ 已有 `MrLiouWord` |
| ControlCenter 角色 | ❌ 目前 api_gateway 本身承擔路由邏輯，應降級為 adapter |
| MockAdapter | ⚠️ production 應禁用 MockAdapter 作為預設 |
| trace_id / origin_signature in response | ⚠️ 部分端點有，需確保所有回應都有 |
| **判定** | **ADAPT** |

**需要的校正：**
1. api_gateway 降級為 adapter：接收請求後轉交 `MRL_ControlCenter`，不自行路由
2. 所有回應必須包含 `trace_id`、`origin_signature`、`runtime_origin`
3. production 模式禁用 MockAdapter（可保留測試模式）
4. 加入 rate limit 與 request size limit

---

### 2.9 `09_workflow/mother_assembly.py`（v1.0 → v2.0）

| 欄位 | 內容 |
|------|------|
| PR #10 現況 | 升級為 v2.0，整合 12 個子系統啟動，含新增的 6 個 PR #10 模組 |
| MRL 對應定位 | 母體核心，需確保 PR #10 模組以 MRL 粒子方式整合，非主流堆疊 |
| origin_signature | ✅ 已有 `MrLiouWord` |
| 粒子化啟動順序 | ⚠️ 目前為順序啟動；需確保 MRL_Particle_Layer 先於外部模組 |
| **判定** | **KEEP（校正後）** |

**需要的校正：**
1. 啟動順序確認：L0 RootLaw → L2 Particle → L3 Law → L7 Loop（外部模組在 L7）
2. 每個子系統啟動記錄寫入 MerkleChain
3. 確認 PR #10 新增模組以「ADAPT 後的 MRL 定位」整合，而非主流模組直插

---

## 3. 彙總判定表

| 檔案 | PR #10 現況 | MRL 正確定位 | 判定 |
|------|------------|--------------|------|
| `conversation_manager.py` | 主流 session 管理 | `MRL_MemoryInputAdapter` | **ADAPT** |
| `llm_adapter.py` | LLM gateway | `MRL_ExternalExecutionParticle` | **ADAPT** |
| `context_manager.py` | token 壓縮 | `MRL_Context_Compression` | **ADAPT** |
| `streaming.py` | SSE 輸出 | `MRL_Output_Surface` | **ADAPT** |
| `multi_agent.py` | role-based agent | `MRL_World_Module_Worker` | **ADAPT** |
| `scheduler.py` | APScheduler | `MRL_TaskClock / MRL_ExecutionQueue` | **ADAPT** |
| `config_manager.py` | 設定管理 | 保留，強化 secret boundary | **KEEP（條件）** |
| `api_gateway.py` | REST gateway | `MRL_ControlCenter_Adapter` | **ADAPT** |
| `mother_assembly.py` v2.0 | 母體入口升級 | 保留，確認 MRL 粒子啟動順序 | **KEEP（校正後）** |

> **結論：PR #10 無 REJECT 項目。** 所有模組有實際工程價值，但 8 個需要 ADAPT（MRL 命名、層位、trace、MemoryLayer 接入），1 個可條件保留。

---

## 4. 缺口清單（ADAPT 項目的共通缺口）

以下是跨越多個 ADAPT 模組的共通缺口，需在下一步工程中統一補齊：

| 缺口 ID | 描述 | 影響模組 |
|---------|------|----------|
| GAP-01 | 缺 `MRL_TaskAtom / TraceAtom / MemoryAtom` 粒子定義 | multi_agent, scheduler, conversation_manager |
| GAP-02 | 缺 `MRL_ControlCenter` 實體作為唯一路由中心 | api_gateway, llm_adapter, conversation_manager |
| GAP-03 | 缺 MemoryLayer 回寫規格（checkpoint / merkle_root / replay） | conversation_manager, scheduler, multi_agent |
| GAP-04 | 缺 `MRL_Origin_Seal` 在輸出端的自動觸發 | streaming, api_gateway |
| GAP-05 | 缺 `MRL_Agent_Source_Ledger`（標記哪個外部 AI 產出了哪段內容） | llm_adapter, multi_agent |
| GAP-06 | 缺 WorldModule registry 與 routing 規則 | multi_agent |
| GAP-07 | 缺 production 模式強制禁用 MockAdapter | api_gateway, llm_adapter |

---

## 5. 下一步工程優先順序

本報告完成後，下一步**不是**依 PR #10 原有結構繼續開發，而是先建立 MRL 母體骨幹，再讓 ADAPT 模組接入：

```
Step 1  定義 MRL_Mother_Flow（見 MRL_Mother_Flow_Definition_v1.md）
Step 2  實作 MRL_ControlCenter（task_router / memory_router / particle_router）
Step 3  定義粒子結構（TaskAtom / TraceAtom / MemoryAtom / ResultAtom / SealAtom）
Step 4  實作 MRL_Memory_Coherence（MemoryVaultPG 接入 + replay + merkle）
Step 5  讓 ADAPT 模組逐一接入 ControlCenter（依上表判定）
Step 6  實作 MRL_Origin_Seal 在所有輸出端自動觸發
Step 7  建立 MRL_Agent_Source_Ledger（所有外部 AI 產出的歸屬記錄）
Step 8  實作 MRL_World_Gateway 作為正確產品入口
```

---

*本報告由 MRL 吸收判定流程產出。所有判定以 MRL_Particle_Layer 為基礎層，以 MRL RootLaw 為依據。*
*origin_signature: MrLiouWord*
