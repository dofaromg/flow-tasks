#!/bin/bash
# Example commands for testing each AI provider
# 測試各個 AI 提供商的範例命令

echo "=================================="
echo "AI Provider Testing Examples"
echo "AI 提供商測試範例"
echo "=================================="
echo ""

# Base URL
BASE_URL="http://127.0.0.1:8787"

echo "1. Health Check / 健康檢查"
echo "----------------------------------"
echo "curl $BASE_URL/judge/health"
echo ""

echo "2. List AI Providers / 列出 AI 提供商"
echo "----------------------------------"
echo "curl $BASE_URL/ai/providers"
echo ""

echo "3. OpenAI Completion / OpenAI 完成"
echo "----------------------------------"
cat << 'EOF'
curl -X POST $BASE_URL/ai/complete \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Explain quantum computing in one sentence",
    "provider": "openai",
    "options": {
      "temperature": 0.7,
      "max_tokens": 100
    }
  }'
EOF
echo ""
echo ""

echo "4. Claude Completion / Claude 完成"
echo "----------------------------------"
cat << 'EOF'
curl -X POST $BASE_URL/ai/complete \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Write a haiku about artificial intelligence",
    "provider": "claude",
    "options": {
      "temperature": 0.9,
      "max_tokens": 100
    }
  }'
EOF
echo ""
echo ""

echo "5. Gemini Completion / Gemini 完成"
echo "----------------------------------"
cat << 'EOF'
curl -X POST $BASE_URL/ai/complete \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "What is the capital of France?",
    "provider": "gemini"
  }'
EOF
echo ""
echo ""

echo "6. Ollama Completion (Local) / Ollama 完成（本地）"
echo "----------------------------------"
cat << 'EOF'
curl -X POST $BASE_URL/ai/complete \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Tell me a fun fact about computers",
    "provider": "ollama"
  }'
EOF
echo ""
echo ""

echo "7. Streaming Response / 串流回應"
echo "----------------------------------"
cat << 'EOF'
curl -X POST $BASE_URL/ai/stream \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Count from 1 to 5",
    "provider": "ollama"
  }'
EOF
echo ""
echo ""

echo "8. Default Provider (with Fallback) / 預設提供商（含容錯）"
echo "----------------------------------"
cat << 'EOF'
curl -X POST $BASE_URL/ai/complete \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Explain machine learning in simple terms"
  }'
EOF
echo ""
echo ""

echo "9. View Cost Logs / 查看成本記錄"
echo "----------------------------------"
echo "tail -f MrLiou_AI_SuperComputer/log/ai_costs.jsonl"
echo ""

echo "10. View Merkle Chain / 查看 Merkle 鏈"
echo "----------------------------------"
echo "tail -f MrLiou_AI_SuperComputer/log/trace.jsonl"
echo ""

echo "=================================="
echo "Setup Required / 需要的設定"
echo "=================================="
echo ""
echo "Before running these commands, ensure you have:"
echo "在執行這些命令之前，請確保您有："
echo ""
echo "1. Set environment variables:"
echo "   設定環境變數："
echo "   export OPENAI_API_KEY=sk-..."
echo "   export ANTHROPIC_API_KEY=sk-ant-..."
echo "   export GOOGLE_API_KEY=..."
echo ""
echo "2. Start the server:"
echo "   啟動伺服器："
echo "   cd MrLiou_AI_SuperComputer && ./run.sh"
echo ""
echo "3. (Optional) Start Ollama for local models:"
echo "   （可選）啟動 Ollama 以使用本地模型："
echo "   ollama serve"
echo "   ollama pull llama2"
echo ""
