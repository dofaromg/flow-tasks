# MRL Copilot Agents 使用指南

本文件說明如何在此 repository 中使用 MRL 工程代理矩陣（GitHub Copilot Cloud Agent）。

代理定義檔位於 [`.github/agents/`](../.github/agents/)，合併進預設分支後即由 Copilot cloud agent 自動載入。  
全域操作規則請參閱 [`.github/copilot-instructions.md`](../.github/copilot-instructions.md)。

---

## 五個代理一覽

| 代理名稱 | 檔案 | 職責 |
|---|---|---|
| **mrl-planner** | [mrl-planner.agent.md](../.github/agents/mrl-planner.agent.md) | 將模糊需求轉為可審計的實作計劃（範圍凍結、預期檔案清單、相依樹、驗收標準、驗證策略） |
| **mrl-implementer** | [mrl-implementer.agent.md](../.github/agents/mrl-implementer.agent.md) | 依凍結範圍實作程式碼，保持相依完整性，完成後輸出 DELIVERY_PASS / DELIVERY_FAIL |
| **mrl-test-specialist** | [mrl-test-specialist.agent.md](../.github/agents/mrl-test-specialist.agent.md) | 新增與改善測試，不修改生產行為（除非明確要求），輸出覆蓋率表格 |
| **mrl-audit-supervisor** | [mrl-audit-supervisor.agent.md](../.github/agents/mrl-audit-supervisor.agent.md) | 審計 PR 或任務結果，執行四個稽核階段，產出 MRL Audit Report |
| **mrl-docs-release** | [mrl-docs-release.agent.md](../.github/agents/mrl-docs-release.agent.md) | 依已驗證的程式碼變更更新 README、文件、changelog 和 PR 描述 |

---

## 建議工作流程

```
Planner → Implementer → Test Specialist → Audit Supervisor → (Docs/Release)
```

**每次 merge 前必須執行 `mrl-audit-supervisor`，並確認回傳 `DELIVERY_PASS` 且覆蓋率 100%，任務才算完成。**

---

## 各步驟 Prompt 範本

### Step 1 — Planner（需求規劃）

```
Use agent: mrl-planner

需求：
<在此貼上你的需求描述>

請產出：
- 凍結範圍（Frozen Scope）
- 預期檔案清單
- 相依樹
- 實作計劃（含順序與 rollback 點）
- 驗證計劃
- MRL 稽核表格（Requested | Planned | Missing | Extra | Risk | Coverage）
```

### Step 2 — Implementer（實作）

```
Use agent: mrl-implementer

依照以下 Planner 產出的計劃實作：
<貼上 Planner 產出>

完成後請輸出：
- 變更檔案清單
- 相依鏈影響範圍
- 驗證命令及結果
- Requested vs Generated diff 稽核
- DELIVERY_PASS 或 DELIVERY_FAIL
```

### Step 3 — Test Specialist（測試）

```
Use agent: mrl-test-specialist

請針對以下變更範圍補充或改善測試：
<描述需要測試的行為或貼上 Implementer 輸出>

完成後請提供：
- 新增或修改的測試檔案
- 每個測試涵蓋的行為說明
- 測試命令執行結果
- MRL 覆蓋率表格（Requested behavior | Test coverage | Missing tests | Risk | Status）
```

### Step 4 — Audit Supervisor（稽核，merge 前必做）

```
Use agent: mrl-audit-supervisor

請稽核目前 PR / branch 的交付結果：
- 原始需求：<貼上原始需求>
- 預期檔案數：<N>

請執行四個稽核階段（Stage 00–03）並輸出 MRL Audit Report，
包含 DELIVERY_PASS 或 DELIVERY_FAIL 最終裁定。
```

### Step 5 — Docs/Release（文件與發布，視需要執行）

```
Use agent: mrl-docs-release

請依以下已驗證的程式碼變更更新相關文件：
<貼上變更摘要或 Implementer 輸出>

請輸出：
- 修改的文件檔案及原因
- 任何文件缺漏風險
- MRL 稽核表格（Code change | Documentation updated | Missing docs | Risk | Status）
```

---

## 重要提醒

- **`mrl-audit-supervisor` 是 merge 前的強制關卡**。未通過稽核（非 `DELIVERY_PASS`）或覆蓋率未達 100%，任務視為 **DELIVERY_FAIL**，不得合併。
- 代理檔案位於 `.github/agents/`，合併進預設分支後 Copilot cloud agent 即自動識別。
- 路徑導向指令（Python、前端、測試）位於 `.github/instructions/`，由 Copilot 依檔案路徑自動套用。
- 全域規則（七條不可為）與完成閘門定義請見 [`.github/copilot-instructions.md`](../.github/copilot-instructions.md)。
