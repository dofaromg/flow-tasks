# AI Fusion Stack System - Möbius Loop Architecture

## 概述 Overview

AI Fusion Stack 是基於粒子語言核心系統的多 AI 提供者組合框架。它允許將多個 AI（OpenAI、Claude、Gemini）像粒子一樣堆疊、疊加和循環執行。

The AI Fusion Stack is a multi-AI provider composition framework based on the particle language core system. It allows multiple AIs (OpenAI, Claude, Gemini) to be stacked, superposed, and recursively executed like particles.

## 核心概念 Core Concepts

### 1. AI Particle (AI 粒子)

每個 AI 提供者都是一個粒子，具有：
- **狀態 (State)**: 記錄執行歷史
- **權重 (Weight)**: 用於加權融合
- **角色 (Role)**: 在融合管線中的角色

Each AI provider is a particle with:
- **State**: Records execution history
- **Weight**: Used for weighted fusion
- **Role**: Position in fusion pipeline

### 2. Fusion Stack (融合堆疊)

粒子堆疊，支援四種融合模式：

Particle stack supporting 4 fusion modes:

#### Sequential Fusion (順序融合)
```
Prompt → AI₁ → AI₂ → AI₃ → Result
```
每個 AI 精煉前一個的輸出，類似管線處理。

Each AI refines the previous output, like a pipeline.

**Use cases**: 高品質內容生成、程式碼重構、多階段優化
- High-quality content generation
- Code refactoring
- Multi-stage optimization

#### Parallel Fusion (並行融合)
```
            ┌→ AI₁ ┐
Prompt → ───┼→ AI₂ ┼─→ Merge → Result
            └→ AI₃ ┘
```
所有 AI 同時處理，結果合併。

All AIs process simultaneously, results merged.

**Use cases**: 多視角分析、事實查核、決策支援
- Multi-perspective analysis
- Fact checking
- Decision support

#### Weighted Fusion (加權融合)
```
Result = w₁×AI₁ + w₂×AI₂ + w₃×AI₃
```
根據權重混合多個 AI 的回應。

Blend responses with weights.

**Use cases**: 專家意見綜合、平衡不同觀點
- Expert opinion synthesis
- Balancing different perspectives

#### Recursive Fusion - Möbius Loop (莫比烏斯循環)
```
   AI₁ → AI₂ → AI₃
    ↑             ↓
    └─────────────┘
```
輸出循環回饋作為輸入，直到收斂或達到最大循環次數。

Output cycles back as input until convergence or max cycles.

**Use cases**: 創意發想、概念演化、問題求解
- Creative brainstorming
- Concept evolution
- Problem solving

### 3. Möbius Loop (莫比烏斯循環)

靈感來自莫比烏斯帶（Möbius strip），一個單面、無始無終的連續循環。

Inspired by the Möbius strip - a single-sided, continuous loop with no beginning or end.

**收斂檢測 Convergence Detection:**
- 計算相鄰循環輸出的相似度
- 當相似度 ≥ 閾值時視為收斂
- Calculate similarity between adjacent cycle outputs
- Converged when similarity ≥ threshold

**應用場景 Applications:**
- 迭代優化想法 (Iterative idea refinement)
- 自我修正的推理 (Self-correcting reasoning)
- 創意內容演化 (Creative content evolution)

## 架構設計 Architecture

### Particle System Mapping (粒子系統映射)

基於 MRLiou Particle Core 的邏輯鏈模式：

Based on MRLiou Particle Core logic chain pattern:

```
STRUCTURE → MARK → FLOW → RECURSE → STORE
    ↓         ↓      ↓        ↓        ↓
  Define    Track   Execute   Loop    Save
  Particles Roles   Fusion    Cycles  Results
```

1. **STRUCTURE**: 定義 AI 粒子配置 (Define AI particle configuration)
2. **MARK**: 標記每個粒子的角色 (Mark each particle's role)
3. **FLOW**: 執行融合流程 (Execute fusion flow)
4. **RECURSE**: 莫比烏斯循環 (Möbius loop)
5. **STORE**: 保存到記憶體結構 (Store to memory structure)

### Memory Structure (記憶體結構)

```
memory/
├── ingest/
│   ├── fusion/
│   │   └── {fusion_id}/
│   │       ├── output_0_openai.txt
│   │       ├── output_1_claude.txt
│   │       ├── output_2_gemini.txt
│   │       ├── merged_result.txt
│   │       └── fusion_result.json
│   └── mobius/
│       └── {loop_id}/
│           ├── cycle_0/
│           │   ├── input.txt
│           │   ├── output.txt
│           │   └── cycle_data.json
│           ├── cycle_1/
│           └── convergence_report.json
└── snapshot/
    └── {timestamp}_{original_file}
```

### Merkle Chain Tracing (默克爾鏈追蹤)

所有融合事件都記錄在 Merkle 鏈中：

All fusion events recorded in Merkle chain:

```
Event: fusion_pre
  ├─ fusion_id
  ├─ manifest
  ├─ mode
  └─ prompt

Event: fusion_post
  ├─ fusion_id
  ├─ outputs_saved
  └─ result_path

Event: mobius_pre/mobius_post
  ├─ loop_id
  ├─ converged
  └─ cycles
```

## API Reference

### GET Endpoints

#### `/judge/health`
健康檢查與 Merkle 錨點 (Health check and Merkle anchor)

```bash
curl http://127.0.0.1:8787/judge/health
```

Response:
```json
{
  "ok": true,
  "anchor": "abc123..."
}
```

#### `/ai/fusion/manifests`
列出所有融合清單 (List all fusion manifests)

```bash
curl http://127.0.0.1:8787/ai/fusion/manifests
```

Response:
```json
{
  "ok": true,
  "manifests": [
    {
      "filename": "sequential_refine.manifest.json",
      "name": "sequential_refine",
      "mode": "sequential",
      "description": "Each AI refines the previous output"
    }
  ]
}
```

### POST Endpoints

#### `/ai/fusion/execute`
執行融合堆疊 (Execute fusion stack)

```bash
curl -X POST http://127.0.0.1:8787/ai/fusion/execute \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Explain quantum entanglement",
    "manifest": "sequential_refine"
  }'
```

Parameters:
- `prompt` (required): 輸入提示 (Input prompt)
- `manifest` (required): 清單名稱 (Manifest name)

#### `/ai/fusion/mobius`
執行莫比烏斯循環 (Execute Möbius loop)

```bash
curl -X POST http://127.0.0.1:8787/ai/fusion/mobius \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Design a sustainable city",
    "max_cycles": 5,
    "convergence_threshold": 0.9,
    "manifest": "mobius_evolve"
  }'
```

Parameters:
- `prompt` (required): 初始提示 (Initial prompt)
- `max_cycles` (optional, default: 5): 最大循環次數 (Max cycles)
- `convergence_threshold` (optional, default: 0.9): 收斂閾值 (Convergence threshold)
- `manifest` (optional, default: "mobius_evolve"): 清單名稱 (Manifest name)

#### `/ai/fusion/custom`
自訂融合配置 (Custom fusion on-the-fly)

```bash
curl -X POST http://127.0.0.1:8787/ai/fusion/custom \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Write a haiku",
    "mode": "weighted",
    "particles": [
      {"provider": "claude", "weight": 0.6, "role": "poet"},
      {"provider": "gemini", "weight": 0.4, "role": "critic"}
    ]
  }'
```

Parameters:
- `prompt` (required): 輸入提示 (Input prompt)
- `mode` (required): 融合模式 (Fusion mode: sequential/parallel/weighted)
- `particles` (required): 粒子配置陣列 (Array of particle configs)

## Fusion Manifests (融合清單)

### Structure (結構)

```json
{
  "manifest_version": "1.0",
  "fusion_name": "example_fusion",
  "fusion_mode": "sequential|parallel|recursive|weighted",
  "description": "English description",
  "description_zh": "中文描述",
  "particles": [
    {
      "provider": "openai|claude|gemini",
      "model": "gpt-4|claude-3-opus|gemini-pro",
      "role": "role_name",
      "weight": 1.0
    }
  ],
  "metadata": {
    "use_case": "What it's good for",
    "best_for": "Specific scenarios"
  }
}
```

### Available Manifests (可用清單)

1. **sequential_refine.manifest.json**
   - Mode: Sequential
   - Use: High-quality multi-pass refinement
   - Particles: OpenAI (draft) → Claude (refine) → Gemini (polish)

2. **parallel_consensus.manifest.json**
   - Mode: Parallel
   - Use: Diverse perspectives and consensus
   - Particles: OpenAI (40%) + Claude (40%) + Gemini (20%)

3. **mobius_evolve.manifest.json**
   - Mode: Recursive
   - Use: Iterative idea evolution
   - Particles: OpenAI (expander) → Claude (critic) → Gemini (synthesizer)

## Merge Strategies (合併策略)

Located in `fusion_strategies.py`:

1. **weighted_merge**: 加權合併 (Weighted merge)
2. **consensus_merge**: 共識合併 (Consensus merge)
3. **meta_ai_merge**: 元 AI 合併 (Meta-AI synthesis)
4. **diff_merge**: 差異合併 (Differential merge)
5. **simple_concatenate**: 簡單串聯 (Simple concatenation)
6. **extract_best**: 提取最佳 (Extract best by criterion)

## Zero Dependencies (零外部依賴)

本系統**不需要**外部 AI API 金鑰即可運行。

This system runs **without** external AI API keys.

- 使用模擬的 AI 回應進行演示
- 可替換 `BaseAIProvider` 來連接真實 API
- Uses simulated AI responses for demo
- Replace `BaseAIProvider` to connect real APIs

## Examples (範例)

### Python API Usage

```python
from ai_fusion_core import (
    AIParticle, FusionStack, MobiusLoop, 
    BaseAIProvider, create_stack_from_manifest
)

# Create particles
openai = AIParticle(BaseAIProvider("openai", "gpt-4"), role="draft")
claude = AIParticle(BaseAIProvider("claude", "claude-3"), role="refine")

# Sequential fusion
stack = FusionStack()
stack.add_particle(openai)
stack.add_particle(claude)
stack.set_mode("sequential")
result = stack.execute("Explain AI fusion")

# Möbius loop
mobius = MobiusLoop(stack)
result = mobius.run("Design a sustainable city", max_cycles=5)
```

### Load from Manifest

```python
from ai_fusion_core import load_fusion_manifest, create_stack_from_manifest

manifest = load_fusion_manifest("fusion_manifests/sequential_refine.manifest.json")
stack = create_stack_from_manifest(manifest)
result = stack.execute("Your prompt here")
```

## Design Philosophy (設計哲學)

**"All AI providers are particles in a quantum superposition, collapsing into fused intelligence through Möbius cycles."**

**"所有 AI 提供者都是量子疊加態中的粒子，通過莫比烏斯循環塌縮為融合智慧。"**

Key principles:
1. **可組合性 (Composability)**: 粒子可自由組合
2. **可回返性 (Reversibility)**: 完整的狀態追蹤
3. **循環性 (Cyclicality)**: 莫比烏斯循環架構
4. **可稽核性 (Auditability)**: Merkle 鏈記錄所有事件

## Integration with Particle Core (與粒子核心整合)

AI Fusion Stack 遵循粒子語言核心的設計模式：

AI Fusion Stack follows the particle language core design patterns:

- **邏輯鏈 (Logic Chain)**: STRUCTURE → MARK → FLOW → RECURSE → STORE
- **狀態管理 (State Management)**: 每個粒子維護自己的狀態
- **壓縮/解壓 (Compression)**: Manifests 類似 .flpkg 格式
- **記憶封存 (Memory Archive)**: 所有輸出保存到 memory/ 結構
- **Merkle 追蹤 (Merkle Tracing)**: 完整的事件稽核鏈

## Future Enhancements (未來增強)

1. 真實 AI API 整合 (Real AI API integration)
2. 動態權重調整 (Dynamic weight adjustment)
3. 自適應收斂閾值 (Adaptive convergence threshold)
4. 粒子演化策略 (Particle evolution strategies)
5. 分散式融合執行 (Distributed fusion execution)

## License

MIT License - 與 MrLiou AI SuperComputer 相同授權
