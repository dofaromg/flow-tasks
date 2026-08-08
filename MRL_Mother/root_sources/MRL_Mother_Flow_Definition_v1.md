# MRL_Mother_Flow_Definition_v1

```
origin_signature: MrLiouWord
document_id:      MRL_Mother_Flow_Definition_v1
repo:             dofaromg/MRL_AI_SYSTEM
version:          v1
date:             2026-04-30
author:           MrLiou / dofaromg
layer:            L3_LAW (canonical flow specification)
```

---

## 0. 定位說明

本文件定義 MRL 系統的**母體產品主流程**（Mother Flow）。

這不是 chat-first 流程，不是 REST API wrapper，不是主流 AI 平台的功能清單。

> MRL 母體流程的核心邏輯是：
> **任何輸入，必須先成為粒子；任何輸出，必須帶有封印。**

---

## 1. 流程總覽

```
使用者輸入（任何形式）
        │
        ▼
① MRL_World_Gateway（產品入口，外層護城河）
        │
        ▼
② MRL_Input_Particleization（輸入粒子化）
        │  → 生成 TaskAtom + TraceAtom
        ▼
③ MRL_ControlCenter（唯一路由中心）
        │  task_router / memory_router / particle_router / world_router
        ▼
④ MRL_WorldMapping（任務 → 世界模組映射）
        │  → 查詢 world_module_registry
        ▼
⑤ MRL_World_Module_Execution（世界模組執行）
        │  → 可呼叫外部 AI 作為 execution particle
        ▼
⑥ MRL_MemoryLayer_Writeback（記憶回寫）
        │  → checkpoint / merkle_root / trace_log
        ▼
⑦ MRL_Origin_Seal（封印）
        │  → origin_signature / output_hash / seal_time
        ▼
⑧ MRL_Product_Output（產品輸出）
        │  → partial_result（預設）/ full_result（解鎖後）
        ▼
⑨ MRL_ProofBundle（可選，輸出完整證明包）
```

---

## 2. 各步驟工程規格

### ① MRL_World_Gateway

**角色：** 產品對外入口，使用者看到的是世界，不是 API。

**職責：**
- 接收使用者輸入（文字、任務描述、檔案、指令）
- 進行初步意圖分析（不做 LLM 呼叫，僅做 pattern match + rule-based routing hint）
- 生成 `session_id`
- 轉交 ② Input Particleization

**輸入格式：**
```json
{
  "user_input": "...",
  "session_id": "auto-generated",
  "entry_type": "task | query | file | command",
  "user_id": "...",
  "timestamp": "ISO8601"
}
```

**不可包含：**
- LLM 呼叫邏輯
- 業務判斷邏輯
- 直接回應邏輯

---

### ② MRL_Input_Particleization

**角色：** 把使用者輸入轉化為 MRL 粒子結構。

**產出兩個核心粒子：**

**TaskAtom：**
```json
{
  "atom_type": "TaskAtom",
  "task_id": "uuid",
  "session_id": "...",
  "user_id": "...",
  "input_text": "...",
  "entry_type": "...",
  "intent_hint": "...",
  "priority": 0-9,
  "origin_signature": "MrLiouWord",
  "created_at": "ISO8601"
}
```

**TraceAtom：**
```json
{
  "atom_type": "TraceAtom",
  "trace_id": "uuid",
  "task_id": "...",
  "session_id": "...",
  "stage": "PARTICLEIZED",
  "agent_source": null,
  "origin_signature": "MrLiouWord",
  "timestamp": "ISO8601"
}
```

**不可包含：**
- LLM 呼叫
- 結果生成邏輯

---

### ③ MRL_ControlCenter

**角色：** 唯一路由中心。任何任務只能通過 ControlCenter 調度，不允許模組間直接呼叫。

**內部路由器：**

| 路由器 | 職責 |
|--------|------|
| `task_router` | 依 TaskAtom intent_hint 決定進入哪個 WorldModule |
| `memory_router` | 決定記憶讀取策略（現有記憶 / 新建 / 繼承 session） |
| `particle_router` | 管理粒子狀態流轉（QUEUED → RUNNING → DONE / FAILED） |
| `world_router` | 查詢 world_module_registry，派發執行者 |
| `persona_router` | 依任務類型選擇 persona / system prompt 策略 |

**任務狀態機：**
```
QUEUED → RUNNING → WAITING_TOOL → DONE → SEALED
                                ↘ FAILED → ARCHIVED
```

**關鍵規則：**
- 所有模組（api_gateway / conversation_manager / multi_agent）都必須通過 ControlCenter，不可繞過
- ControlCenter 不執行業務邏輯，只負責路由與狀態管理
- 每次路由決策寫入 TraceAtom

---

### ④ MRL_WorldMapping

**角色：** 把 TaskAtom 映射到正確的世界模組。

**WorldModule Registry（初版）：**

| Module ID | 觸發場景 | 描述 |
|-----------|----------|------|
| `Engineering_WorldModule` | 工程任務、程式碼、架構設計 | 工程執行世界 |
| `Document_Analysis_WorldModule` | 文件分析、PDF、報告 | 文件解析世界 |
| `Product_Output_WorldModule` | 產品方案、規格書輸出 | 產品產出世界 |
| `Code_Repair_WorldModule` | 程式碼修復、debug | 程式碼修復世界 |
| `Proof_Bundle_WorldModule` | 創作權、法律、時間戳 | 證明包產出世界 |
| `Deployment_WorldModule` | 部署、伺服器、環境 | 部署執行世界 |
| `Business_Strategy_WorldModule` | 商業分析、策略、定價 | 商業策略世界 |
| `Memory_Retrieval_WorldModule` | 記憶查詢、歷史重播 | 記憶檢索世界 |

**映射規則：**
- 可同時進入多個 WorldModule（並行執行）
- 映射決策記入 TraceAtom

---

### ⑤ MRL_World_Module_Execution

**角色：** 世界模組內部執行邏輯，可呼叫外部 AI 作為 execution particle。

**執行原則：**
1. 外部 AI（Qwen / OpenAI / Claude 等）是 **execution particle**，不是執行主體
2. 每次外部 AI 呼叫必須記錄 `agent_source`
3. 外部 AI 回應必須被 MRL 吸收（命名校正、粒子化）後才能成為結果
4. 執行失敗必須保留 `error_trace`，不可靜默失敗

**產出：**
```json
{
  "atom_type": "ResultAtom",
  "result_id": "uuid",
  "task_id": "...",
  "trace_id": "...",
  "world_module": "Engineering_WorldModule",
  "partial_result": "...",
  "full_result": "...",
  "agent_source": "qwen / openai / local",
  "origin_signature": "MrLiouWord",
  "status": "DONE | FAILED",
  "error_trace": null
}
```

---

### ⑥ MRL_MemoryLayer_Writeback

**角色：** 把執行結果與完整 trace 回寫入 MRL_MemoryLayer（七層記憶架構）。

**回寫內容：**

| 欄位 | 說明 |
|------|------|
| `session_id` | 會話識別 |
| `task_id` | 任務識別 |
| `trace_id` | 追蹤鏈 |
| `input_atom` | 原始輸入粒子 |
| `result_atom` | 結果粒子 |
| `merkle_root` | 本次記憶的 Merkle 根 |
| `checkpoint` | 狀態快照（可 replay） |
| `origin_signature` | `MrLiouWord` |
| `seal_pending` | 是否等待封印 |

**MemoryVaultPG 對接：**
- 回寫至 PostgreSQL（`03_memory/` 定義的表結構）
- 支援 `replay(session_id)` 重建完整對話與任務流
- 每次回寫觸發 Merkle 鏈更新

---

### ⑦ MRL_Origin_Seal

**角色：** 為每次輸出蓋章，建立不可抵賴的產出封印。

**封印內容：**
```json
{
  "atom_type": "SealAtom",
  "seal_id": "uuid",
  "task_id": "...",
  "trace_id": "...",
  "result_id": "...",
  "origin_signature": "MrLiouWord",
  "agent_source": "...",
  "runtime_origin": "DL580 | Cloudflare | external",
  "output_hash": "sha256(...)",
  "merkle_root": "...",
  "seal_time": "ISO8601",
  "accepted_by": "MrLiou"
}
```

**觸發時機：**
- 每次 full_result 產出時自動觸發
- streaming 完成後的最終 chunk 觸發
- 每次 proof_bundle 匯出時觸發

---

### ⑧ MRL_Product_Output

**角色：** 控制輸出分層（partial / full），對接 entitlement 系統。

**輸出規則：**

| 狀態 | 可見內容 |
|------|----------|
| 未解鎖 | `partial_result`（預覽、摘要、部分結果） |
| 已解鎖（付款 / 授權） | `full_result` + `proof_bundle` |
| Admin | 全部 + trace + seal + memory |

**每個輸出都必須包含：**
```json
{
  "origin_signature": "MrLiouWord",
  "task_id": "...",
  "trace_id": "...",
  "seal_id": "...",
  "output_type": "partial | full",
  "runtime_origin": "..."
}
```

---

### ⑨ MRL_ProofBundle（可選）

**角色：** 匯出完整的創作權 / 執行權 / 時間戳證明包。

**包含：**
- TaskAtom（原始輸入）
- TraceAtom 序列（完整 trace 鏈）
- ResultAtom（結果）
- SealAtom（封印）
- MemoryCheckpoint（記憶快照）
- MerkleRoot + Proof Path
- AgentSourceLedger（哪個外部 AI 產出了哪段內容）

**輸出格式：** `.json` / `.pdf` / `.zip`（含所有粒子的完整序列）

---

## 3. MRL_Agent_Source_Ledger

任何外部 AI 產出的內容，必須記入 Ledger：

```json
{
  "ledger_id": "uuid",
  "task_id": "...",
  "agent_source": "copilot | claude | chatgpt | qwen | local",
  "source_repo": "dofaromg/MRL_AI_SYSTEM",
  "source_pr": "PR #10",
  "source_commit": "5c3ee9e...",
  "content_type": "module | function | config | documentation",
  "absorbed_into": "MRL_MemoryInputAdapter",
  "absorption_status": "candidate | absorbed | rejected | archived",
  "accepted_by": "MrLiou",
  "origin_signature": "MrLiouWord",
  "timestamp": "ISO8601"
}
```

---

## 4. 關鍵設計原則總結

| 原則 | 說明 |
|------|------|
| **Particle First** | 任何輸入先粒子化，才能被母體處理 |
| **ControlCenter Only** | 所有路由通過 ControlCenter，禁止模組直連 |
| **External AI = Execution Particle** | 外部 AI 是執行工具，不是架構基礎 |
| **Every Output Sealed** | 所有輸出必須有 SealAtom（origin_signature + hash） |
| **Memory is Ground Truth** | MemoryLayer 是系統唯一真相來源，不是 session dict |
| **Proof Always Ready** | 任何任務都可匯出 ProofBundle |
| **No Silent Failure** | 失敗必須保留 error_trace，不可靜默 |

---

## 5. 與 PR #10 模組的對應關係

| PR #10 模組 | Mother Flow 步驟 | 介入方式 |
|------------|-----------------|---------|
| `api_gateway.py` | ① World_Gateway 外層 | 降級為 adapter，轉交 ControlCenter |
| `conversation_manager.py` | ⑥ MemoryLayer_Writeback | 作為 MemoryInputAdapter 提供 session 輸入 |
| `llm_adapter.py` | ⑤ World_Module_Execution | 作為 ExternalExecutionParticle 被呼叫 |
| `context_manager.py` | ③ ControlCenter 前置 | 提供 context 壓縮，不替代記憶層 |
| `streaming.py` | ⑧ Product_Output | 作為 Output Surface，觸發 Seal |
| `multi_agent.py` | ⑤ World_Module_Execution | 作為 WorldModule Worker |
| `scheduler.py` | ③ ControlCenter 任務佇列 | 提供 TaskClock 能力 |
| `config_manager.py` | 全層 | 設定提供者，強化 secret boundary |
| `mother_assembly.py` | 全流程啟動器 | 確認粒子層先於外部模組啟動 |

---

*本文件是 MRL 母體流程的 v1 規格。後續工程實作必須以本文件為基準，不可繞過任何步驟。*
*origin_signature: MrLiouWord*
