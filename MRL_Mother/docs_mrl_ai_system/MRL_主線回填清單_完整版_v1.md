# MRL 主線回填清單（完整版）v1

> origin_signature: `MrLiouWord`  
> 當下狀態日期：2026-06-29（沙盒）  
> 文件性質：依模板實填之「可直接審核版」  
> 模板來源：`/home/runner/work/MRL_AI_SYSTEM/MRL_AI_SYSTEM/docs/MRL_主線回填清單模板_v1.md`

---

## 0. 使用範圍與誠實邊界

- 本文件僅回填「主線治理層」可確認資訊。
- 涉及 `DL580` / `真模型` / `runtime 實機鏈路` 未取得實機證據者，一律維持 `PENDING`。
- 本文件結論皆為**當下狀態**，非永久結論。

---

## 1. 回填分級（實填）

### 1.1 已完成（可回填）

| 項目 | 證據 | 驗收環境 | 當下狀態 |
|---|---|---|---|
| 新增主線回填模板（治理文件） | `docs/MRL_主線回填清單模板_v1.md` 已存在 | 沙盒 | PASS（2026-06-29） |
| 主線附錄已掛載模板入口 | `docs/MRL_主線收斂與分支條例_附錄_v1.md` 行首區段已有「執行模板」絕對路徑 | 沙盒 | PASS（2026-06-29） |
| PIDScope 驗收腳本可獨立執行 | `npm run MRL_pidscope_acceptance` 輸出 `MRL_PIDSCOPE_ACCEPTANCE_PASS` | 沙盒 | PASS（2026-06-29） |

### 1.2 待驗證（僅可 pending）

| 項目 | 缺口 | 需要的驗證 | 當下狀態 |
|---|---|---|---|
| `MRL_acceptance` 全驗收 | 本地未啟動 `127.0.0.1:8790` runtime endpoint | 啟動本地 runtime 後重跑 `npm run MRL_acceptance` | PENDING（2026-06-29，沙盒） |
| DL580 實機 runtime 鏈路 | 本次無實機環境證據 | DL580 host 實跑與證據回填 | PENDING（2026-06-29） |
| 真模型端點（Ollama/OpenAI/Anthropic） | 本次無實機/真實 endpoint 驗證 | 實機 `OLLAMA_HOST` 或雲端金鑰端到端驗收 | PENDING（2026-06-29） |

### 1.3 不回填

| 項目 | 不回填原因 | 保存方式 |
|---|---|---|
| PR #37 舊分支內容再次合入 | 附錄判定該分支內容已在 `main`，再合會「以舊覆新」 | 附錄標記 `[已併入·可關閉]`，不再 merge |
| PR #19 舊時 UI/API 歷史分支直接回主線 | 基底久遠，疑似被後續主線演進取代 | 附錄保全，待人工確認獨有價值 |
| PR #47 雜項 worker 名稱調整直接升格主線基準 | 非主線核心，避免干擾收斂主體 | 附錄保全，快合或關閉皆可 |

---

## 2. Additive-Only 檢查（實填）

- [x] 本輪僅新增/定位/標記，未刪除既有檔案  
- [x] 本輪未覆蓋主線既有內容  
- [x] 舊分支若已被主線吸收，已標記為「已併入·可關閉」  
- [x] 外部/歷史材料以附錄/治理文件保留來源與位置  

---

## 3. 候選分支差異盤點（先比對再決策）

| 候選分支/PR | 主線缺口 | 已存在於主線 | 是否被新版本取代 | 回填決策 |
|---|---|---|---|---|
| #49 `claude/memory-system-rules-prep-EuBXH` | deny-by-default 真引擎修正作為主線基準 | 否（依附錄敘述為主線本體候選） | 否 | 主線本體（先行） |
| #37 `MRL_Branch_StructureField_Rename_Alignment_v1` | 無新增缺口（附錄載明核心包已在 `main`） | 是 | 是（分支較舊） | 不回填、建議關閉 |
| #19 `copilot/add-missing-features-to-mrl-agi` | 待人工確認是否仍有獨有增量 | 不明（附錄標示疑被取代） | 高機率是 | 附錄保全，不阻塞主線 |
| #47 `update_worker_name_to_mrliousilly` | 雜項 chore，非主線核心 | 不影響主線 | 不適用 | 快合或關閉（附錄線） |

---

## 4. 回填主文件（治理層先行）

| 文件絕對路徑 | 更新目的 | 狀態 |
|---|---|---|
| `/home/runner/work/MRL_AI_SYSTEM/MRL_AI_SYSTEM/docs/MRL_主線收斂與分支條例_附錄_v1.md` | 主線處置、PR 狀態與 pending 邊界基準 | 已存在並可引用（當下狀態） |
| `/home/runner/work/MRL_AI_SYSTEM/MRL_AI_SYSTEM/docs/MRL_主線回填清單模板_v1.md` | 執行模板（空白版） | 已完成（當下狀態） |
| `/home/runner/work/MRL_AI_SYSTEM/MRL_AI_SYSTEM/docs/MRL_主線回填清單_完整版_v1.md` | 本次實填交付（可直接審核） | 已完成（當下狀態） |

五段式回填紀錄（本批次）：
1. 已完成：模板與完整版治理文件已建立，主線附錄入口可用。  
2. 待驗證：`MRL_acceptance`、DL580、真模型端點仍待實機/鏈路證據。  
3. 不回填：#37 舊分支再合、#19 舊基底直接升格、#47 非核心雜項。  
4. 回填主文件：附錄 + 模板 + 本完整版。  
5. 下一步：以本清單驅動逐項驗證與處置。  

---

## 5. 主線整合順序（實填）

1. 主線本體（#49）  
2. 附錄 PR 處置（#37 關閉建議；#19/#47 人工裁示）  
3. 僅吸收已確認增量，不以歷史分支覆寫主體  

本輪排序執行狀態（治理層）：
- [x] Step 1 已定義（基準已在附錄明確）  
- [x] Step 2 已定義（處置策略已表列）  
- [x] Step 3 已定義（Additive-Only 與不覆新原則已落地）  

---

## 6. 驗收與狀態標示（實填）

| 驗收項目 | 沙盒 | 實機 | 當下狀態標示 |
|---|---|---|---|
| 回填文件一致性 | PASS | N/A | PASS（2026-06-29，沙盒） |
| runtime 實跑（`MRL_pidscope_acceptance`） | PASS | PENDING | PASS（沙盒）/ 實機待驗證 |
| runtime 驗收（`MRL_acceptance`） | FAIL（endpoint 未啟動） | PENDING | PENDING（需 127.0.0.1:8790） |
| DL580 驗收 | N/A | PENDING | PENDING（待實機） |
| 真模型端點 | N/A | PENDING | PENDING（待實機 endpoint） |

---

## 7. 最終輸出（主線回填清單）

| 回填項目 | 來源分支/PR | 回填性質 | 證據 | 狀態 | 是否進主線 |
|---|---|---|---|---|---|
| 主線治理模板 | 本 repo 現況 | governance | `docs/MRL_主線回填清單模板_v1.md` | PASS | 是 |
| 主線回填完整版清單 | 本 repo 現況 | governance | 本文件 | PASS | 是 |
| #49 主線本體定位 | 附錄記錄 | governance/mainline baseline | `docs/MRL_主線收斂與分支條例_附錄_v1.md` §1/§2 | PARTIAL（附錄依據） | 待合併動作 |
| #37 再合入 | 附錄記錄 | governance disposition | 同上 §2 | PENDING（待關閉處置） | 否 |
| #19/#47 直接升格 | 附錄記錄 | governance disposition | 同上 §2 | PENDING（待人工裁示） | 否（暫） |

---

## 8. 回填批次摘要

- 批次編號：`MRL_MAINLINE_BACKFILL_20260629_01`
- 執行日期：2026-06-29
- 執行環境：沙盒
- 本輪結論（當下狀態）：
  - 已完成：治理層模板與完整版清單已落地，可直接用於審核與追蹤。
  - 待驗證：`MRL_acceptance` endpoint、DL580、真模型端點。
  - 不回填：舊分支覆新類路徑（#37 再合入）、未確認價值舊基底直升（#19）、非核心雜項升格（#47）。
  - 下一步：依本清單逐項補實機證據，完成 pending 項目後再更新狀態。

---

## 9. 依據來源（本 repo）

- `/home/runner/work/MRL_AI_SYSTEM/MRL_AI_SYSTEM/docs/MRL_主線收斂與分支條例_附錄_v1.md`
- `/home/runner/work/MRL_AI_SYSTEM/MRL_AI_SYSTEM/docs/MRL_Claude_Engineering_Handoff_v1.md`
- `/home/runner/work/MRL_AI_SYSTEM/MRL_AI_SYSTEM/docs/MRL_主線回填清單模板_v1.md`
- `/home/runner/work/MRL_AI_SYSTEM/MRL_AI_SYSTEM/package.json`
