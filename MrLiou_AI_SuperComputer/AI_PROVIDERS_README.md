# AI Provider Abstraction Layer

**Multi-Provider AI Support for MrLiou AI SuperComputer**  
**MrLiou AI 超級電腦的多提供商 AI 支援**

## Overview / 概述

This module provides a unified interface for multiple AI service providers, enabling the MrLiou AI SuperComputer to work with various AI models through a consistent API.

本模組為多個 AI 服務提供商提供統一介面，使 MrLiou AI 超級電腦能夠透過一致的 API 使用各種 AI 模型。

## Features / 功能

✅ **Multiple Providers** - Support for OpenAI, Claude, Gemini, Ollama, and Azure OpenAI  
✅ **Automatic Fallback** - Switch to alternative providers on failure  
✅ **Cost Tracking** - Monitor token usage and estimated costs  
✅ **Audit Trail** - All AI interactions logged to Merkle chain  
✅ **Zero Dependencies** - Pure Python stdlib (urllib, json)  
✅ **Streaming Support** - Server-Sent Events (SSE) for real-time responses  

## Supported Providers / 支援的提供商

### 1. OpenAI
- **Models**: GPT-4, GPT-3.5-turbo, etc.
- **API**: OpenAI Chat Completions API
- **Configuration**:
  ```json
  {
    "enabled": true,
    "api_key": "${OPENAI_API_KEY}",
    "model": "gpt-4",
    "base_url": "https://api.openai.com/v1"
  }
  ```

### 2. Anthropic Claude
- **Models**: Claude 3 Opus, Sonnet, Haiku
- **API**: Anthropic Messages API
- **Configuration**:
  ```json
  {
    "enabled": true,
    "api_key": "${ANTHROPIC_API_KEY}",
    "model": "claude-3-opus-20240229",
    "base_url": "https://api.anthropic.com/v1"
  }
  ```

### 3. Google Gemini
- **Models**: Gemini Pro, Gemini Ultra (when available)
- **API**: Gemini REST API
- **Configuration**:
  ```json
  {
    "enabled": true,
    "api_key": "${GOOGLE_API_KEY}",
    "model": "gemini-pro",
    "base_url": "https://generativelanguage.googleapis.com/v1beta"
  }
  ```

### 4. Ollama (Local)
- **Models**: Llama 2, Mistral, Code Llama, etc.
- **API**: Ollama Local API
- **Configuration**:
  ```json
  {
    "enabled": true,
    "base_url": "http://localhost:11434",
    "model": "llama2"
  }
  ```

### 5. Azure OpenAI
- **Models**: GPT-4, GPT-3.5-turbo (via Azure)
- **API**: Azure OpenAI Service API
- **Configuration**:
  ```json
  {
    "enabled": false,
    "api_key": "${AZURE_OPENAI_KEY}",
    "endpoint": "${AZURE_OPENAI_ENDPOINT}",
    "deployment_name": "gpt-4",
    "api_version": "2024-02-15-preview"
  }
  ```

## Quick Start / 快速開始

### 1. Setup Environment Variables / 設定環境變數

```bash
# Copy template
cp config/env_template.txt .env

# Edit .env and add your API keys
# 編輯 .env 並新增您的 API 金鑰
nano .env

# Load environment variables
# 載入環境變數
export $(cat .env | xargs)
```

### 2. Start the Server / 啟動伺服器

```bash
cd MrLiou_AI_SuperComputer
./run.sh
```

### 3. Test the API / 測試 API

```bash
# List available providers
curl http://127.0.0.1:8787/ai/providers

# Complete with default provider
curl -X POST http://127.0.0.1:8787/ai/complete \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Hello, AI!"}'
```

## Architecture / 架構

### Class Hierarchy / 類別階層

```
BaseAIProvider (Abstract Base Class)
├── OpenAIProvider
├── ClaudeProvider
├── GeminiProvider
├── OllamaProvider
└── AzureOpenAIProvider

AIProviderManager
├── _load_config()
├── get_provider()
├── list_providers()
└── complete_with_fallback()
```

### Data Flow / 資料流

```
HTTP Request → flowcore_loop.py
              ↓
         judge_ai_complete()
              ↓
         AIProviderManager
              ↓
         Provider (with fallback)
              ↓
         External AI API
              ↓
         Response + Cost Tracking
              ↓
         Merkle Chain + Storage
```

## API Reference / API 參考

### GET /ai/providers

List all available AI providers.

**Response:**
```json
{
  "ok": true,
  "providers": [
    {
      "provider": "OpenAIProvider",
      "model": "gpt-4",
      "available": true
    }
  ]
}
```

### POST /ai/complete

Synchronous AI completion.

**Request:**
```json
{
  "prompt": "Your prompt here",
  "provider": "openai",  // optional
  "options": {
    "temperature": 0.7,
    "max_tokens": 2000
  }
}
```

**Response:**
```json
{
  "ok": true,
  "request_id": "abc123...",
  "content": "AI response...",
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
  "response_path": "memory/ingest/ai_responses/...",
  "merkle_root": "..."
}
```

### POST /ai/stream

Streaming AI completion (Server-Sent Events).

**Request:**
```json
{
  "prompt": "Your prompt here",
  "provider": "ollama"
}
```

**Response (SSE):**
```
data: {"chunk": "Hello"}

data: {"chunk": " world"}

data: [DONE]
```

## Cost Tracking / 成本追蹤

All AI requests are logged with token usage and estimated costs:

```bash
# View cost logs
tail -f log/ai_costs.jsonl
```

**Log Format:**
```json
{
  "timestamp": "2026-02-01T12:00:00Z",
  "provider": "openai",
  "model": "gpt-4",
  "input_tokens": 50,
  "output_tokens": 200,
  "total_tokens": 250,
  "estimated_cost_usd": 0.015
}
```

## Fallback Mechanism / 容錯機制

When a provider fails, the system automatically tries alternatives:

當提供商失敗時，系統會自動嘗試替代方案：

```json
{
  "fallback_enabled": true,
  "fallback_order": ["openai", "claude", "ollama"]
}
```

**Example Response:**
```json
{
  "ok": true,
  "provider": "claude",
  "fallback_used": true,
  "attempts": 2
}
```

## Security Best Practices / 安全最佳實踐

1. **Never commit API keys** - Use environment variables
2. **Rotate keys regularly** - Follow provider recommendations
3. **Monitor usage** - Check `ai_costs.jsonl` for anomalies
4. **Set rate limits** - Configure `max_tokens` appropriately
5. **Use HTTPS** - All providers use secure connections

## Testing / 測試

### Run Integration Tests
```bash
python3 test_ai_supercomputer.py
```

### Run Demo Script
```bash
python3 MrLiou_AI_SuperComputer/demo_ai_providers.py
```

## Troubleshooting / 疑難排解

### Provider Not Available

**Symptoms:**
- `Provider not available` error
- Provider shows as `unavailable` in `/ai/providers`

**Solutions:**

1. **Check environment variables:**
   ```bash
   echo $OPENAI_API_KEY
   ```

2. **Verify API key format:**
   - OpenAI: `sk-...`
   - Claude: `sk-ant-...`
   - Gemini: Standard API key format

3. **Test API connectivity:**
   ```bash
   curl https://api.openai.com/v1/models \
     -H "Authorization: Bearer $OPENAI_API_KEY"
   ```

### Ollama Connection Failed

**Symptoms:**
- Ollama provider unavailable
- Connection refused errors

**Solutions:**

1. **Check if Ollama is running:**
   ```bash
   curl http://localhost:11434/api/tags
   ```

2. **Start Ollama:**
   ```bash
   ollama serve
   ```

3. **Pull a model:**
   ```bash
   ollama pull llama2
   ```

### High Costs

**Monitor usage:**
```bash
# View total costs
jq -s 'map(.estimated_cost_usd) | add' log/ai_costs.jsonl

# View costs by provider
jq -s 'group_by(.provider) | map({provider: .[0].provider, total: (map(.estimated_cost_usd) | add)})' log/ai_costs.jsonl
```

**Reduce costs:**
- Use smaller models (gpt-3.5-turbo instead of gpt-4)
- Set lower `max_tokens` limits
- Use local models with Ollama
- Enable caching for repeated queries

## Extending / 擴充

### Adding a New Provider

1. **Create provider class:**
   ```python
   class MyAIProvider(BaseAIProvider):
       def complete(self, prompt: str, **kwargs) -> Dict[str, Any]:
           # Implementation
           pass
       
       def stream(self, prompt: str, **kwargs) -> Iterator[str]:
           # Implementation
           pass
       
       def is_available(self) -> bool:
           # Check availability
           pass
   ```

2. **Register in AIProviderManager:**
   ```python
   provider_classes = {
       "myai": MyAIProvider
   }
   ```

3. **Add configuration:**
   ```json
   {
     "providers": {
       "myai": {
         "enabled": true,
         "api_key": "${MY_AI_KEY}",
         "model": "my-model"
       }
     }
   }
   ```

## License / 授權

MIT License - See main repository LICENSE file

## Support / 支援

For issues and questions:
- Check the documentation in `docs/SUPERCOMPUTER_QUICKSTART.md`
- Review test files for usage examples
- Run the demo script to verify setup

有問題請：
- 查看 `docs/SUPERCOMPUTER_QUICKSTART.md` 文件
- 查看測試檔案以了解使用範例
- 執行演示腳本以驗證設定
