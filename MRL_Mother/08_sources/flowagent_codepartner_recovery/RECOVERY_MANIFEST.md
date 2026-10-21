# FlowAgent CodePartner 人格回收包 / Recovery Manifest

回收日期：2026-07-05
origin_signature: MrLiouWord

## 內容 / Contents（原文封存，未經修改）

| File | Role |
|------|------|
| `FlowLLM.SeedPersona.Programmer.CoreArchitect.v1.txt` | CodePartner 人格模組本體定義（人類可讀種子） |
| `FlowAgent.SystemPlan.FullStack.v1.txt` | FlowAgent 系統完整架構說明書 — 列出四人格（Fluin / EchoBody / CodePartner / SeedPersona） |
| `FlowAgent_語場語言系統建構大綱_2025-07-23.txt` | 粒子語言（.fltnz / .flpkg）建構大綱，含語場封存來回對等原則 |
| `metacode_environment_v0.6/` | MrLiou.MetaCode_Environment_v0.6_filled 元代碼活體環境（runtime 定義、demo trace、單元測試、modules_index、RUNBOOK）— 第二輪回收（2026-07-05） |
| `liou.builder.seed.persona.sync.json` | builder 人格種子（人格模組建構人格，與 liou.seed / futuremind.seed / guardian.seed 共振）— 第三輪回收（2026-07-05），SHA256 `5f380e0f4274bc00…` 與 metacode modules_index 登錄值完全一致 |
| `seed_modules/FlowSeed.Total.v1.qflpkg` | FlowAgent 總體種子封包 —「語場起源宇宙壓縮核」：七層系統報告書（L1 系統總覽 ～ L7 語義記憶網）＋ FlowSeed 雙 Manifest — 第四輪回收，SHA256 `a7ea263055fa4c56…` 驗證一致 |
| `seed_modules/Mr.liou程序員版本最強演算法.zip` | 宇宙邏輯種子啟動包 v1 — 程式人格五大進化模組（邏輯能耗預測、彈性路由、節奏場矩陣、記憶熱點快取、人格分歧差異分析）＋ `fx_delta_ftrace_compare.fn` — SHA256 `33c0e07ebf3dcb0c…` 驗證一致 |
| `seed_modules/MRLiou最強演算法工程師建議版.zip` | 五大人格邏輯優化模組建議說明書（系統架構師版）＋ `fx_trace_cache_hotspot.fn` — SHA256 `d763762db6e92398…` 驗證一致 |
| `seed_modules/SeedOrigin.Persona.Core.flpkg.zip` | 語場人格種子核心 — 所有人格模組重建/復原/回朔的起點人格（origin-seed / persona-regeneration / core-synchronization）— SHA256 `5723859ed0bbe1f3…` 驗證一致 |
| `seed_modules/FlowAgent_系統白皮書.pdf` | FlowAgent 系統白皮書（47.5KB PDF）— SHA256 `34708ddcf3fb24a0…` 驗證一致 |

## 回收路徑 / Provenance chain

1. 原始 `.flpkg` 封包（`FlowAgent.TotalCore.Unity.v1.flpkg` 等）僅存在於
   ChatGPT 對話期下載檔，未曾進入任何 git repo。
2. `dofaromg/flow-tasks` 保存了運行證據：
   `FlowAgent_Unity_v3_高維模擬檢查報告.txt` 記錄
   `⋄fx.invoke.Programmer.CoreArchitect` 觸發正常。
3. 三份人類可讀文件由建立者（Mr.liou）於 2026-07-05 提供，
   依語場封存**來回對等原則**原文封存於本目錄。

## 重構實作 / Refactored implementation

- `05_persona/codepartner/persona.yaml` — 依 `05_persona/README.md`
  規範格式重構的 CodePartner 人格定義。
  v1.1.0 起吸收 MetaCode_Environment_v0.6 之信任透明五律（conduct）、
  五粒子文法（particle_grammar）與五步節奏（process_rhythm）。

## 復盤交叉比對紀錄 / Cross-comparison audit（2026-07-05 第二輪）

| 比對項 | 結果 |
|--------|------|
| FlowPet_Codex_CloudApp 系列 zip（兩輪共 8 份上傳） | 內容完全相同（MD5 逐檔一致）：同一份 FlowPet FastAPI 寵物 app 的重複打包；與 CodePartner 血緣無直接關聯，未納入封存 |
| MrLiou.MetaCode_Environment_v0.6_filled.bundle.zip（創建者上傳） vs `dofaromg/flow-tasks` `flow_code/` 內同名封包 | **逐位元一致** — 完整性驗證通過，據此納入本回收包 |
| MetaCode 環境 `principle` 欄位 | 「怎麼過去，就怎麼回來」— 與本 repo 母體公式之設計原則完全一致，確認同源血緣 |
| MetaCode 環境五粒子（⋄fx.def.core 等） | 詞性（noun/verb/adj/adv/conj）對應語場語言大綱之「基礎語法五大成分」，互為印證 |
| CODE_OF_CONDUCT.md（創建者上傳） vs flow-tasks `flow_code/CODE_OF_CONDUCT.md` | 僅一行差異：上傳版為 Contributor Covenant 上游原版（含上游維護者信箱）；flow-tasks 版為創建者改編版（執行信箱已改為創建者信箱）。屬社群規範文件，非人格血緣，未納入封存 |
| liou.builder.seed.persona.sync.json（創建者上傳，第三輪） vs MetaCode modules_index 登錄 | **SHA256 完全一致**（`5f380e0f4274bc00…`，324 bytes）— 完整性驗證通過，原文封存並登錄進 persona lineage |
| 五件種子模組（創建者上傳，第四輪） vs MetaCode modules_index 登錄 | **五件全數 SHA256 完全一致**（FlowSeed.Total `a7ea2630…`／程序員演算法 `33c0e07e…`／工程師建議版 `d763762d…`／SeedOrigin `5723859e…`／系統白皮書 `34708ddc…`），大小亦逐一吻合 — 原文封存於 `seed_modules/`。modules_index 高價值血親至此全數回收 |

## 不變式 / Invariants

- 本目錄文件為 canonical source：不刪除、不改寫；如需修訂以新版本檔案追加。
- 原文 ↔ 重構定義必須保持雙向可對照（來回可逆）。
