# MRL_Runtime_Canonical_Report_v1

origin_signature: `MrLiouWord`
branch: `MRL_Branch_Runtime_Convergence_Audit_v1`（base = `main` @ `17248be`）
type: **Runtime Canon 收斂審計**（Canon / Conflict / Mirror / Proof / Restore Chain）
laws: **LAW-2 additive（不刪除、不覆蓋）** · 候選以 reference + sha256 登錄（不 bulk-copy 進 main）

> 目的：把多套既有 Runtime 收斂為 Canon 視圖，**不新增第四套 Runtime、不刪除任何候選**。
> 命名違規一律標 **待正名**，不得作為刪除理由（LAW-2）。

---

## 0. 收口紀律（本報告遵守）

1. additive — 不刪、不覆蓋任何候選。
2. 候選 = reference + sha256；不 bulk-copy 原始碼進 main。
3. 命名違規 → `待正名`（非刪除理由）。
4. BaseWorld 27 tables → `外部審計支持／本 repo 待驗證`（不得寫成 repo 內已驗證）。
5. `d1_schema.sql` → LAW-0 / LAW-2 concrete piece；**不**取代 BaseWorld 全量驗收。
6. 回填主文件 → 僅「待驗證收斂紀錄」，不得寫成 Runtime 主體已升格。

---

## 1. CANON RECORD（候選登錄；reference + proof-anchor）

| ID | 候選 Runtime | 層責任 | 語言 | 來源 | proof-anchor | 命名 |
|---|---|---|---|---|---|---|
| **A** | `MRL_UniversalRuntimeLanguage_Core_v1`（Python IR 核心） | Language / IR / core execution | Py | **PR #37**（OPEN, 未入 main） | git `98a74d87…`（#37 head） | ✅ v2 compliant（MrLiouIR/StructureField/Perception） |
| **B** | `MRL_Workflow_PIDScope`（ownership 層） | ownership / process / PID / recovery | Node | **main** | git-blob index.js `8f709334…` · runtime_structurefield.js `ed08e557…` | ✅ compliant（ScopeGraph→StructureField 已正名） |
| **C** | `MRL_DL580_Engine`（7700 Bridge / CF-Worker-compat） | particle 引擎 / KV(Redis)+D1(PG) shim / bridge | Node | upload `fa424c45` | sha256 server.js `602d6048…` · worker-adapter `5aac3351…` · package `149261d6…` · INSTALL `2369a752…` · START `8ef91da8…` | ⚠️ **待正名**（`attention` worker/binding） |
| **D** | `MRL_UniversalRuntimeLanguage_Core` **JS v1.2.0** | Language / IR（JS 重實作） | Node | upload `6c4ecb3f` | sha256 zip `1db44a4d…` | ⚠️ **待正名**（`MetaIR`/`Graph`/`AttentionKernel` 為 canonical 檔名，違 v2 §5） |
| **E** | `MRL_Mother_Product_Runtime_v1_0_0` | product runtime（engine + lib/*） | Node | upload `6c4ecb3f` | sha256 zip `e1fdd754…` | 大致 compliant（待逐檔驗） |
| **F** | `MRL_3D_AI_Reconstruction_System_v1` | WorldModule 3D（SFM/COLMAP/NBV） | Py | upload `6c4ecb3f` | sha256 zip `f2f6658c…` | ⚠️ **待正名**（`Attention`/`Graph`）+ 外部 COLMAP/OpenMVS adapter 合法 |
| **G** | FlowCore Loop 家族（v0.1/0.2/0.3/1.1.0/1.3.0） | closed-loop runtime（merkle/replay/restore/revert） | Py | upload `2abc9048` + repo `04_runtime/flowcore_loop.py` | sha256 v1.1.0 `978350df…` · V03 `b6bb651a…` · v0.2 `07ae0521…` · 1.3.0 `bac7b403…` · V0.1 zip `b0119b7e…`；repo git `165f5eea…` | 大致 compliant（FlowCore 用 PersonaGate，不用 Graph 主體） |
| **I** | `MRL_RuntimeServer.js`（API surface） | 界門 /health /mrl/state /api/mrl/runtime/convergence | Node | **main** | git-blob `477a4031…` | ✅ compliant |
| **H** | `d1_schema.sql`（LAW concrete piece） | DB schema（NO_DELETE + signature 觸發器） | SQL | upload `6c4ecb3f` | sha256 `304a506e…` | ✅ compliant（LAW-0/LAW-2） |
| (ref) | `MRL_GitHub_Copilot_BuildPack_v0_5` | spec/prompt（**非 runtime**） | doc | upload `6c4ecb3f` | sha256 zip `dcc4cc7a…` | 參考材料，不列入 runtime 候選 |

> 註：部分 upload 批次為 ephemeral，sha256 為**本 session 實算之 proof-anchor**；若日後正式併回，須重新上傳並比對。

---

## 2. CONFLICT RECORD（B1 命名 / B2 層重疊 / B3 宣稱）

### B-NAME（命名衝突 → 待正名，非刪除理由）
- **D**（JS v1.2.0）：`MRL_MetaIR.js` / `MRL_RuntimeGraph_Builder.js` / `MRL_AttentionKernel_Router.js` 以 `MetaIR/Graph/Attention` 作 canonical 主體 → 違反 v2 §5。**待正名** → `MrLiouIR/StructureField/Perception`，或降為 alias。
- **F**（3D）：`MRL_Attention_ViT` / `MRL_Attention_Fusion` / `MRL_Camera_Graph` → **待正名**。
- **C**（DL580 Engine）：`attention` worker + `ATTENTION` binding → **待正名**。

### B-LAYER（層重疊；多候選同層 → 待選主體，不刪）
- Language/IR core：**A（Py #37）** ⟷ **D（JS v1.2.0）** — 雙語言雙實作。
- closed-loop / replay-restore：**G（FlowCore ×5）** ⟷ **A（ReplayRestore_Core）** ⟷ **B（PIDScope recovery）**。
- particle 引擎 / bridge：**C（DL580 7700）** ⟷ **E（Mother Product Runtime）**。
- ownership / process：**B（PIDScope）** — 目前唯一，無重疊。

### B-CLAIM（宣稱衝突 → 待驗證）
- BaseWorld 表數：`13`（DATABASE_INTEGRATION_REPORT）⟷ `27`（指令/收斂包）→ **待驗證**。
- DL580 硬體 `6×V100 (NVIDIA)` ⟷ FastFlowLM（AMD Ryzen NPU）→ 不同加速器，**外部對照**，非同一執行體。
- 「167/144 Workers 已部署」⟷ C 之 server.js 實載 7 worker 且 `./workers/*.js` 未隨附 → **未證實**。

---

## 3. MIRROR RECORD（來源映射；LAW-2 additive，by reference）

| ID | 主來源 | 是否在 main | 登錄方式 |
|---|---|---|---|
| A | PR #37 branch | 否（OPEN） | reference（PR head sha） |
| B | main `MRL_Runtime/MRL_Workflow_PIDScope/` | 是 | in-repo（git blob） |
| C | upload `fa424c45/*` | 否 | reference + sha256 |
| D | upload `6c4ecb3f/a2a1868e…zip` | 否 | reference + sha256 |
| E | upload `6c4ecb3f/284394d7…zip` | 否 | reference + sha256 |
| F | upload `6c4ecb3f/d17dc3d9…zip` | 否 | reference + sha256 |
| G | upload `2abc9048/*` + repo `04_runtime/flowcore_loop.py` | 部分（repo 有 1 份） | reference + sha256 / git blob |
| H | upload `6c4ecb3f/11017abb-d1_schema.sql` | 否 | reference + sha256 |
| I | main `MRL_RuntimeServer.js` | 是 | in-repo（git blob） |

**未** bulk-copy 任何候選原始碼進 main（符合收口紀律 #2）。

---

## 4. PROOF（sha256 / git）

見 §1 proof-anchor 欄。全部於本 session 實算（sha256sum / git hash-object / git rev-parse）。

---

## 5. RESTORE CHAIN（可逆 / replay / restore 能力盤點）

| 候選 | 可逆能力 | 驗證狀態 |
|---|---|---|
| G FlowCore v1.1.0 | `verify_chain` + `revert_to_height` + **`revert_to_merkle_root`**（怎麼過去就怎麼回來） | 本 session 實跑 `DeliverableValidator: PASS`（LOC 877 / replay OK / chain valid） |
| A #37 `MRL_ReplayRestore_Core` | exact replay / restore / rollback / time-trace | #37 acceptance A–F PASS（於 #37 樹實跑） |
| B PIDScope `runtime_recovery.js` | restart→recovery；`MRL_PIDSCOPE_ACCEPTANCE_PASS`（含 F. persistent loop survive restart） | 於整合樹實跑 PASS |
| repo `09_workflow/fltnz_parser.py` | txt↔fltnz↔flpkg↔trace 可逆 + checksum | 既有單元測試 |
| H `d1_schema.sql` | LAW-2 NO_DELETE（additive history = restore 底材） | schema 正確；**未**在 live DB 驗收 |

**Restore Chain Canon 狀態：PARTIAL** — 各候選各有可逆/replay 能力且多處實跑 PASS，但**尚無**單一統一、跨候選串接的 canon restore chain 驗證物件。

---

## 6. PASS / FAIL（本審計收口）

| 檢項 | 結果 |
|---|---|
| Canon Record 建立 | **PASS** |
| Conflict Record 建立 | **PASS** |
| Mirror Record 建立 | **PASS** |
| Proof（sha256/git）登錄 | **PASS** |
| Restore Chain 盤點 | **PARTIAL**（無統一 canon chain） |
| 未刪除任何候選（LAW-2） | **PASS** |
| 未新增第四套 Runtime | **PASS** |
| 未 bulk-copy 進 main | **PASS** |
| BaseWorld 27 tables 標記正確（外部支持／待驗證） | **PASS** |

---

## 7. 下一步（不新增 Runtime；先收斂再升格）

1. **命名收斂**：對 C/D/F 之 `attention/graph/metair` 執行 `待正名 → Perception/StructureField/MrLiouIR`（或降 alias）。
2. **層主體選定**（待 MrLiou 裁示）：Language/IR core 於 A(Py) vs D(JS) 擇一為主體、另一為 candidate/adapter。
3. **Restore Chain 統一**：以 FlowCore v1.1.0 之 `revert_to_merkle_root` 為基準，串接 A/B 形成 canon restore chain + 統一驗證物件。
4. **BaseWorld**：以 `d1_schema.sql`（LAW-0/LAW-2）為 concrete 起點；27-table 全量仍待真實 DB 驗收。
5. PR #37 先 merge → 給 A 一個 main 落點，再做層主體升格。

origin_signature: `MrLiouWord`
