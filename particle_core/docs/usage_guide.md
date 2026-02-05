# MRLiou Particle Language Core 使用說明

## 概述

MRLiou 粒子語言核心系統是一個邏輯運算框架，支援函數鏈執行、邏輯壓縮與模組化處理。

## 核心概念

### 函數鏈 (Function Chain)

標準的 MRLiou 邏輯鏈包含五個核心步驟：

1. **STRUCTURE** - 定義輸入資料結構
2. **MARK** - 建立邏輯跳點標記
3. **FLOW** - 轉換為流程結構節奏
4. **RECURSE** - 遞歸展開為細部結構
5. **STORE** - 封存至邏輯記憶模組

### 壓縮格式

邏輯鏈可以壓縮為緊湊格式：
```
SEED(X) = STORE(RECURSE(FLOW(MARK(STRUCTURE(X)))))
```

## 使用方式

### CLI 模擬器

```bash
python src/cli_runner.py
```

提供互動式介面，包含：
- 邏輯模擬執行
- 函數鏈說明
- 壓縮/解壓縮測試

### 邏輯管線

```bash
python src/logic_pipeline.py
```

直接執行邏輯管線處理。

### 壓縮還原器

```bash
python src/rebuild_fn.py
```

處理 .flpkg 格式的壓縮與還原。

### 邏輯轉化器

```bash
python src/logic_transformer.py
```

進階的邏輯格式轉換工具。

## 檔案格式

### .fn 格式
人類可讀的函數表示格式，用於描述邏輯流程。

### .flpkg 格式
壓縮的邏輯封包格式，包含完整的模組資訊。

### .pcode 格式
偽代碼格式，可被 CLI 工具執行。

## 配置

系統配置位於 `config/core_config.json`，包含：
- 函數鏈定義
- 檔案格式設定
- 輸出配置
- 壓縮規則

## 範例

查看 `examples/` 目錄中的範例檔案：
- `sample_simulation.json` - 模擬執行結果
- `standard_logic.flpkg.json` - 標準邏輯封包

## 擴展

系統支援自定義函數鏈和預設規則，可通過配置檔案或程式介面進行擴展。