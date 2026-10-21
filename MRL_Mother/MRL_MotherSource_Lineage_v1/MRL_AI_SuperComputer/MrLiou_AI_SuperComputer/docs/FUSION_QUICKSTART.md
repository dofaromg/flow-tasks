# AI Fusion Stack - Quick Start Guide

**快速上手指南 - 5 分鐘開始使用 AI 融合系統**

## Prerequisites (前置需求)

- Python 3.10+ (標準庫，無需額外安裝)
- 已啟動 MrLiou AI SuperComputer 服務器

## Step 1: Start the Server (啟動服務器)

```bash
cd MrLiou_AI_SuperComputer
python3 flowcore_loop.py
```

You should see:
```
AI SuperComputer running on http://127.0.0.1:8787
Fusion System: enabled
```

## Step 2: Verify Server is Running (驗證服務器運行)

```bash
curl http://127.0.0.1:8787/judge/health
```

Expected output:
```json
{
  "ok": true,
  "anchor": "abc123..."
}
```

## Step 3: List Available Fusion Manifests (查看可用融合清單)

```bash
curl http://127.0.0.1:8787/ai/fusion/manifests
```

You'll see 3 pre-configured fusion manifests:
- `sequential_refine` - Sequential pipeline
- `parallel_consensus` - Parallel processing
- `mobius_evolve` - Möbius loop

## Step 4: Try Sequential Fusion (嘗試順序融合)

```bash
curl -X POST http://127.0.0.1:8787/ai/fusion/execute \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Explain quantum computing",
    "manifest": "sequential_refine"
  }'
```

This will:
1. OpenAI generates initial draft
2. Claude refines it
3. Gemini polishes the final version

## Step 5: Try Möbius Loop (嘗試莫比烏斯循環)

```bash
curl -X POST http://127.0.0.1:8787/ai/fusion/mobius \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Design a sustainable city",
    "max_cycles": 5,
    "convergence_threshold": 0.9
  }'
```

The output will cycle through multiple AIs until it converges or hits max_cycles.

## Step 6: Create Custom Fusion (創建自訂融合)

```bash
curl -X POST http://127.0.0.1:8787/ai/fusion/custom \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Write a poem",
    "mode": "weighted",
    "particles": [
      {"provider": "claude", "weight": 0.7},
      {"provider": "gemini", "weight": 0.3}
    ]
  }'
```

## Step 7: Run Complete Examples (運行完整示例)

We've provided a comprehensive example script:

```bash
python3 fusion_examples.py
```

This will demonstrate all 4 fusion modes.

## Step 8: Explore the Results (探索結果)

### Memory Structure
All fusion outputs are saved to:
```
memory/
├── ingest/
│   ├── fusion/
│   │   ├── {fusion_id}/
│   │   │   ├── output_0_openai.txt
│   │   │   ├── output_1_claude.txt
│   │   │   ├── output_2_gemini.txt
│   │   │   ├── merged_result.txt
│   │   │   └── fusion_result.json
│   └── mobius/
│       └── {loop_id}/
│           ├── cycle_0/
│           ├── cycle_1/
│           └── convergence_report.json
```

### Merkle Chain Audit Trail
All events are logged to:
```
log/trace.jsonl
```

View fusion events:
```bash
grep "fusion" log/trace.jsonl | tail -5
```

## Understanding Fusion Modes (理解融合模式)

### 1. Sequential (順序融合)
```
Prompt → AI₁ → AI₂ → AI₃ → Final Result
```
**Best for:** High-quality content, multi-pass refinement

### 2. Parallel (並行融合)
```
         ┌→ AI₁ ┐
Prompt → ┼→ AI₂ ┼→ Merge → Result
         └→ AI₃ ┘
```
**Best for:** Multiple perspectives, consensus building

### 3. Weighted (加權融合)
```
Result = w₁×AI₁ + w₂×AI₂ + w₃×AI₃
```
**Best for:** Balancing expert opinions

### 4. Möbius Loop (莫比烏斯循環)
```
AI₁ → AI₂ → AI₃
 ↑             ↓
 └─────────────┘
```
**Best for:** Iterative refinement, creative evolution

## Python API Usage (Python API 使用)

```python
from ai_fusion_core import (
    AIParticle, FusionStack, MobiusLoop,
    BaseAIProvider, create_stack_from_manifest,
    load_fusion_manifest
)

# Method 1: Use manifest
manifest = load_fusion_manifest("fusion_manifests/sequential_refine.manifest.json")
stack = create_stack_from_manifest(manifest)
result = stack.execute("Your prompt here")

# Method 2: Manual configuration
stack = FusionStack()
stack.add_particle(AIParticle(BaseAIProvider("openai", "gpt-4")))
stack.add_particle(AIParticle(BaseAIProvider("claude", "claude-3")))
stack.set_mode("sequential")
result = stack.execute("Your prompt")

# Method 3: Möbius loop
mobius = MobiusLoop(stack)
result = mobius.run("Your prompt", max_cycles=5)
```

## Creating Custom Manifests (創建自訂清單)

Create a new file in `fusion_manifests/`:

```json
{
  "manifest_version": "1.0",
  "fusion_name": "my_custom_fusion",
  "fusion_mode": "sequential",
  "description": "My custom fusion pipeline",
  "particles": [
    {
      "provider": "openai",
      "model": "gpt-4",
      "role": "analyzer",
      "weight": 1.0
    },
    {
      "provider": "claude",
      "model": "claude-3-opus",
      "role": "synthesizer",
      "weight": 1.0
    }
  ]
}
```

## Troubleshooting (故障排除)

### Server not responding
```bash
# Check if server is running
ps aux | grep flowcore_loop

# Check logs
tail -f log/trace.jsonl
```

### Import errors
Make sure you're in the MrLiou_AI_SuperComputer directory:
```bash
cd MrLiou_AI_SuperComputer
python3 flowcore_loop.py
```

## Next Steps (下一步)

1. Read the full guide: [`docs/AI_FUSION_GUIDE.md`](AI_FUSION_GUIDE.md)
2. Explore fusion strategies: `fusion_strategies.py`
3. Customize manifests for your use cases
4. Integrate real AI APIs (replace `BaseAIProvider`)

## Zero Dependencies (零外部依賴)

The current implementation uses **simulated AI responses** - no API keys needed!

To connect real AIs:
1. Subclass `BaseAIProvider`
2. Implement `generate()` method with actual API calls
3. Update manifests to use your providers

---

**Happy Fusing! 融合愉快！** 🌀
