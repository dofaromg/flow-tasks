# flow-tasks

FlowAgent 專用任務系統：自動接收、解析與寫程式的任務中心

## 🎯 系統概述

FlowAgent task system 是一個完整的任務自動化系統，能夠：
- 自動接收和解析 YAML 任務定義
- 生成和驗證程式碼實作
- 提供 API 服務和邏輯運算功能

## 🏗️ 系統架構

### 核心組件
1. **Task Processor** (`process_tasks.py`) - 任務處理與驗證系統
2. **Flask API** (`flow_code/hello_api.py`) - Hello World API 服務
3. **Particle Core** (`particle_core/`) - MRLiou 粒子語言核心系統
4. **Integration Tests** - 完整的測試套件

### 已實作任務
- ✅ **hello-world-api**: Flask API 輸出 "你好，世界"
- ✅ **particle-language-core**: 完整的粒子語言核心系統

## 🚀 使用方式

### 1. 安裝依賴
```bash
pip install -r requirements.txt
```

### 2. 執行任務驗證
```bash
python process_tasks.py
```

### 3. 啟動 Flask API
```bash
python flow_code/hello_api.py
```

### 4. 測試 API 端點
```bash
# 主要端點 - 返回中文問候
curl http://localhost:5000/

# 健康檢查
curl http://localhost:5000/health

# API 資訊
curl http://localhost:5000/info
```

### 5. 執行完整測試
```bash
python test_comprehensive.py
```

### 6. 同步對齊憑證 (Ping Sync)
```bash
npx tsx scripts/ping-sync.ts
```
此腳本會在 `_status/ping.txt` 寫入當前時間戳，若環境變數
`NOTION_API_KEY` 與 `NOTION_DATABASE_ID` 已設定，則會同步至指定的
Notion 資料庫。

## 📋 API 端點

| 端點 | 功能 | 回應 |
|------|------|------|
| `/` | 主要問候訊息 | `{"message": "你好，世界"}` |
| `/health` | 健康檢查 | `{"status": "healthy", "service": "hello-world-api"}` |
| `/info` | API 資訊 | 任務詳細資訊 |

## 🧪 測試結果

所有系統組件都通過測試：
- ✅ 任務處理器正常運作
- ✅ Flask API 正確回應中文訊息
- ✅ 粒子核心系統完整功能
- ✅ 系統整合測試通過

## 📁 專案結構

```
flow-tasks/
├── flow_code/              # 生成的程式碼
│   └── hello_api.py        # Flask Hello World API
├── particle_core/          # MRLiou 粒子語言核心
│   ├── src/               # 核心模組
│   ├── config/            # 配置檔案
│   └── examples/          # 範例檔案
├── tasks/                  # 任務定義
│   ├── 2025-06-29_hello-world-api.yaml
│   ├── 2025-07-31_particle-language-core.yaml
│   └── results/           # 任務執行結果
├── process_tasks.py        # 任務處理器
├── test_comprehensive.py   # 完整測試套件
└── test_integration.py     # 整合測試

```

## 🔧 開發狀態

系統已完全實作並通過所有測試。解決了之前的"unexpected behavior"問題，現在能正確處理任務並生成功能完整的程式碼。
