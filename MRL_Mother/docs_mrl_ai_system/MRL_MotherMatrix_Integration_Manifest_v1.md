# MRL 母體整合清單 v1 — MotherMatrix Integration Manifest

> 法則：**Additive-Only**。本清單只新增、只定位、不刪除、不覆蓋。
> 母體（MRL Mother）為最高權威，所有外部檔案一律視為母體吸收之知識／技術／訓練模組與能力的映射，
> 一律回收、轉換、定位回母體系統名稱產物，給予位置，等待起動。

- 分支：`MRL_Branch_MotherMatrix_Integration_Stack_v1`（堆疊於 `main`）
- 模式：堆疊標記（stack-mark）／additive 吸收
- 對等關係：與主流（mainstream/`main`）維持對等，不取代、不降級

---

## 1. 母體分層架構（既有，最高權威錨點）

| 層 | 位置 | 角色 |
|---|---|---|
| 00 | `00_rootlaw/` | 根法則 |
| 01 | `01_schema/` | 結構綱要 |
| 02 | `02_principles/` | 原則 |
| 03 | `03_memory/` | 記憶 |
| 04 | `04_runtime/` | 運行時 |
| 05 | `05_persona/` | 人格 |
| 06 | `06_trace/` | 軌跡 |
| 07 | `07_ingest/` | 吸收／攝入 |
| 08 | `08_sources/` | 來源 |
| 09 | `09_workflow/` | 工作流 |
| — | `MRL_Mother/` `MRL_Runtime/` `MRL_Symbolic/` `MRL_Adapters/` | 母體主體模組 |

---

## 2. 本次吸收定位（External → Mother，additive，待起動）

來源分支：`MRL_Branch_StructureField_Rename_Alignment_v1`
吸收方式：以 additive 方式置入母體 repo，原檔名不變、無覆蓋（main 上原不存在）。
狀態一律標記 **待起動（PENDING-ACTIVATION）**，等待母體 runtime 起動納編。

### 2.1 通用運行語言核心 — `MRL_UniversalRuntimeLanguage_Core_v1/`

| # | 吸收位置 | 母體定位 | 狀態 |
|---|---|---|---|
| 1 | `MRL_UniversalRuntimeLanguage_Core_v1/__init__.py` | 核心入口 | 待起動 |
| 2 | `…/README.md` | 核心說明 | 待起動 |
| 3 | `…/MRL_Language/MRL_UniversalParser_Core.py` | 語言層·通用解析核心 | 待起動 |
| 4 | `…/MRL_Language/MRL_MetaIR_Compiler.py` | 語言層·MetaIR 編譯 | 待起動 |
| 5 | `…/MRL_Language/MRL_MrLiouIR_Compiler.py` | 語言層·MrLiouIR 編譯 | 待起動 |
| 6 | `…/MRL_Language/MRL_ParticleIR_Engine.py` | 語言層·粒子 IR 引擎 | 待起動 |
| 7 | `…/MRL_Language/MRL_PerceptionKernel.py` | 語言層·感知核 | 待起動 |
| 8 | `…/MRL_Language/__init__.py` | 語言層入口 | 待起動 |
| 9 | `…/MRL_Runtime/MRL_WorldRuntime.py` | 運行時·世界運行 | 待起動 |
| 10 | `…/MRL_Runtime/MRL_DL580_Runtime.py` | 運行時·**DL580**（下一步建構錨點） | 待起動 |
| 11 | `…/MRL_Runtime/MRL_PersistentLoop.py` | 運行時·持久迴圈 | 待起動 |
| 12 | `…/MRL_Runtime/MRL_ReplayRestore_Core.py` | 運行時·重播還原核 | 待起動 |
| 13 | `…/MRL_Runtime/MRL_RuntimeGraph_Builder.py` | 運行時·圖構建 | 待起動 |
| 14 | `…/MRL_Runtime/MRL_RuntimeStructureField.py` | 運行時·結構場（StructureField） | 待起動 |
| 15 | `…/MRL_Runtime/MRL_Verification.py` | 運行時·驗證 | 待起動 |
| 16 | `…/MRL_Runtime/__init__.py` | 運行時入口 | 待起動 |
| 17 | `…/MRL_DB/MRL_BaseWorld_DB_Adapter.py` | 資料·BaseWorld 介接（27 tables 外部支持／本 repo 待驗證） | 待起動·待驗證 |
| 18 | `…/MRL_DB/MRL_Registry.py` | 資料·登錄表 | 待起動 |
| 19 | `…/MRL_DB/__init__.py` | 資料層入口 | 待起動 |
| 20 | `…/MRL_External/__init__.py` | 外部介接層入口 | 待起動 |
| 21 | `…/MRL_PersistentLoop_Daemon_v1_SPEC.md` | 規格·持久迴圈守護 | 待起動 |
| 22 | `…/MRL_RUNTIME_CIVILIZATION_STACK_ACCEPTANCE_REPORT.md` | 報告·文明堆疊驗收 | 待起動 |
| 23 | `…/acceptance/MRL_Runtime_Acceptance_TestSuite.py` | 驗收·測試套件 | 待起動 |
| 24 | `…/scripts/MRL_runtime_civilization_run.py` | 腳本·文明運行 | 待起動 |
| 25 | `…/docs/MRL_StructureField_Visualization.dot` | 圖示·結構場(dot) | 待起動 |
| 26 | `…/docs/MRL_StructureField_Visualization.json` | 圖示·結構場(json) | 待起動 |
| 27 | `…/docs/MRL_StructureField_Visualization.mmd` | 圖示·結構場(mermaid) | 待起動 |
| 28 | `…/docs/MRL_Verification_Report.md` | 報告·驗證 | 待起動 |
| 29 | `…/docs/MRL_WorldRuntime_Report.md` | 報告·世界運行 | 待起動 |

### 2.2 母體 docs／tests／workflow 吸收

| # | 吸收位置 | 母體定位 | 狀態 |
|---|---|---|---|
| 30 | `docs/MRL_StructureField_Layer_Ownership_v1.md` | 母體文件·結構場層級歸屬 | 待起動 |
| 31 | `tests/test_MRL_universal_runtime_core.py` | 母體測試·通用運行核 | 待起動 |
| 32 | `.github/workflows/MRL_GitHub_Mirror.yml` | CI·GitHub 鏡像 | 待起動 |

---

## 3. 法則聲明（不可違反）

1. **不刪除**：任何已吸收檔案皆保留，視為母體產物映射。
2. **不覆蓋**：本次吸收皆為 main 上原不存在之檔，零覆蓋。
3. **給位置**：每一檔皆已在第 2 節獲得母體定位。
4. **等待起動**：狀態統一為「待起動」，由母體 runtime 後續納編起動。
5. **主流對等**：本堆疊與 `main` 維持對等，不取代主流。
6. **最高權威**：外部一律為母體吸收之知識／技術／訓練模組與能力，回收轉換回母體系統名稱產物。

---

## 4. 下一步（DL580 建構錨點）

DL580 運行時錨點已吸收定位：
`MRL_UniversalRuntimeLanguage_Core_v1/MRL_Runtime/MRL_DL580_Runtime.py`

相關既有分支（遠端，可後續堆疊）：
- `MRL_Branch_DL580_PIDScope_Layer_v1`
- `MRL_Branch_DL580_Workflow_PIDScope_v1`
- `claude/dl580-cloudflared-deploy-xoopz`

> 轉向 DL580 建構時，以此錨點為起點，沿用 additive 法則向母體 runtime 起動納編。

### 4.1 DL580 已起動納編母體 crown（v2.3，additive）

`09_workflow/MRL_mother_assembly.py`（MotherAssembly，早期母體 crown）已 additive 接入 DL580：

- `__init__`：新增 `self.dl580`（母體自運行節點）
- `boot()`：新增第 16 子系統 `dl580_runtime`（`_boot_dl580()`，沿用 `_try_import` 優雅降級）
- `run_dl580(source, lang, loop_id)`：母體驅動 DL580 canonical 管線，結果封入 MerkleChain，**無 Prompt→LLM→Output 路徑**
- 內建工具 `dl580_run` 已註冊進 ToolRegistry
- `status()`：新增 `dl580_runtime` 健康欄位
- `ASSEMBLY_VERSION`：`2.0 → 2.3`

**本機驗收（offline）：**
- MotherAssembly boot → `dl580_runtime: ok`，`status.dl580_runtime: True`
- 母體 → DL580 全管線：`MRL_RUNTIME_ACCEPTANCE_PASS` 6/6
- 文明驗收套件：接受度 6/6 + 命名驗證 9/9，exit 0
- 既有不變更：版本常數由測試以 import 比對，未破壞 `test_mother_assembly.py`

---

## 5. RuntimeOS 企業級執行平台吸收（v1.4.0，additive，318 檔）

來源：使用者上傳套件 `MRL_RuntimeOS_EnterpriseRuntimePlatform_CoreExecutable_v1_4_0.zip`
吸收位置：repo 根層同名目錄（main 上原不存在 → 零覆蓋零刪除，318 檔）。
上傳之 5 個獨立檔（report / RuntimeGraph json / AIModelGateway js / service unit）皆與包內 byte-identical，隨包一併吸收，無重複放置。

### 5.1 正式產品子服務定位（依報告命名規則）

| 子服務 | 位置 |
|---|---|
| `MRL_RuntimeOS_AIModelGateway_Service_v1` | `MRL_Services/MRL_RuntimeOS_AIModelGateway_Service_v1.js` |
| `MRL_RuntimeOS_SkillModule_Service_v1` | `MRL_Services/MRL_RuntimeOS_SkillModule_Service_v1.js` |
| `MRL_RuntimeOS_ArtifactTransfer_Service_v1` | `MRL_Services/MRL_RuntimeOS_ArtifactTransfer_Service_v1.js` |
| `MRL_RuntimeOS_3DModelBridge_Service_v1` | `MRL_BlenderBridge/MRL_RuntimeOS_3DModelBridge_Service_v1/` |
| Core / LanguageAdapters / Runtime / API / Mesh / Node / Security / Enterprise / OpenAPI / Deploy / Docs | 同名子目錄，全部給位置 |

### 5.2 沙盒實跑驗收結果（嚴守「不可誤標」）

| 項目 | 真實狀態 |
|---|---|
| Node RuntimeOS 多語言管線驗收（`MRL_Acceptance_TestSuite.js`） | **PASS**（8 語言 `verification_pass: true`，exit 0，沙盒） |
| DL580 smoke（`MRL_Smoke_Dl580.js`，server 起於 :8788） | **PASS**（health/execute/verify，沙盒 runtime 路徑，**非真實 AI 模型**） |
| AIModelGateway | 真 connector（Ollama / OpenAI-compatible）；**模型可用性需實機 `OLLAMA_HOST` / OpenAI endpoint 後驗收** |
| 3DModelBridge / Blender | source integrated；**Blender runtime（`bpy`）待實機** |
| SkillModule | 可列出 / 執行 / 持久化技能執行紀錄 |

### 5.3 不可誤標（沿用報告約束）

> 不得寫成 DL580 已上線、Blender 已跑通、Ollama 真模型已存在。
> 沙盒僅驗證 runtime 管線與 HTTP 路徑；真實模型／Blender 須實機配置後才可升格。

---

## 6. 依序完成進度（當下狀態 2026-05-29，沙盒；非永久結論）

| # | 項目 | 當下狀態 | 升格條件 |
|---|---|---|---|
| 1 | git push / PR #43 / 遠端驗收 | ✅ 完成（沙盒）— PR #43 open，CI 全綠 | — |
| 2 | 母體吸收 32 檔 + DL580 起動 v2.3 | ✅ 完成（沙盒）— mother→DL580 6/6 PASS | — |
| 3 | RuntimeOS v1.4.0 套件吸收（318 檔） | ✅ 完成（沙盒）— 多語言管線 8/8、DL580 smoke PASS | — |
| 4 | BaseWorld adapter 本地鏡像 | ✅ 完成（沙盒）— 7 掛接點 round-trip OK、未知點拒絕 | — |
| 5 | BaseWorld **正式 27-table** schema 對齊 | 🟡 部分（沙盒）— schema 已入 repo、沙盒 Postgres 實建 27 表 PASS；**但發現兩套分歧 schema，canonical 歸屬待裁決**；live DL580 待實機 | 擁有者裁決 canonical schema + 實機 `MRL_BaseWorld_DB_v1` DSN |
| 6 | AIModelGateway 真模型 | ⏳ 待實機 — 真 connector 已驗，模型不存在於沙盒 | 實機 `OLLAMA_HOST` 或 OpenAI-compatible endpoint + key |
| 7 | 3DModelBridge Blender runtime | ⏳ 待實機 — source integrated，`bpy` 依賴 Blender | 實機 Blender 環境 |
| 8 | DL580 真機上線 | ⏳ 待實機 — 沙盒 runtime/HTTP 路徑已驗 | DL580 真機 host 部署驗收 |
| 9 | 失落舊產出 `d9ef615` / `Canonical_Report_v1.md` | ❌ 不可復原（本環境）— 未偽造 | 使用者提供原檔則可 additive 補回 |

> 第 5–8 項皆**非程式可在沙盒完成**，需外部資源；一律標「待實機」，不得標 PASS/已完成。
> 第 9 項在本 ephemeral 環境不可復原，已誠實標示，未以重打方式偽造原稿。
