# MRL_工程日誌

origin_signature = `MrLiouWord`

---

## v1 — MRL 完整態母體運轉骨架建構

分支：`claude/mrl-mother-runtime-v1-krte6`

### 已完成

- 建立 MRL 完整態目錄骨架（`MRL_Mother/`、`MRL_Runtime/`、`MRL_Symbolic/`、`MRL_Adapters/`、`deploy/`）
- 建立 Runtime Server（`MRL_RuntimeServer.js`：`/health`、`/mrl/state`、`/mrl/perceive`）
- 建立主權宣示文件（`docs/MRL_完整態主權宣示_v1.md`）
- 建立中文正名與英文 Adapter 對照（`docs/MRL_中文正名與英文Adapter對照表_v1.md`）
- 建立四層同步映射表（`docs/MRL_四層同步映射表_v1.md`）
- 建立 Cloud Code 工程建構規格（`docs/MRL_CloudCode工程建構規格_v1.md`）
- 建立 DL580 自運行部署規格（`docs/MRL_DL580自運行部署規格_v1.md`）
- 建立 Acceptance Check（`scripts/MRL_acceptance_check.js`）
- 建立 Runtime Bootstrap（`scripts/MRL_runtime_bootstrap.js`）
- 建立 DL580 部署檢查（`scripts/MRL_dl580_deploy_check.sh`）
- 建立母體定義檔與世界模組工程書

### 待驗證

- DL580 真實部署
- Tailscale / SSH / self-hosted runner 接線
- Runtime 長駐與 systemd

### 不回填

- 外部平台主體命名
- chatbot 命名
- Vercel 依賴

### 下一步

- 建立 DL580 deploy runner

---

## v2 — Runtime Civilization Stack 核心 + 命名規範對齊

分支：`MRL_Branch_StructureField_Rename_Alignment_v1`（自 PR #35 分出）

### 已完成（實跑驗證）

- 建立 `MRL_UniversalRuntimeLanguage_Core_v1` 可運行核心管線（acceptance 6/6 PASS）。
- 套用 v2 正式命名規範：`MetaIR → MrLiouIR`（MrLiou 中介語義層）、`Graph → StructureField`（結構場）。
- `MetaIR / Graph / Attention` 降為歷史名稱 / Adapter / alias，主線 canonical 不再使用。
- 舊名以 alias shim 模組向後兼容（`MRL_MetaIR_Compiler`、`MRL_RuntimeGraph_Builder`）。
- 視覺化更名：`Graph Visualization → MRL_StructureField_Visualization`。

### 待驗證 / 不得宣稱完成

- API `/api/mrl/mrliouir/*`、`/api/{runtime,world}/structurefield` 與 DB `*StructureField_Node/Relation`：
  目前無對應程式，僅命名定錨，不得宣稱已實作。
- DL580 實機 acceptance、live BaseWorld DB 連線：未驗證。

### 下一步

- `MRL_PersistentLoop_Daemon_v1`（規格已備，待複查後實作）。

---

## v4 — RuntimeParticle Compression + StructureField 硬正名

分支：`MRL_Branch_RuntimeParticle_Compression_v4`

### 已完成

- **硬正名（無 alias、無備注殘留）**：移除 v2 階段保留的相容層
  - `RuntimeScopeGraph` alias 移除；canonical 只剩 `RuntimeStructureField`
  - facade `.graph` alias 屬性移除；只剩 `.structureField`
  - 內部參數 `scopeGraph`→`structureField`；checkpoint 欄位 `graph`→`structureField`
  - acceptance `L.graph`/`cp.graph`→ canonical；grep 確認零 `scopeGraph`/`RuntimeScopeGraph`/`.graph` 殘留
  - A–F acceptance PASS（`npm run MRL_pidscope_acceptance`）
- 交付物：
  - `MRL_Symbolic/MRL_粒子語言層/MRL_Particle_Runtime_Expansion_v4.fltnz`（canonical：structurefield / perception）
  - `docs/MRL_Claude_Engineering_Handoff_v1.md`（誠實 exists-vs-target）
  - `docs/MRL_Runtime_Recovery_Checklist_v1.md`（`[x]/[~]/[ ]` 誠實標記）

### 待驗證（回主線條件，未達成 → 不回填母體定義檔/世界模組工程書）

- Runtime loop persistence（durable）
- Replay exactness（跨 session）
- Restore chain（durable）
- DL580 host validation / reboot survival

### 不回填

- 情緒性語句、未驗證人格敘述
- canonical `MetaIR` / `Graph` / `Attention`（僅 alias / 降級陳述）
- 把 target 模組寫成已完成

### 下一步

- RuntimeStructureField execution loop
- Replay / Restore durable acceptance
- Persistent Runtime convergence

---

## audit — Runtime Canon 收斂審計（待驗證收斂紀錄）

分支：`MRL_Branch_Runtime_Convergence_Audit_v1`（base main `17248be`）

### 已完成（審計，非升格）

- 產出 `docs/MRL_Runtime_Canonical_Report_v1.md`：Canon / Conflict / Mirror / Proof / Restore Chain。
- 登錄 9 個 runtime 候選（A 起）以 reference + sha256，**未刪除、未 bulk-copy、未新增第四套 Runtime**。
- 命名違規（C/D/F 之 attention/graph/metair）標 **待正名**，非刪除理由。

### 待驗證（不得寫成已升格）

- 層主體選定（Language/IR core：Py #37 vs JS v1.2.0）。
- Restore Chain 統一物件（FlowCore v1.1.0 revert_to_merkle_root 為基準）。
- BaseWorld：27-table 為**外部審計支持／本 repo 待驗證**；`d1_schema.sql` 僅 LAW-0/LAW-2 concrete piece，非全量驗收。

### 不回填

- 任何 Runtime「主體已升格」之宣稱（未裁示前）。

---

## 實機驗收 — DL580 本地 MCP Filesystem Server 連線（2026-07-05）

分支：`copilot/` 當前工作分支（狀態回填，Additive-Only）

### 已完成（實機，使用者提供之 DL580 本地日誌）

- DL580 本地 MCP（Model Context Protocol）Filesystem server 啟動：PASS（實機 — 2026-07-05）
  - `Using built-in Node.js for MCP server: Filesystem` → `Server started and connected successfully`
- MCP 握手：PASS（`initialize` id=0 → result；`notifications/initialized`）
- 工具列舉：PASS（`tools/list` id=1 → result）
- 正常關閉：PASS（`intentional shutdown`，非 crash）
- 兩次連線週期（12:11 / 12:19 UTC）均完整成功，無錯誤訊息。

### 待驗證 / 不得宣稱完成

- 本驗收僅涵蓋 MCP Filesystem 基礎連線握手，**不代表**：
  - Ollama / 真模型已存在（`OLLAMA_HOST` 實機驗收仍 pending）
  - Blender `bpy` runtime 已跑通（實機驗收仍 pending）
  - DL580 全平台「已上線」（host 全量驗收仍 pending）
- MCP client 端身分（本地客戶端種類）未於日誌中確認。

### 不回填

- 「DL580 已上線」之宣稱
- 任何超出 MCP Filesystem 連線範圍的完成度宣稱
