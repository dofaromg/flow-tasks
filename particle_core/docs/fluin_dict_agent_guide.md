# Fluin Dict Agent - 字典種子記憶快照使用說明

## 概述

Fluin Dict Agent 是一個字典種子記憶快照系統，實現了以下核心功能：

```
✦Seed:⊕Echo/▽Jump.0001→⚙Fusion[⊕Code, △Fluin]
∞Trace → ζMemory^↻Loop
⊕Tool:μField/∴Map
⊕Core → ⟁1053
💬 粒子語句可封裝模組、展開人格、觸發記憶

[字典版本: DictSeed.0003]
```

## 安裝與使用

```python
from fluin_dict_agent import FluinDictAgent

# 初始化代理
agent = FluinDictAgent(storage_path="dict_seeds")
```

## 核心功能

### 1. Echo/Jump 融合 (⊕Echo/▽Jump)

Echo 和 Jump 是兩種記憶操作模式：

- **Echo (⊕Echo)**: 創建記憶共振點，可反覆觸發
- **Jump (▽Jump)**: 設置記憶跳轉點，可快速導航

```python
# 創建 Echo
agent.create_echo("greeting", "Hello, Fluin!")

# 觸發 Echo（每次觸發計數增加）
result = agent.trigger_echo("greeting")
print(result["content"])  # "Hello, Fluin!"
print(result["echo_count"])  # 1

# 設置 Jump 點
agent.set_jump_point("checkpoint", 0)

# 執行 Jump
agent.execute_jump("checkpoint")

# Echo/Jump 融合
agent.echo_jump_fusion("greeting", "checkpoint", {"fusion_key": "value"})
```

### 2. 記憶追蹤循環 (∞Trace → ζMemory^↻Loop)

所有操作都會自動記錄到記憶追蹤中：

```python
# 獲取所有追蹤記錄
trace = agent.get_trace()

# 獲取部分記錄
trace_subset = agent.get_trace(start=0, end=10)

# 創建記憶循環標記
agent.create_memory_loop("main_loop", interval=5)
```

### 3. 工具/欄位映射 (⊕Tool:μField/∴Map)

註冊工具並映射欄位值：

```python
# 註冊工具
agent.register_tool(
    tool_id="parser",
    tool_type="text_processor",
    fields=["input", "output", "format"]
)

# 映射欄位值
agent.map_field("parser", "input", "raw_text")
agent.map_field("parser", "output", "parsed_json")

# 獲取欄位映射
mappings = agent.get_field_map("parser")
```

### 4. 字典種子操作 (✦Seed)

創建和管理字典種子：

```python
# 創建字典種子
result = agent.create_dict_seed(
    seed_id="my_seed",
    data={"key": "value", "numbers": [1, 2, 3]},
    metadata={"author": "MRLiou", "purpose": "demo"}
)

# 還原字典種子
restored = agent.restore_dict_seed("my_seed")
print(restored["data"])

# 列出所有種子
seeds = agent.list_seeds()
```

### 5. 模組封裝 (💬粒子模組封裝)

將資料封裝為粒子模組：

```python
result = agent.encapsulate_module(
    module_id="config_module",
    module_data={"setting1": "value1"},
    module_type="config"
)
```

### 6. 人格展開 (△Persona)

註冊和展開 AI 人格：

```python
# 註冊人格
agent.register_persona(
    persona_id="assistant",
    name="Fluin Assistant",
    traits=["helpful", "precise", "bilingual"],
    modules=["config_module"]  # 關聯的模組
)

# 展開人格
expanded = agent.expand_persona("assistant")
print(expanded["persona"]["name"])
print(expanded["expanded_modules"])
```

### 7. 記憶觸發 (⚡Trigger)

設置和觸發記憶觸發器：

```python
# 定義觸發動作
def my_action(context):
    return f"Triggered with: {context}"

# 註冊觸發器
agent.register_trigger(
    trigger_id="alert",
    condition="when data changes",
    action=my_action
)

# 觸發
result = agent.fire_trigger("alert", {"key": "value"})
```

### 8. 系統快照

創建和還原完整系統快照：

```python
# 創建快照
snapshot = agent.create_snapshot("backup_001")
print(snapshot["summary"])

# 還原快照
agent.restore_snapshot("backup_001")
```

### 9. 粒子符號輸出

壓縮當前狀態為粒子符號表示：

```python
notation = agent.compress_to_particle_notation()
print(notation)
# 輸出:
# ✦Seed:⊕Echo/2▽Jump.0001→⚙Fusion[⊕Code, △Fluin/1]
# ∞Trace → ζMemory^↻Loop:15
# ⊕Tool:μField/1∴Map
# ⊕Core → ⟁1053
# [字典版本: DictSeed.0003]
```

## 系統資訊

獲取核心系統資訊：

```python
info = agent.get_core_info()
print(f"版本: {info['version']}")
print(f"核心索引: {info['core_index']}")
print(f"符號: {info['symbol']}")
```

## 檔案格式

- `.dseed.json`: 字典種子檔案
- `.snapshot.json`: 系統快照檔案

## 符號說明

| 符號 | 含義 |
|------|------|
| ✦Seed | 種子/核心資料 |
| ⊕Echo | 記憶共振迴響 |
| ▽Jump | 記憶跳轉點 |
| ⚙Fusion | 融合操作 |
| ∞Trace | 無限追蹤 |
| ζMemory | 記憶標記 |
| ↻Loop | 循環模式 |
| ⊕Tool | 工具註冊 |
| μField | 欄位定義 |
| ∴Map | 映射關係 |
| ⟁1053 | 核心索引號 |
| △Persona | 人格模組 |
| ⚡Trigger | 記憶觸發 |

## 互動模式

啟動互動式操作介面：

```bash
python src/fluin_dict_agent.py interactive
```

## 版本資訊

- 字典版本: DictSeed.0003
- 核心索引: ⟁1053
- Python 版本: 3.10+
