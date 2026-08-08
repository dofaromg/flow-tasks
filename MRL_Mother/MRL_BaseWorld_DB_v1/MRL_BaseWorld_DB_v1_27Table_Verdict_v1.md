# MRL_BaseWorld_DB_v1 — 27 表分歧裁決報告 v1（證據定論）

origin_signature: MrLiouWord
當下狀態：2026-05-29（沙盒）；本檔以**沙盒實跑 + 稽核文件**為證據，給出 canonical 裁決建議。

## 1. 問題重述

`MRL_BaseWorld_DB_v1` 存在兩套都號稱「27 表」的 schema，表集不相交。本檔以結構+邏輯+實跑證據定論。

## 2. 硬證據（沙盒實跑 + 稽核）

| 維度 | tar1 Schema 包（PascalCase） | tar2 Deploy 包（小寫） |
|---|---|---|
| 目標引擎 | **SQLite**（首行 `PRAGMA foreign_keys=ON`） | **PostgreSQL**（Dockerfile `postgres:16`） |
| 沙盒實跑 | ✅ sqlite 套用：**27 表 + 8 顯式索引 + Init + 9 FLTNZ 種子** | ✅ postgres 套用：**27 表** |
| 代表表 | Identity_Signature_Root / Canon_State / FLTNZ_Asset / Proof_Merkle / Trace_Log / Mirror_Record / Module_Registry … Cleanup_Decision | mrl_origin / mrl_state / mrl_projection / mrl_world_module / mrl_passport_* / mrl_persona / mrl_metaenv … |
| **SCHEMA_AUDIT.pdf** | ✅ **列出 27 PascalCase 表 + 完整外鍵圖，結論 PASS** | 未提及 |
| **Consistency_Check.pdf** | ✅ README↔Schema 一致性檢查（PascalCase） | 未提及 |
| Schema README 分層 | ✅ ROOT/Canon/FLTNZ/Memory/Mirror/Proof（PascalCase） | — |
| repo adapter 7 掛接點 | ✅ 對映（Canon/Registry/FLTNZ_Asset/Memory/Proof/Trace/Mirror） | ✗ 多數無對應表 |
| MAINLINE_BACKFILL 批次008 | — | ✅ 列為 canonical 27 表（schema-level-formal） |
| Dockerfile/compose 實際部署 | — | ✅ initdb 部署的是這套 |
| Mainline Batch015 docx 第24章 | — | ✅ FlowPassport 映射小寫表 |

## 3. 結構+邏輯判讀

兩套不是「同層競品」，而是**兩個世代 / 兩個引擎目標**：

- **PascalCase = 被正式稽核(SCHEMA_AUDIT/Consistency_Check)通過、外鍵完整、對映 repo adapter 的 canonical 資料模型**（SQLite 參考實作）。
- **小寫 = 目前綁在 DL580 Dockerfile 的 PostgreSQL 部署 initdb**（BACKFILL-008 / Batch015）。

矛盾的本質：**「被稽核 PASS 的 canonical（PascalCase）」與「實際部署到 DL580 的（小寫）」不是同一套。** 若照現狀部署，DL580 跑的是未經 SCHEMA_AUDIT 的小寫表，且 repo adapter 掛接點(Canon/Proof/Trace/Mirror/Registry)在該庫無對應。

## 4. 裁決建議（依證據權重）

**canonical = tar1 PascalCase Schema 包**，理由：唯一通過 SCHEMA_AUDIT（完整外鍵 PASS）+ Consistency_Check + 對映 repo adapter + 沙盒 27/8/9 實證。

**解決動作（建議）**：把 PascalCase canonical schema **移植為 PostgreSQL initdb**（母體獨立運行、可部署 DL580），取代目前發散的小寫 initdb，使「部署 = 被稽核的 canonical」。

## 5. 仍需擁有者確認的一點（誠實）

小寫那套有 BACKFILL-008 + Batch015 + Dockerfile 三處背書，**不能排除它是刻意的另一代 PostgreSQL 模型**。故在擁有者確認前：
- 不擅自改寫/刪除任一套（兩套皆已 additive 保留並實證）。
- 待確認後才執行「移植 PascalCase → postgres initdb 並對齊」。

## 6. 補充：Backfill.sql（本次上傳）內容

`MRL_BaseWorld_DB_Backfill_runtime5tables.sql` 含 5 張 **runtime 橋接表**（MRL_MetaIR_Record / MRL_ParticleIR_Node / MRL_RuntimeGraph_Edge / MRL_Attention_Route / MRL_Verification_Report），是 runtime↔BaseWorld 的接點，**非 27 表本身**；獨立定位、待起動。
