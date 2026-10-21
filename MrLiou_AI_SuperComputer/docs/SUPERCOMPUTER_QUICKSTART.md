# MrLiou AI SuperComputer v1.0

**唯一裁決：一致性可回返循環。**

## 🚀 啟動

```bash
./run.sh
```

## 🔌 核心 API

### 基礎功能 / Basic Functions
```
GET  /judge/health          # 健康檢查 + Merkle 錨點 / Health check + Merkle anchor
POST /vault/write_text      # 寫入檔案（自動快照）/ Write file (auto snapshot)
GET  /l1/search?q=關鍵字    # 低解析度搜尋 / Low resolution search
```

### AI 功能 / AI Functions  
```
GET  /ai/providers          # 列出所有可用的 AI 提供商 / List all available AI providers
POST /ai/complete           # 同步 AI 完成 / Synchronous AI completion
POST /ai/stream             # 串流 AI 完成 / Streaming AI completion
```

## 💡 核心概念

- **所有寫入先快照** → `memory/snapshot/`
- **不可逆不可進核心** → 只接受可回返操作
- **不定義狀態，只定義循環** → 事件流 + Merkle 鏈
- **多提供商支援** → 統一介面，自動容錯

## 🤖 AI 提供商設定 / AI Provider Setup

### 1. 設定環境變數 / Set Environment Variables

複製範本並填入 API 金鑰：/ Copy template and fill in API keys:

```bash
cp config/env_template.txt .env
# 編輯 .env 並填入您的 API 金鑰 / Edit .env and fill in your API keys
```

範例 / Example:
```bash
export OPENAI_API_KEY=sk-...
export ANTHROPIC_API_KEY=sk-ant-...
export GOOGLE_API_KEY=...
```

### 2. 支援的提供商 / Supported Providers

| 提供商 / Provider | 模型範例 / Model Example | 說明 / Description |
|------------------|-------------------------|-------------------|
| OpenAI | gpt-4, gpt-3.5-turbo | OpenAI GPT models |
| Claude | claude-3-opus-20240229 | Anthropic Claude |
| Gemini | gemini-pro | Google Gemini |
| Ollama | llama2, mistral | Local models |
| Azure OpenAI | gpt-4 | Azure OpenAI Service |

### 3. 設定檔 / Configuration

編輯 `config/ai_providers.json` 來自訂提供商設定：
Edit `config/ai_providers.json` to customize provider settings:

```json
{
  "default_provider": "openai",
  "fallback_enabled": true,
  "fallback_order": ["openai", "claude", "ollama"],
  "providers": {
    "openai": {
      "enabled": true,
      "model": "gpt-4",
      ...
    }
  }
}
```

### 4. ⚠️ 安全與隱私注意事項 / Security & Privacy Considerations

**重要提醒 / Important Notices:**

- **提示詞會被保存到磁碟** / Prompts are persisted to disk  
  所有 AI 請求的提示詞和回應都會保存在 `memory/ingest/ai_responses/` 目錄中，用於完整的審計追蹤和 Merkle 鏈驗證。請勿在提示詞中包含敏感資訊（PII、API 金鑰、機密數據等）。  
  All AI request prompts and responses are saved in `memory/ingest/ai_responses/` for complete audit trails and Merkle chain verification. Do not include sensitive information (PII, API keys, confidential data) in prompts.

- **無身份驗證機制** / No authentication mechanism  
  目前 HTTP 端點沒有身份驗證。請勿在公開網路上暴露此服務。  
  HTTP endpoints currently have no authentication. Do not expose this service on public networks.

- **費用追蹤** / Cost tracking  
  所有 AI 請求的成本會記錄在 `log/ai_costs.jsonl` 中。請定期監控以避免意外費用。  
  All AI request costs are logged in `log/ai_costs.jsonl`. Monitor regularly to avoid unexpected charges.

## 📖 使用範例 / Usage Examples

### 健康檢查 / Health Check
```bash
curl http://127.0.0.1:8787/judge/health
```

### 寫入檔案 / Write File
```bash
curl -X POST http://127.0.0.1:8787/vault/write_text \
  -H "Content-Type: application/json" \
  -d '{"path":"memory/ingest/raw/test.txt", "text":"Hello SuperComputer"}'
```

### 搜尋 / Search
```bash
curl "http://127.0.0.1:8787/l1/search?q=hello"
```

### 列出 AI 提供商 / List AI Providers
```bash
curl http://127.0.0.1:8787/ai/providers
```

**回應範例 / Response Example:**
```json
{
  "ok": true,
  "providers": [
    {
      "provider": "OpenAIProvider",
      "model": "gpt-4",
      "available": true
    },
    {
      "provider": "OllamaProvider", 
      "model": "llama2",
      "available": false
    }
  ]
}
```

### AI 完成（預設提供商）/ AI Completion (Default Provider)
```bash
curl -X POST http://127.0.0.1:8787/ai/complete \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Explain quantum computing in simple terms"}'
```

**回應範例 / Response Example:**
```json
{
  "ok": true,
  "request_id": "abc123...",
  "content": "Quantum computing uses quantum mechanics...",
  "provider": "openai",
  "model": "gpt-4",
  "usage": {
    "prompt_tokens": 10,
    "completion_tokens": 150,
    "total_tokens": 160
  },
  "cost": {
    "input_tokens": 10,
    "output_tokens": 150,
    "estimated_cost_usd": 0.0093
  },
  "response_path": "memory/ingest/ai_responses/20260201120000_abc123.json",
  "merkle_root": "a1b2c3..."
}
```

### AI 完成（指定提供商）/ AI Completion (Specific Provider)
```bash
curl -X POST http://127.0.0.1:8787/ai/complete \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Write a haiku about AI",
    "provider": "claude",
    "options": {
      "temperature": 0.9,
      "max_tokens": 100
    }
  }'
```

### 串流回應 / Streaming Response
```bash
curl -X POST http://127.0.0.1:8787/ai/stream \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Count from 1 to 5",
    "provider": "ollama"
  }'
```

**回應格式（SSE）/ Response Format (SSE):**
```
data: {"chunk": "1"}

data: {"chunk": ", 2"}

data: {"chunk": ", 3"}

data: [DONE]
```

## 🏗️ 架構 / Architecture

```
MrLiou_AI_SuperComputer/
├── flowcore_loop.py         # 核心 Runtime + Judge Loop
├── ai_providers.py          # AI 提供商抽象層 / AI provider abstraction
├── modules_loader.py        # 模組載入器（Manifest-aware）
├── run.sh                   # 啟動腳本
├── config/                  # 設定檔 / Configuration
│   ├── ai_providers.json   # AI 提供商設定
│   └── env_template.txt    # 環境變數範本
├── memory/                  # 資料層
│   ├── ingest/
│   │   ├── raw/            # 原始輸入
│   │   └── ai_responses/   # AI 回應記錄
│   ├── snapshot/           # 自動快照
│   ├── domain/A|R/         # 領域資料
│   └── derived/l1/         # 衍生資料（L1 低解析度）
└── log/                     # 稽核日誌
    ├── trace.jsonl         # 事件流
    ├── trace_state.json    # Merkle 狀態
    └── ai_costs.jsonl      # AI 成本追蹤
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
✅ **多提供商** - 統一介面，自動容錯  
✅ **成本追蹤** - 自動記錄 token 使用與費用

## 🐛 疑難排解 / Troubleshooting

### AI 提供商無法使用 / AI Provider Not Available

**問題 / Problem:** `Provider not available` 錯誤

**解決方案 / Solutions:**

1. **檢查環境變數 / Check environment variables:**
   ```bash
   echo $OPENAI_API_KEY
   ```

2. **確認 API 金鑰正確 / Verify API key is correct:**
   - OpenAI: 應以 `sk-` 開頭 / Should start with `sk-`
   - Claude: 應以 `sk-ant-` 開頭 / Should start with `sk-ant-`

3. **檢查網路連線 / Check network connectivity:**
   ```bash
   curl https://api.openai.com/v1/models \
     -H "Authorization: Bearer $OPENAI_API_KEY"
   ```

4. **檢查 Ollama 是否執行 / Check if Ollama is running:**
   ```bash
   curl http://localhost:11434/api/tags
   ```

### 容錯機制 / Fallback Mechanism

當主要提供商失敗時，系統會自動嘗試容錯順序中的其他提供商：
When primary provider fails, system automatically tries other providers in fallback order:

```json
{
  "fallback_enabled": true,
  "fallback_order": ["openai", "claude", "ollama"]
}
```

檢查回應中的 `fallback_used` 欄位以了解是否使用了容錯：
Check `fallback_used` field in response to see if fallback was used:

```json
{
  "ok": true,
  "provider": "claude",
  "fallback_used": true,
  "attempts": 2
}
```

### 成本追蹤 / Cost Tracking

查看 AI 使用成本：/ View AI usage costs:

```bash
tail -f log/ai_costs.jsonl
```

範例記錄 / Example entry:
```json
{
  "timestamp": "2026-XX-XXT12:00:00Z",
  "provider": "openai",
  "model": "gpt-4",
  "input_tokens": 50,
  "output_tokens": 200,
  "total_tokens": 250,
  "estimated_cost_usd": 0.015
}
```

---

**這不是框架，這是一台 AI 用的電腦。**  
**This is not a framework, this is a computer for AI.**
