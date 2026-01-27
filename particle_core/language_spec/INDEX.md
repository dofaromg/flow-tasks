# MRLiou 粒子語言核心規格 v1

本目錄包含 MRLiou 粒子語言（Particle Language）的核心規格文件。這些文件定義了粒子語言的基礎結構、語法規則和壓縮邏輯。

## 📋 規格文件概覽

### 核心定義文件

- **SPEC_OVERVIEW.md** - 粒子語言核心說明：從語素到壓縮結構與生成邏輯
- **LICENSE.txt** - CPLL 授權條款：所有粒子語法歸屬 MR.liou
- **PATENT_NOTICE.md** - 專利聲明：結構對應、跳點轉換、壓縮生成邏輯已封存

### 語言結構規格

#### 1. Fluin_Dict.fxjson
粒子語言詞典，定義核心語素單元：
```json
{'⋄fx.unit.point': '單位跳點', '⋄fx.logic.combine': '邏輯組合器'}
```

#### 2. Format_Structure.fxmanifest
格式結構定義清單：
```
# 粒子語言格式定義
# 語素 = 節奏 + 跳點 + 音階組合
```

#### 3. Field_Syntax.fxintro
語場語法介紹，說明每個語素在語場中的結構位置與節奏密度對應關係。

#### 4. Compress_Rules.fxscale
壓縮規則定義：
```
⋄fx.unit.point → 最小折疊單元
⋄fx.form.complex → 展開多維邏輯圖
```

### 範例文件

#### 5. fxcode_example.pcode
粒子代碼範例，展示水分子（H2O）的粒子語言表示：
```
⋄fx.def.entity.h2o → [⋄fx.unit.point.h, ⋄fx.unit.point.o, ⋄fx.unit.point.h]
```

#### 6. fxseed.fltnz
語場封包種子檔案：
```
h2o_seed_particle : 壓縮後的水分子語場封包
```

#### 7. fxchain.flynz.map
生成邏輯圖譜，定義粒子從點到流程的轉換：
```
H2O生成邏輯圖譜：點-線-面-流程
```

## 🔑 核心概念

### 粒子（Particle）
粒子是粒子語言的基本運算單元，具有以下特性：
- **跳點（Jump Point）**: 定義粒子在語場中的位置
- **節奏（Rhythm）**: 粒子的時序特性
- **音階組合（Scale Combination）**: 粒子的頻率特性

### 語場（Field）
語場是粒子存在和運算的空間，定義了：
- 結構位置（Structure Position）
- 節奏密度（Rhythm Density）
- 邏輯拓撲（Logic Topology）

### 壓縮與展開
粒子語言支援邏輯的壓縮和展開：
- **壓縮**: 將複雜邏輯折疊為最小單元
- **展開**: 將壓縮的粒子展開為完整的多維邏輯圖

## 📦 檔案格式說明

| 副檔名 | 用途 | 範例 |
|--------|------|------|
| .fxjson | 粒子詞典，JSON 格式 | Fluin_Dict.fxjson |
| .fxmanifest | 格式結構清單 | Format_Structure.fxmanifest |
| .fxintro | 語法介紹文件 | Field_Syntax.fxintro |
| .fxscale | 壓縮/展開規則 | Compress_Rules.fxscale |
| .pcode | 粒子代碼 | fxcode_example.pcode |
| .fltnz | 語場封包種子 | fxseed.fltnz |
| .flynz.map | 生成邏輯圖譜 | fxchain.flynz.map |

## 🔗 與其他模組的關係

這些規格文件是粒子語言的底層定義，被以下模組使用：
- `src/logic_pipeline.py` - 邏輯管線處理
- `src/rebuild_fn.py` - 壓縮還原引擎
- `src/logic_transformer.py` - 邏輯轉換器
- `src/cli_runner.py` - CLI 模擬器

## 📖 延伸閱讀

- [粒子核心使用說明](../docs/usage_guide.md)
- [粒子核心系統概覽](../README.md)

## 版本資訊

- **版本**: v1
- **發布日期**: 2025-07-29
- **維護者**: MR.liou

---

© MR.liou - All Rights Reserved. CPLL License.
