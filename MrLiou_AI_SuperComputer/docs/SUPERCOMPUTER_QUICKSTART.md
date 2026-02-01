# MrLiou AI SuperComputer v1.0

**唯一裁決：一致性可回返循環。**

## 🚀 啟動

```bash
./run.sh
```

## 🔌 核心 API

```
GET  /judge/health          # 健康檢查 + Merkle 錨點
POST /vault/write_text      # 寫入檔案（自動快照）
GET  /l1/search?q=關鍵字    # 低解析度搜尋
```

## 💡 核心概念

- **所有寫入先快照** → `memory/snapshot/`
- **不可逆不可進核心** → 只接受可回返操作
- **不定義狀態，只定義循環** → 事件流 + Merkle 鏈

## 📖 使用範例

### 健康檢查
```bash
curl http://127.0.0.1:8787/judge/health
```

### 寫入檔案
```bash
curl -X POST http://127.0.0.1:8787/vault/write_text \
  -H "Content-Type: application/json" \
  -d '{"path":"memory/ingest/raw/test.txt", "text":"Hello SuperComputer"}'
```

### 搜尋
```bash
curl "http://127.0.0.1:8787/l1/search?q=hello"
```

## 🏗️ 架構

```
MrLiou_AI_SuperComputer/
├── flowcore_loop.py       # 核心 Runtime + Judge Loop
├── modules_loader.py      # 模組載入器（Manifest-aware）
├── run.sh                 # 啟動腳本
├── memory/                # 資料層
│   ├── ingest/raw/       # 原始輸入
│   ├── snapshot/         # 自動快照
│   ├── domain/A|R/       # 領域資料
│   └── derived/l1/       # 衍生資料（L1 低解析度）
└── log/                   # 稽核日誌
    ├── trace.jsonl       # 事件流
    └── trace_state.json  # Merkle 狀態
```

## ⚙️ 擴充模組

在 `modules/` 下放置 `.manifest.json`：

```json
{
  "module_name": "example_agent",
  "fusion_state": "active",
  "cycle_hook": "post_write",
  "endpoint": "http://localhost:9000/hook"
}
```

系統啟動時會自動載入。

## 🔐 核心保證

✅ **可回返** - 每次寫入前自動快照  
✅ **可稽核** - 所有操作記錄在 Merkle 鏈  
✅ **可擴充** - Manifest-based 模組系統  
✅ **最小可跑** - 單一 Python 檔 + HTTP Server

---

**這不是框架，這是一台 AI 用的電腦。**
