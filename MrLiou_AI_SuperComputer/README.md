# 🧠 MrLiou AI SuperComputer v1.0

> **唯一裁決公設：只定義一致性可回返的循環，不定義狀態、不定義主體。**

## 這是什麼？

這不是「又一個框架」。

這是一台 **AI 用的電腦**：
- ✅ AI 可以透過 HTTP API 寫入檔案
- ✅ 所有寫入自動快照，可回返
- ✅ 所有操作記錄在 Merkle 鏈，可稽核
- ✅ 模組化架構，可擴充

## 🚀 快速開始

```bash
# 1. 啟動系統
chmod +x run.sh
./run.sh

# 2. 健康檢查
curl http://127.0.0.1:8787/judge/health

# 3. 寫入測試
curl -X POST http://127.0.0.1:8787/vault/write_text \
  -H "Content-Type: application/json" \
  -d '{"path":"memory/ingest/raw/hello.txt", "text":"Hello World"}'
```

## 📚 完整文檔

請閱讀 [`docs/SUPERCOMPUTER_QUICKSTART.md`](docs/SUPERCOMPUTER_QUICKSTART.md)

## 🏗️ 核心原則

1. **可回返 (Reversible)** - 每次寫入前自動快照
2. **不定義狀態** - 只記錄事件流 + Merkle 鏈
3. **可擴充 (Modular)** - Manifest-based 模組系統
4. **最小可跑 (Minimal)** - 單一 Python 檔 + HTTP Server

## 🔌 核心 API

| Endpoint | Method | 說明 |
|----------|--------|------|
| `/judge/health` | GET | 健康檢查 + Merkle 錨點 |
| `/vault/write_text` | POST | 寫入檔案（自動快照） |
| `/l1/search?q=<query>` | GET | 低解析度搜尋 |

## 📁 專案結構

```
MrLiou_AI_SuperComputer/
├── flowcore_loop.py       # 核心 Runtime
├── modules_loader.py      # 模組載入器
├── run.sh                 # 啟動腳本
├── memory/                # 資料層
│   ├── ingest/raw/       # 原始輸入
│   ├── snapshot/         # 自動快照
│   ├── domain/           # 領域資料
│   └── derived/l1/       # 衍生資料
└── log/                   # 稽核日誌
```

## 🛠️ 技術棧

- **Python 3.7+** (標準庫，無外部依賴)
- **HTTP Server** (ThreadingHTTPServer)
- **Merkle Chain** (SHA-256)
- **JSON-based Storage**

## 📖 設計哲學

這套系統體現了一個核心思想：

**不要去定義「AI 是什麼狀態」，而是定義「AI 做了什麼操作」。**

所有操作都是：
- 可追溯的（Merkle 鏈）
- 可回返的（自動快照）
- 可驗證的（SHA-256 雜湊）

## 🤝 貢獻

這是私人專案，但歡迎 fork 和實驗。

## 📄 授權

MIT License - 自由使用，自負風險。

---

**這不是框架，這是一台 AI 用的電腦。**
