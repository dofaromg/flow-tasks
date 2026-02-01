# 🧠 MrLiou AI SuperComputer v1.0

> **唯一裁決公設：只定義一致性可回返的循環，不定義狀態、不定義主體。**

## 這是什麼？

這不是「又一個框架」。

這是一台 **AI 用的電腦**：
- ✅ AI 可以透過 HTTP API 寫入檔案
- ✅ 所有寫入自動快照，可回返
- ✅ 所有操作記錄在 Merkle 鏈，可稽核
- ✅ 模組化架構，可擴充
- 🆕 **AI Fusion Stack** - 多 AI 提供者組合系統（新功能）

## 🌀 AI Fusion Stack (新功能)

**將多個 AI (OpenAI, Claude, Gemini) 像粒子一樣堆疊、疊加和循環執行**

支援 4 種融合模式：
- **Sequential** (順序融合): AI₁ → AI₂ → AI₃
- **Parallel** (並行融合): 所有 AI 同時處理，結果合併
- **Weighted** (加權融合): 按權重混合多個 AI 回應
- **Möbius Loop** (莫比烏斯循環): 輸出循環回饋作為輸入直到收斂

查看完整文檔：[`docs/AI_FUSION_GUIDE.md`](docs/AI_FUSION_GUIDE.md)

### 快速示範

```bash
# 列出所有融合清單
curl http://127.0.0.1:8787/ai/fusion/manifests

# 執行順序融合
curl -X POST http://127.0.0.1:8787/ai/fusion/execute \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Explain quantum entanglement", "manifest": "sequential_refine"}'

# 執行莫比烏斯循環
curl -X POST http://127.0.0.1:8787/ai/fusion/mobius \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Design a sustainable city", "max_cycles": 5}'
```

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
| **🆕 `/ai/fusion/manifests`** | GET | **列出所有 AI 融合清單** |
| **🆕 `/ai/fusion/execute`** | POST | **執行融合堆疊** |
| **🆕 `/ai/fusion/mobius`** | POST | **執行莫比烏斯循環** |
| **🆕 `/ai/fusion/custom`** | POST | **自訂融合配置** |

## 📁 專案結構

```
MrLiou_AI_SuperComputer/
├── flowcore_loop.py       # 核心 Runtime
├── modules_loader.py      # 模組載入器
├── run.sh                 # 啟動腳本
├── ai_fusion_core.py      # 🆕 AI 融合核心
├── fusion_strategies.py   # 🆕 融合策略
├── fusion_manifests/      # 🆕 融合配置清單
│   ├── sequential_refine.manifest.json
│   ├── parallel_consensus.manifest.json
│   └── mobius_evolve.manifest.json
├── memory/                # 資料層
│   ├── ingest/raw/       # 原始輸入
│   ├── ingest/fusion/    # 🆕 融合輸出
│   ├── ingest/mobius/    # 🆕 莫比烏斯循環記錄
│   ├── snapshot/         # 自動快照
│   ├── domain/           # 領域資料
│   └── derived/l1/       # 衍生資料
├── log/                   # 稽核日誌
└── docs/                  # 文檔
    ├── AI_FUSION_GUIDE.md  # 🆕 AI 融合指南
    └── SUPERCOMPUTER_QUICKSTART.md
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
