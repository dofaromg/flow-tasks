# MRLiou Structural Earth Runtime v1.1

**中心不變的骨架定義 | 反射神經夾層輸出 | 運轉能量最小化**

MRLiou Structural Earth Runtime 是一個基於壓力場映射和跳層衍生的運轉軌跡系統。

---

## ✨ 核心特性

### 1️⃣ **Pressure Field（壓力場映射）**
- 每個節點投影時，使用 `N/eta/alpha/beta` 更新壓力 `Pk→P_next`
- 壓力資訊寫入 `projection.pressure`
- 完整的軌跡記錄，形成可回溯的「運轉能量最小化」版本

### 2️⃣ **Jump Rule（跳層衍生）**
- 當 `pressure >= threshold` 時，自動生成 synthetic jump node
- 寫入 jump edge (`src→jump_node`)
- 軌跡中有 `jump=True` 標記

### 3️⃣ **Replay（可前進/可後退）**
- 支援 `mlriou-earth replay` 命令
- 讀取 `trace.jsonl`，輸出任意 tick 的狀態快照
- forward/backward 都使用同一份 trace 做截取

---

## 🚀 快速開始

### 安裝

```bash
cd mlriou_structural_earth_runtime_v1_1
python -m pip install -e .
```

### 基本使用

#### 1. 執行運轉

```bash
mlriou-earth run \
  --input examples/sample_nodes.json \
  --outdir out \
  --alpha 2.0 \
  --threshold 20 \
  --ring-lift 0 \
  --sector-shift 0 \
  --max-ticks 50
```

**參數說明：**
- `--input`: 輸入節點數據文件（JSON 格式）
- `--outdir`: 輸出目錄
- `--alpha`: 全局放大係數（默認 2.0）
- `--threshold`: 跳層壓力閾值（默認 20.0）
- `--ring-lift`: 環層提升（正值向外擴展，負值向內收縮）
- `--sector-shift`: 扇區旋轉（正值順時針，負值逆時針）
- `--max-ticks`: 最大時間步（默認 100）

#### 2. 回放軌跡

```bash
# 回放到 tick 10
mlriou-earth replay --trace out/trace.jsonl --tick 10

# 回放並導出快照
mlriou-earth replay \
  --trace out/trace.jsonl \
  --tick 25 \
  --output snapshot_tick25.json \
  --verbose
```

**參數說明：**
- `--trace`: 軌跡文件路徑（trace.jsonl）
- `--tick`: 回放到指定時間步
- `--output`: 導出快照到 JSON 文件（可選）
- `--verbose`: 顯示詳細節點狀態

---

## 📂 目錄結構

```
mlriou_structural_earth_runtime_v1_1/
├── mlriou_earth/
│   ├── __init__.py
│   ├── core/
│   │   ├── __init__.py
│   │   ├── structure.py       # 中心不變的骨架定義
│   │   ├── projection.py      # 壓力場映射 (N/eta/alpha/beta → Pk→P_next)
│   │   ├── jump.py            # 跳層衍生 (pressure >= threshold)
│   │   └── trace.py           # 運轉軌跡記錄
│   ├── replay/
│   │   ├── __init__.py
│   │   └── player.py          # 前進/後退回放
│   └── cli.py                 # mlriou-earth run / replay
├── examples/
│   └── sample_nodes.json      # 範例節點資料
├── setup.py                   # 安裝配置
├── README.md                  # 本文件
└── requirements.txt           # 依賴套件（v1.1 無外部依賴）
```

---

## 🧬 核心概念

### 結構定義（Structure）

系統使用三層結構：**Ring → Sector → Cell**

- **Ring（環層）**: 從中心（ring=0）向外擴展
- **Sector（扇區）**: 每個環層的分區
- **Cell（單元）**: 扇區內的細分

**中心不變性**: 中心節點（ring=0, sector=0, cell=0）保持固定，所有變換都基於這個不變中心。

### 壓力場映射（Projection）

每個節點的壓力更新公式：

```python
P_next = (N / eta) * alpha * P_current + beta + external_force
P_next = P_next * exp(-eta * dt)  # 能量最小化阻尼
```

其中：
- `N`: 節點強度
- `eta`: 阻尼係數（能量耗散）
- `alpha`: 放大係數（壓力增益）
- `beta`: 偏移係數（基準調整）
- `P_current`: 當前壓力

### 跳層衍生（Jump）

當節點壓力達到閾值時：

```python
if pressure >= threshold:
    jump_distance = int((pressure - threshold) / threshold)
    target_ring = source_ring + jump_distance
    create_synthetic_jump_node(target_ring)
```

跳層節點具有：
- 降低的強度（能量分散）
- 增加的阻尼（穩定性）
- 保持源節點的扇區和單元位置

### 軌跡記錄（Trace）

所有事件記錄為 JSONL 格式，每行一個事件：

```json
{"tick": 0, "event_type": "projection", "node_id": "n1", "data": {...}}
{"tick": 5, "event_type": "jump", "node_id": "n1", "data": {"jump": true, ...}}
```

---

## 📊 輸出文件

運轉完成後，在輸出目錄會生成：

1. **trace.jsonl**: 完整軌跡記錄（支持回放）
2. **final_structure.json**: 最終結構狀態（包含所有合成節點）
3. **jump_statistics.json**: 跳層統計信息
4. **trace_statistics.json**: 軌跡統計信息

---

## 🔧 節點數據格式

輸入節點數據（JSON）格式：

```json
{
  "nodes": [
    {
      "node_id": "center",
      "ring": 0,
      "sector": 0,
      "cell": 0,
      "N": 1.0,
      "eta": 1.0,
      "alpha": 1.0,
      "beta": 0.0,
      "data": {
        "is_center": true
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
    ["center", "n1"]
  ]
}
```

---

## 🎯 使用案例

### 案例 1: 基本運轉測試

```bash
mlriou-earth run \
  --input examples/sample_nodes.json \
  --outdir out_basic \
  --alpha 2.0 \
  --threshold 20.0 \
  --max-ticks 30
```

### 案例 2: 高壓力跳層測試

```bash
mlriou-earth run \
  --input examples/sample_nodes.json \
  --outdir out_highjump \
  --alpha 3.0 \
  --threshold 10.0 \
  --max-ticks 50
```

### 案例 3: 結構變換測試

```bash
mlriou-earth run \
  --input examples/sample_nodes.json \
  --outdir out_transform \
  --ring-lift 1 \
  --sector-shift 1 \
  --max-ticks 40
```

### 案例 4: 回放分析

```bash
# 前進回放
mlriou-earth replay --trace out_basic/trace.jsonl --tick 10 --verbose
mlriou-earth replay --trace out_basic/trace.jsonl --tick 20 --verbose

# 後退回放（指定較大的 tick）
mlriou-earth replay --trace out_basic/trace.jsonl --tick 15 --verbose
mlriou-earth replay --trace out_basic/trace.jsonl --tick 5 --verbose
```

---

## 🚀 下一階段（v1.2 預告）

v1.2 將加入：
- **reflect_view 的多層視圖輸出**（ring/sector/cell + jump 分層）
- **縮放視角輸出**（同一份資料以不同 alpha 生成不同呈現）
- **視覺化工具**（圖形化展示結構和壓力場）

---

## 📝 授權

MIT License

---

## 👤 作者

**MR.Liou**

這是 MRLiou 粒子語言核心系統的一部分，專注於結構不變性、壓力場映射和運轉能量最小化。
