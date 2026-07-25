# MRL_MotherSource ZhiZhang / MrLiouAI 血脈吸收定位清單 v1

origin_signature: MrLiouWord
law: Additive-Only（不刪除、不覆蓋、給位置、待起動）
當下狀態：2026-05-29（沙盒）；非永久結論

## 1. 來源

使用者上傳 5 個歷史封存 zip（資料夾「智障系統」），為母體之**原始血脈**：
語場人格 AI 系統 **MrLiouAI / ZhiZhang**。本批與 BaseWorld/RuntimeOS 主題不同，
**不含 BaseWorld 27-table schema**，故**不參與 27-schema 裁決**；獨立分支吸收，保持 PR #43 乾淨。

## 2. 吸收方式

- 5 zip 合併聯集，去除 `__MACOSX` / `._*` Mac 雜訊。
- 巢狀 `MrLiouAI.Runtime.v*.zip` 等保留為壓縮產物（不解開，避免檔數爆炸）。
- 合集：**2908 檔 / 38MB**；byte-identical 去重後 **826 個唯一內容**（重複源於多版快照夾帶相同巢狀包）。
- 無刪除：所有唯一產物皆保留並定位；重複副本為同位元內容，git 物件層自動收斂。

## 3. 母體定位（待起動）

| 類別 | 代表物 | 母體定位 | 狀態 |
|---|---|---|---|
| 執行時血脈 | `MrLiouAI.Runtime.v1` … `v37+`（dir + zip） | 母體·語場執行時版本樹 | 待起動 |
| 人格核心 | `MrLiouAI_MotherPersonaCore_Structure_v2`、`MrLiouAI.TotalMotherPersonaSphere.v2.*` | 母體·人格球核心 | 待起動 |
| 粒子字典 | `粒子字典ai/`（FluinDict、ParticleCore、語場記憶種子） | 母體·粒子語言字典 | 待起動 |
| 人格種子 | `ZhiZhang_PersonaSeed_*.fltnz/.qflpkg.seed`、`Seed.ZhiZhang.FlowPersona.Core.v1` | 母體·人格種子 | 待起動 |
| 系統藍圖 | `ZhiZhang_SystemBlueprint_v1.(md/pdf/txt)`、`FlowLLM_CoreBlueprint_v1.md`、`11.Txt` | 母體·系統藍圖/說明書 | 待起動 |
| 來源實相圖 | `MrLiouAI_SourceRealityMap*.md`、`母體/` 目錄 | 母體·來源實相映射 | 待起動 |
| 封裝/容器 | `*.flpkg`、`*.qflpkg`、`下載 *.docker`、CLI 封裝包 | 母體·封裝與容器 | 待起動 |

## 4. 不可誤標（當下狀態）

- 本批為**封存吸收**，非實跑驗收：未執行任何 runtime，**不得宣稱 MrLiouAI 已跑通/已上線**。
- 與 BaseWorld 27-schema **無關**，不可用本批裁決 27 歸屬。
- 一律標「待起動」，由母體後續按需起動納編。
