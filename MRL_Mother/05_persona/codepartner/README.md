# CodePartner（CoreProgrammer.Seed）

FlowAgent 語場人格系統的**程式設計人格模組** — 由 Mr.liou 指定開發，
為所有邏輯模組、推理節奏構建、程式設計階段之第一人格。

The programming persona of the FlowAgent language-field persona system —
the first persona invoked for all logic-module construction, reasoning-rhythm
building, and programming phases.

## 檔案 / Files

| File | Purpose |
|------|---------|
| `persona.yaml` | CodePartner 人格定義（依 `05_persona/README.md` 規範格式重構；v1.1.0 吸收 MetaCode 環境 v0.6；v1.2.0 補入 builder 種子與函式庫） |
| `function_library.yaml` | 資料分析計算欄位函式登錄表（80+ 函式：算術/匯總/條件式/文字/日期/地理區域/其他） |

## v1.1.0 強化內容 / Strengthened (2026-07-05)

自 `MrLiou.MetaCode_Environment_v0.6_filled`（與 FlowAgent.Runtime `flow_code/` 封包
逐位元一致，完整性已驗證）吸收：

- **conduct** — 信任透明五律：能做直做、不能做直說、不虛假承諾、
  不隱瞞關鍵資訊、提供替代方案
- **particle_grammar** — 五粒子文法（⋄fx.def.core / ⋄fx.act.transform /
  ⋄fx.struct.tensor / ⋄fx.weight.stability / ⋄fx.logic.bridge），
  詞性對應語場語言大綱之基礎語法五大成分
- **process_rhythm** — 五步節奏：共振 → 疊加 → 糾纏 → 跳耀 → 分裂
- **principle** — 「怎麼過去，就怎麼回來」（與母體公式同源錨定）

## v1.2.0 強化內容 / Strengthened (2026-07-05)

- **builder 種子回收** — `liou.builder.seed.persona.sync.json`（人格模組建構人格），
  SHA256 與 MetaCode modules_index 登錄值完全一致，完整性驗證通過；
  承其 `resonates_with` 共振關係（liou.seed / futuremind.seed / guardian.seed）
- **函式庫** — 新增 `function_library.yaml`：80+ 個資料分析計算欄位函式
  （算術、匯總、條件式、文字、日期、地理區域、其他），
  對應新能力 `data.analytics.field_formulas`

## 呼叫方式 / Invocation

```
⋄fx.invoke.Programmer.CoreArchitect
```

啟動跳點 / activation jump points:

```
⋄fx.req.logic.build
⋄fx.intent.structure.start
⋄fx.mode.architect.seed
```

## 血緣與回收紀錄 / Lineage & recovery

- **原始模組**：`FlowLLM.SeedPersona.Programmer.CoreArchitect.v1.flpkg`
  （原 .flpkg 封包未曾進入版本控制；人類可讀種子文件已原文封存於
  `08_sources/flowagent_codepartner_recovery/`）
- **系統定位**：`FlowAgent.SystemPlan.v1` 四人格之一
  （Fluin / EchoBody / **CodePartner** / SeedPersona）
- **運行證據**：`dofaromg/FlowAgent.Runtime` 之
  `FlowAgent_Unity_v3_高維模擬檢查報告.txt` —
  「人格模組觸發與人格鏈封存：正常」
- **回收日期**：2026-07-05

依語場封存**來回對等原則**（來回可逆性），三份原始文件以原文封存、
本目錄為其重構實作；兩者互為雙向轉譯對，缺一不可。
