# MRLiou Structural Earth Runtime v1.1 使用指南

## 目錄
1. [快速開始](#快速開始)
2. [核心概念](#核心概念)
3. [命令參考](#命令參考)
4. [使用案例](#使用案例)
5. [數據格式](#數據格式)
6. [進階用法](#進階用法)

---

## 快速開始

### 安裝

```bash
cd mlriou_structural_earth_runtime_v1_1
python -m pip install -e .
```

安裝完成後，你可以使用 `mlriou-earth` 命令。

### 第一次運行

```bash
# 使用範例數據運行
mlriou-earth run \
  --input examples/sample_nodes.json \
  --outdir my_first_run \
  --max-ticks 20

# 查看結果
ls my_first_run/
# 輸出: trace.jsonl  final_structure.json  jump_statistics.json  trace_statistics.json
```

### 回放軌跡

```bash
# 回放到 tick 10
mlriou-earth replay \
  --trace my_first_run/trace.jsonl \
  --tick 10 \
  --verbose
```

---

## 核心概念

### 1. 結構定義（Structure）

系統使用三層結構表示節點的空間位置：

```
中心 (Ring 0)
  └─ Ring 1
      ├─ Sector 0
      │   └─ Cell 0, 1, 2...
      ├─ Sector 1
      └─ Sector 2
  └─ Ring 2
      └─ ...
```

**中心不變性**：中心節點（ring=0, sector=0, cell=0）永遠固定，是整個系統的參考點。

### 2. 壓力場映射（Pressure Projection）

每個節點都有四個參數控制其壓力演化：

- **N** (節點強度): 節點的基礎能量
- **eta** (阻尼係數): 控制能量耗散，越大則壓力衰減越快
- **alpha** (放大係數): 控制壓力增益，配合全局 alpha 使用
- **beta** (偏移係數): 基準壓力調整

**壓力更新公式**：
```
P_next = (N / eta) * alpha_global * alpha_local * P_current + beta
P_next = P_next * exp(-eta * dt)  # 能量最小化阻尼
```

### 3. 跳層衍生（Jump Mechanism）

當節點壓力超過閾值時，系統會自動創建「跳層節點」：

```python
if pressure >= threshold:
    jump_distance = (pressure - threshold) / threshold
    target_ring = current_ring + jump_distance
    create_jump_node(target_ring)
```

跳層節點特性：
- 強度降低（N * 0.5）
- 阻尼增加（eta * 1.5）
- 保持源節點的扇區和單元位置

### 4. 軌跡記錄（Trace）

所有事件都記錄在 `trace.jsonl` 中，每行一個事件：

```json
{"tick": 0, "event_type": "projection", "node_id": "n1", "data": {...}}
{"tick": 5, "event_type": "jump", "node_id": "n1", "data": {...}}
```

這使得系統狀態完全可回溯。

---

## 命令參考

### mlriou-earth run

執行運轉模擬。

```bash
mlriou-earth run \
  --input <input_file> \
  --outdir <output_directory> \
  [選項...]
```

**必需參數：**
- `--input`: 輸入節點數據文件（JSON 格式）
- `--outdir`: 輸出目錄

**可選參數：**
- `--alpha <float>`: 全局放大係數（默認: 2.0）
- `--threshold <float>`: 跳層壓力閾值（默認: 20.0）
- `--ring-lift <int>`: 環層提升（正值向外，負值向內，默認: 0）
- `--sector-shift <int>`: 扇區旋轉（正值順時針，負值逆時針，默認: 0）
- `--max-ticks <int>`: 最大時間步（默認: 100）

**輸出文件：**
- `trace.jsonl`: 完整軌跡記錄
- `final_structure.json`: 最終結構狀態
- `jump_statistics.json`: 跳層統計
- `trace_statistics.json`: 軌跡統計

### mlriou-earth replay

回放軌跡到指定時間點。

```bash
mlriou-earth replay \
  --trace <trace_file> \
  --tick <tick_number> \
  [選項...]
```

**必需參數：**
- `--trace`: 軌跡文件路徑（trace.jsonl）
- `--tick`: 回放到的時間步

**可選參數：**
- `--output <file>`: 導出快照到 JSON 文件
- `--verbose`: 顯示詳細節點狀態

---

## 使用案例

### 案例 1: 基礎運轉

最簡單的使用方式，使用默認參數：

```bash
mlriou-earth run \
  --input examples/sample_nodes.json \
  --outdir run_basic \
  --max-ticks 50
```

### 案例 2: 高壓力環境測試

降低跳層閾值，增加放大係數，觀察快速跳層：

```bash
mlriou-earth run \
  --input examples/sample_nodes.json \
  --outdir run_high_pressure \
  --alpha 3.0 \
  --threshold 10.0 \
  --max-ticks 50
```

這會產生更多的跳層節點。

### 案例 3: 結構變換

測試環層提升和扇區旋轉：

```bash
# 向外擴展 2 層
mlriou-earth run \
  --input examples/sample_nodes.json \
  --outdir run_lift \
  --ring-lift 2 \
  --max-ticks 30

# 旋轉 1 個扇區
mlriou-earth run \
  --input examples/sample_nodes.json \
  --outdir run_shift \
  --sector-shift 1 \
  --max-ticks 30
```

### 案例 4: 時間序列分析

運行後，使用回放觀察不同時間點的狀態：

```bash
# 運行
mlriou-earth run \
  --input examples/sample_nodes.json \
  --outdir run_timeseries \
  --max-ticks 100

# 觀察不同時間點
mlriou-earth replay --trace run_timeseries/trace.jsonl --tick 10 --verbose
mlriou-earth replay --trace run_timeseries/trace.jsonl --tick 25 --verbose
mlriou-earth replay --trace run_timeseries/trace.jsonl --tick 50 --verbose
mlriou-earth replay --trace run_timeseries/trace.jsonl --tick 75 --verbose

# 導出關鍵時刻快照
mlriou-earth replay --trace run_timeseries/trace.jsonl --tick 50 --output snapshot_t50.json
```

### 案例 5: 對比實驗

使用不同參數進行對比：

```bash
# 實驗 A: 低 alpha
mlriou-earth run --input examples/sample_nodes.json --outdir exp_a --alpha 1.5 --max-ticks 50

# 實驗 B: 中 alpha（默認）
mlriou-earth run --input examples/sample_nodes.json --outdir exp_b --alpha 2.0 --max-ticks 50

# 實驗 C: 高 alpha
mlriou-earth run --input examples/sample_nodes.json --outdir exp_c --alpha 3.0 --max-ticks 50

# 比較統計
cat exp_a/jump_statistics.json
cat exp_b/jump_statistics.json
cat exp_c/jump_statistics.json
```

---

## 數據格式

### 輸入節點數據（JSON）

```json
{
  "nodes": [
    {
      "node_id": "center",      // 節點ID（必需，唯一）
      "ring": 0,                // 環層（必需，>= 0）
      "sector": 0,              // 扇區（必需，>= 0）
      "cell": 0,                // 單元（必需，>= 0）
      "N": 1.0,                 // 節點強度（默認 1.0）
      "eta": 1.0,               // 阻尼係數（默認 1.0）
      "alpha": 1.0,             // 局部放大係數（默認 1.0）
      "beta": 0.0,              // 偏移係數（默認 0.0）
      "data": {                 // 附加數據（可選）
        "description": "中心節點",
        "custom_field": "..."
      }
    },
    {
      "node_id": "n1",
      "ring": 1,
      "sector": 0,
      "cell": 0,
      "N": 2.0,
      "eta": 0.8,
      "alpha": 1.2,
      "beta": 0.5,
      "data": {}
    }
  ],
  "edges": [
    ["center", "n1"],          // [源節點ID, 目標節點ID]
    ["n1", "n2"]
  ]
}
```

### 軌跡記錄格式（JSONL）

每行一個 JSON 對象，記錄一個事件：

**投影事件：**
```json
{
  "tick": 0,
  "event_type": "projection",
  "node_id": "n1",
  "data": {
    "pressure_before": 1.0,
    "pressure_after": 2.92,
    "pressure_delta": 1.92,
    "energy": 8.53,
    "metadata": {...}
  }
}
```

**跳層事件：**
```json
{
  "tick": 5,
  "event_type": "jump",
  "node_id": "n1",
  "data": {
    "jump": true,
    "jump_node_id": "jump_n1_1",
    "pressure": 22.06,
    "target_ring": 3,
    "metadata": {...}
  }
}
```

### 快照格式（JSON）

```json
{
  "tick": 10,
  "node_states": {
    "n1": {
      "tick": 10,
      "pressure": 434.69,
      "energy": 188962.75,
      "pressure_delta": 273.54,
      "metadata": {...}
    }
  },
  "jump_nodes": [
    {
      "tick": 5,
      "source_node_id": "n1",
      "jump_node_id": "jump_n1_1",
      "pressure": 22.06,
      "target_ring": 3,
      "metadata": {...}
    }
  ],
  "statistics": {
    "tick": 10,
    "total_nodes": 32,
    "total_jumps": 30,
    "total_energy": 27362000838032.70,
    "avg_pressure": 165416.89,
    "max_pressure": 5230503.33
  }
}
```

---

## 進階用法

### 自定義節點數據

創建你自己的節點配置：

```python
import json

data = {
    "nodes": [
        {
            "node_id": "center",
            "ring": 0, "sector": 0, "cell": 0,
            "N": 1.0, "eta": 1.0, "alpha": 1.0, "beta": 0.0,
            "data": {"is_center": True}
        },
        # 添加更多節點...
    ],
    "edges": [
        ["center", "node1"],
        # 添加更多邊...
    ]
}

with open("my_nodes.json", "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)
```

### 批量處理

使用 shell 腳本批量運行多個實驗：

```bash
#!/bin/bash
# run_batch.sh

for alpha in 1.5 2.0 2.5 3.0; do
  for threshold in 10 15 20 25; do
    outdir="batch_a${alpha}_t${threshold}"
    echo "Running alpha=$alpha, threshold=$threshold"
    mlriou-earth run \
      --input examples/sample_nodes.json \
      --outdir $outdir \
      --alpha $alpha \
      --threshold $threshold \
      --max-ticks 50
  done
done
```

### Python API 使用

直接在 Python 代碼中使用：

```python
from mlriou_earth.core.structure import EarthStructure, StructureNode
from mlriou_earth.core.projection import PressureProjection
from mlriou_earth.core.jump import JumpManager
from mlriou_earth.core.trace import TraceRecorder

# 創建結構
structure = EarthStructure()
node = StructureNode(
    node_id="n1",
    ring=1, sector=0, cell=0,
    N=2.0, eta=0.8, alpha=1.2, beta=0.5
)
structure.add_node(node)

# 創建壓力投影器
projection = PressureProjection(alpha_global=2.0)
jump_manager = JumpManager(pressure_threshold=20.0)
trace_recorder = TraceRecorder("my_trace.jsonl")

# 運行模擬
for tick in range(100):
    projection.advance_tick()
    
    for node in structure.nodes.values():
        prev_pressure = projection.get_pressure(node.node_id) or 1.0
        state = projection.project(
            node.node_id, node.N, node.eta, node.alpha, node.beta, prev_pressure
        )
        
        trace_recorder.record_projection(
            tick, node.node_id, prev_pressure, state.pressure, state.energy
        )
        
        jump_node = jump_manager.check_and_create_jump(node, state.pressure, tick)
        if jump_node:
            trace_recorder.record_jump(
                tick, node.node_id, jump_node.jump_id,
                state.pressure, jump_node.target_ring
            )

trace_recorder.close_file()
```

### 分析和可視化

使用 Python 分析結果：

```python
import json
import matplotlib.pyplot as plt

# 讀取軌跡
pressures = {}
with open("out/trace.jsonl", "r") as f:
    for line in f:
        record = json.loads(line)
        if record["event_type"] == "projection":
            node_id = record["node_id"]
            tick = record["tick"]
            pressure = record["data"]["pressure_after"]
            
            if node_id not in pressures:
                pressures[node_id] = {"ticks": [], "values": []}
            pressures[node_id]["ticks"].append(tick)
            pressures[node_id]["values"].append(pressure)

# 繪製壓力演化
plt.figure(figsize=(12, 6))
for node_id, data in list(pressures.items())[:5]:  # 前5個節點
    plt.plot(data["ticks"], data["values"], label=node_id)
plt.xlabel("Tick")
plt.ylabel("Pressure")
plt.legend()
plt.title("Pressure Evolution")
plt.savefig("pressure_evolution.png")
```

---

## 常見問題

### Q: 如何控制跳層數量？

A: 調整 `--threshold` 參數。閾值越高，跳層越少；閾值越低，跳層越多。

### Q: 運轉能量爆炸怎麼辦？

A: 增加節點的 `eta` 值（阻尼係數），或減小 `alpha` 值（放大係數）。

### Q: 回放可以跨不同運行嗎？

A: 不行。回放只能使用對應運行產生的 `trace.jsonl` 文件。

### Q: 如何理解「中心不變」？

A: 中心節點（ring=0）是整個系統的參考點，所有結構變換（ring lift, sector shift）都不會影響中心節點的位置。

---

## 下一步

- 查看 `README.md` 了解更多技術細節
- 運行 `test_mlriou_earth.py` 驗證安裝
- 閱讀源碼了解實現細節
- 等待 v1.2 的視覺化功能！

**MR.Liou - 粒子語言核心系統**
