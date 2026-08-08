# Memory Quick Mount (MQM) 模組文檔

## 功能概述 / Overview

Memory Quick Mount (MQM) 是一個記憶體快速掛載和狀態管理工具，提供以下核心功能：

Memory Quick Mount (MQM) is a memory quick mount and state management tool that provides the following core features:

### 核心特性 / Core Features

- **記憶種子快速掛載** / **Quick Memory Seed Mounting**: 一鍵載入和整合記憶種子到運行上下文
- **代理狀態快照** / **Agent State Snapshots**: 記錄代理執行狀態的時間點快照
- **狀態重新載入** / **State Rehydration**: 從快照恢復之前的代理狀態
- **粒子壓縮格式** / **Particle Compression Format**: 使用粒子符號壓縮和表示複雜資料結構
- **離線本地運作** / **Offline Local Operation**: 無需外部 API，完全本地化運作
- **雙格式支援** / **Dual Format Support**: 支援 JSON 和 YAML 格式的種子檔案

## 安裝說明 / Installation

### 依賴安裝 / Install Dependencies

```bash
cd particle_core
pip install -r requirements.txt
```

主要依賴 / Main Dependencies:
- `pyyaml>=6.0` - YAML 檔案解析 / YAML file parsing
- `rich` - 終端機美化輸出 / Terminal rich output
- `fastapi` - API 框架 (可選) / API framework (optional)
- `uvicorn` - ASGI 伺服器 (可選) / ASGI server (optional)

## 使用範例 / Usage Examples

### 1. 掛載記憶種子 / Mount Memory Seeds

```bash
# 使用配置檔案掛載種子
# Mount seeds using configuration file
python particle_core/src/memory_quick_mount.py --config particle_core/config/mqm_config.yaml mount
```

輸出示例 / Output Example:
```
🔧 開始掛載記憶種子...
🔧 Starting memory seed mount...

✓ 成功載入種子: particle_core/examples/memory_seed_example.json
✓ Successfully loaded seed: particle_core/examples/memory_seed_example.json

✓ 成功掛載 1 個種子
✓ Successfully mounted 1 seed(s)
```

### 2. 記錄快照 / Record Snapshot

```bash
# 為代理記錄狀態快照
# Record state snapshot for agent
python particle_core/src/memory_quick_mount.py \
  --config particle_core/config/mqm_config.yaml \
  snapshot \
  --agent "FlowAgent" \
  --state '{"scene":"初始化完成","status":"ready","progress":0.5}'
```

輸出示例 / Output Example:
```
📸 為代理 'FlowAgent' 建立快照...
📸 Creating snapshot for agent 'FlowAgent'...

✓ 快照已儲存: snapshots/snapshot_FlowAgent_20251231_120000.json
✓ Snapshot saved: snapshots/snapshot_FlowAgent_20251231_120000.json

┌─ 粒子壓縮表示 / Particle Compressed Representation ─┐
│ ⊕scene:初始化完成                                    │
│ ⊕status:ready                                       │
│ ⊕progress:0.5                                       │
└─────────────────────────────────────────────────────┘
```

### 3. 重新載入狀態 / Rehydrate State

```bash
# 重新載入特定代理的最新狀態
# Rehydrate latest state for specific agent
python particle_core/src/memory_quick_mount.py \
  --config particle_core/config/mqm_config.yaml \
  rehydrate \
  --agent "FlowAgent"
```

輸出示例 / Output Example:
```
💧 重新載入狀態...
💧 Rehydrating state...

✓ 成功重新載入代理 'FlowAgent' 的狀態
✓ Successfully rehydrated state for agent 'FlowAgent'
時間戳記: 2025-12-31T12:00:00.000000
Timestamp: 2025-12-31T12:00:00.000000
```

列出所有可用快照 / List All Available Snapshots:
```bash
# 不指定代理名稱時，列出所有快照
# Without specifying agent name, list all snapshots
python particle_core/src/memory_quick_mount.py \
  --config particle_core/config/mqm_config.yaml \
  rehydrate
```

## API 文檔 / API Documentation

### ParticleCompressor 類別

基礎粒子壓縮器，提供基本的資料壓縮功能。

Basic particle compressor providing fundamental data compression.

#### 方法 / Methods

##### `compress(data: Dict[str, Any]) -> str`

將資料壓縮為粒子表示法。

Compress data into particle notation.

**參數 / Parameters:**
- `data`: 要壓縮的字典資料 / Dictionary data to compress

**返回 / Returns:**
- 粒子壓縮字串 / Particle compressed string

**範例 / Example:**
```python
from memory_quick_mount import ParticleCompressor

compressor = ParticleCompressor()
data = {
    'time': '2025-12-31',
    'subject': 'Agent',
    'action': 'execute',
    'item': 'task_001'
}
compressed = compressor.compress(data)
# 輸出: ⏰[2025-12-31]→👤[Agent]→⚡[execute]→📦[task_001]
```

##### `decompress(compressed: str) -> Dict[str, Any]`

將粒子表示法解壓縮為原始資料。

Decompress particle notation to original data.

**參數 / Parameters:**
- `compressed`: 粒子壓縮字串 / Particle compressed string

**返回 / Returns:**
- 解壓縮後的字典資料 / Decompressed dictionary data

**範例 / Example:**
```python
compressed = "⏰[2025-12-31]→👤[Agent]→⚡[execute]→📦[task_001]"
data = compressor.decompress(compressed)
# 輸出: {'time': '2025-12-31', 'subject': 'Agent', 'action': 'execute', 'item': 'task_001'}
```

#### 支援的粒子編碼 / Supported Particle Encodings

| 符號 / Symbol | 鍵 / Key | 說明 / Description |
|--------------|---------|-------------------|
| ⏰ | time | 時間 / Time |
| 👤 | subject | 主體 / Subject |
| 🤝 | partner | 夥伴 / Partner |
| ⚡ | action | 行動 / Action |
| 📦 | item | 項目 / Item |
| 📍 | location | 位置 / Location |
| 🔄 | state | 狀態 / State |
| ✅ | result | 結果 / Result |

### AdvancedParticleCompressor 類別

進階粒子壓縮器，支援巢狀結構的壓縮。

Advanced particle compressor supporting nested structure compression.

繼承自 `ParticleCompressor`，額外提供以下方法：

Inherits from `ParticleCompressor`, provides additional methods:

##### `compress_nested(data: Any, level: int = 0) -> str`

壓縮巢狀結構（包含字典和列表）。

Compress nested structures (including dictionaries and lists).

**參數 / Parameters:**
- `data`: 要壓縮的資料（支援字典、列表等） / Data to compress (supports dict, list, etc.)
- `level`: 巢狀層級（預設 0）/ Nesting level (default 0)

**返回 / Returns:**
- 巢狀粒子壓縮字串 / Nested particle compressed string

**範例 / Example:**
```python
from memory_quick_mount import AdvancedParticleCompressor

compressor = AdvancedParticleCompressor()
data = {
    'agent': 'FlowAgent',
    'config': {
        'mode': 'production',
        'features': ['mount', 'snapshot']
    }
}
compressed = compressor.compress_nested(data)
print(compressed)
```

輸出 / Output:
```
⊕agent:FlowAgent
⊕config⟨
  ⊕mode:production
  ⊕features⟨
    ⊕[0]:mount
    ⊕[1]:snapshot
  ⟩
⟩
```

### MemoryQuickMounter 類別

核心記憶掛載類別，提供完整的記憶種子管理功能。

Core memory mounting class providing complete memory seed management.

#### 初始化 / Initialization

```python
from memory_quick_mount import MemoryQuickMounter

# 使用配置檔案初始化
# Initialize with config file
mounter = MemoryQuickMounter(config_path='particle_core/config/mqm_config.yaml')

# 使用預設設定初始化
# Initialize with default settings
mounter = MemoryQuickMounter()
```

#### 方法 / Methods

##### `load_seed(seed_path: str) -> Optional[Dict[str, Any]]`

載入記憶種子檔案（支援 JSON/YAML）。

Load memory seed file (supports JSON/YAML).

**參數 / Parameters:**
- `seed_path`: 種子檔案路徑 / Seed file path

**返回 / Returns:**
- 種子資料字典或 None（失敗時）/ Seed data dictionary or None (on failure)

**範例 / Example:**
```python
seed_data = mounter.load_seed('particle_core/examples/memory_seed_example.json')
if seed_data:
    print(f"載入成功: {seed_data['metadata']['version']}")
```

##### `mount() -> bool`

掛載配置中指定的所有記憶種子到整合上下文。

Mount all memory seeds specified in config to integration context.

**返回 / Returns:**
- 掛載是否成功 / Whether mount was successful

**範例 / Example:**
```python
success = mounter.mount()
if success:
    print("所有種子已成功掛載")
```

##### `snapshot(agent_name: str, state: Dict[str, Any]) -> bool`

為指定代理記錄狀態快照。

Record state snapshot for specified agent.

**參數 / Parameters:**
- `agent_name`: 代理名稱 / Agent name
- `state`: 狀態資料 / State data

**返回 / Returns:**
- 快照是否成功 / Whether snapshot was successful

**範例 / Example:**
```python
state = {
    'scene': '初始化完成',
    'status': 'ready',
    'progress': 0.5
}
success = mounter.snapshot('FlowAgent', state)
```

##### `rehydrate(agent_name: Optional[str] = None) -> Optional[Dict[str, Any]]`

重新載入代理的最後已知狀態。

Rehydrate agent's last known state.

**參數 / Parameters:**
- `agent_name`: 代理名稱（可選，不提供時列出所有快照）/ Agent name (optional, list all snapshots if not provided)

**返回 / Returns:**
- 快照資料或 None / Snapshot data or None

**範例 / Example:**
```python
# 重新載入特定代理
# Rehydrate specific agent
snapshot = mounter.rehydrate('FlowAgent')
if snapshot:
    print(f"已恢復狀態: {snapshot['state']}")

# 列出所有快照
# List all snapshots
mounter.rehydrate()
```

## 粒子壓縮範例 / Particle Compression Examples

### 基礎壓縮 / Basic Compression

```python
from memory_quick_mount import ParticleCompressor

compressor = ParticleCompressor()

# 任務執行資料
# Task execution data
task_data = {
    'time': '2025-12-31T12:00:00',
    'subject': 'FlowAgent',
    'action': 'process_task',
    'item': 'task_12345',
    'result': 'success'
}

compressed = compressor.compress(task_data)
print("壓縮結果 / Compressed:")
print(compressed)
# ⏰[2025-12-31T12:00:00]→👤[FlowAgent]→⚡[process_task]→📦[task_12345]→✅[success]

# 解壓縮
# Decompress
decompressed = compressor.decompress(compressed)
print("\n解壓縮結果 / Decompressed:")
print(decompressed)
```

### 進階巢狀壓縮 / Advanced Nested Compression

```python
from memory_quick_mount import AdvancedParticleCompressor

compressor = AdvancedParticleCompressor()

# 複雜的代理狀態
# Complex agent state
agent_state = {
    'agent_id': 'FlowAgent_001',
    'status': 'active',
    'tasks': [
        {'id': 'task_1', 'priority': 'high'},
        {'id': 'task_2', 'priority': 'low'}
    ],
    'config': {
        'memory_mode': 'persistent',
        'compression': True,
        'features': {
            'snapshot': True,
            'rehydrate': True
        }
    }
}

compressed = compressor.compress_nested(agent_state)
print("巢狀壓縮結果 / Nested Compressed:")
print(compressed)
```

輸出 / Output:
```
⊕agent_id:FlowAgent_001
🔄[status=active]
⊕tasks⟨
  ⊕[0]⟨
    ⊕id:task_1
    ⊕priority:high
  ⟩
  ⊕[1]⟨
    ⊕id:task_2
    ⊕priority:low
  ⟩
⟩
⊕config⟨
  ⊕memory_mode:persistent
  ⊕compression:True
  ⊕features⟨
    ⊕snapshot:True
    ⊕rehydrate:True
  ⟩
⟩
```

### 完整工作流程範例 / Complete Workflow Example

```python
from memory_quick_mount import MemoryQuickMounter

# 1. 初始化掛載器
# Initialize mounter
mounter = MemoryQuickMounter(config_path='particle_core/config/mqm_config.yaml')

# 2. 掛載記憶種子
# Mount memory seeds
print("步驟 1: 掛載種子 / Step 1: Mount seeds")
mounter.mount()

# 3. 執行任務並記錄快照
# Execute task and record snapshot
print("\n步驟 2: 記錄快照 / Step 2: Record snapshot")
state = {
    'scene': '任務執行中',
    'current_task': 'data_processing',
    'progress': 0.75,
    'errors': []
}
mounter.snapshot('FlowAgent', state)

# 4. 模擬代理重啟，重新載入狀態
# Simulate agent restart, rehydrate state
print("\n步驟 3: 重新載入狀態 / Step 3: Rehydrate state")
restored_snapshot = mounter.rehydrate('FlowAgent')
if restored_snapshot:
    print(f"已恢復進度: {restored_snapshot['state']['progress'] * 100}%")
```

## 配置檔案格式 / Configuration File Format

### YAML 格式 / YAML Format

```yaml
# 上下文儲存目錄
# Context storage directory
context_dir: context

# 快照儲存目錄
# Snapshot storage directory
snapshot_dir: snapshots

# 要掛載的種子檔案列表
# List of seed files to mount
seeds:
  - particle_core/examples/memory_seed_example.json
  - path/to/another_seed.yaml
  - path/to/third_seed.json
```

### JSON 格式 / JSON Format

```json
{
  "context_dir": "context",
  "snapshot_dir": "snapshots",
  "seeds": [
    "particle_core/examples/memory_seed_example.json",
    "path/to/another_seed.yaml"
  ]
}
```

## 記憶種子格式 / Memory Seed Format

記憶種子可以包含任意結構，但建議包含以下欄位：

Memory seeds can contain arbitrary structure, but should include these fields:

```json
{
  "structure": {
    "core_persona": "代理人格定義 / Agent persona definition",
    "semantic_roles": {
      "role_name": "角色描述 / Role description"
    },
    "jump_sequence": ["步驟1 / Step 1", "步驟2 / Step 2"],
    "regen_path": {
      "checkpoint_name": "檢查點路徑 / Checkpoint path"
    }
  },
  "metadata": {
    "version": "1.0.0",
    "created_at": "2025-12-31T00:00:00Z",
    "description": "種子描述 / Seed description"
  }
}
```

## 目錄結構 / Directory Structure

MQM 模組運作時會建立以下目錄結構：

MQM module creates the following directory structure:

```
project_root/
├── context/                          # 上下文目錄 / Context directory
│   └── mounted_context.json         # 已掛載的上下文 / Mounted context
├── snapshots/                        # 快照目錄 / Snapshot directory
│   ├── snapshot_AgentName_*.json    # 快照檔案 / Snapshot files
│   └── latest_AgentName.json        # 最新快照指標 / Latest snapshot pointer
└── particle_core/
    ├── config/
    │   └── mqm_config.yaml          # MQM 配置 / MQM configuration
    └── examples/
        └── memory_seed_example.json # 範例種子 / Example seed
```

## 錯誤處理 / Error Handling

MQM 模組提供完善的錯誤處理：

MQM module provides comprehensive error handling:

### 檔案不存在 / File Not Found

```python
seed_data = mounter.load_seed('nonexistent.json')
# 輸出: ✗ 種子檔案不存在: nonexistent.json
# Output: ✗ Seed file not found: nonexistent.json
```

### JSON 解析失敗 / JSON Parsing Failed

```python
# 若檔案包含無效的 JSON
# If file contains invalid JSON
seed_data = mounter.load_seed('invalid.json')
# 輸出: ✗ JSON 解析失敗: ...
# Output: ✗ JSON parsing failed: ...
```

### 快照不存在 / Snapshot Not Found

```python
snapshot = mounter.rehydrate('NonExistentAgent')
# 輸出: ⚠ 找不到代理 'NonExistentAgent' 的快照
# Output: ⚠ No snapshot found for agent 'NonExistentAgent'
```

## 最佳實踐 / Best Practices

1. **定期快照** / **Regular Snapshots**: 在關鍵操作點記錄快照
2. **命名規範** / **Naming Conventions**: 使用有意義的代理名稱
3. **版本控制** / **Version Control**: 在種子的 metadata 中記錄版本
4. **備份策略** / **Backup Strategy**: 定期備份 snapshots 目錄
5. **清理舊快照** / **Clean Old Snapshots**: 定期清理不需要的舊快照檔案

## 進階用途 / Advanced Usage

### 程式化使用 / Programmatic Usage

```python
from memory_quick_mount import MemoryQuickMounter, AdvancedParticleCompressor

class MyAgent:
    def __init__(self):
        self.mounter = MemoryQuickMounter()
        self.state = {'initialized': False}
    
    def initialize(self):
        # 掛載記憶種子
        # Mount memory seeds
        self.mounter.mount()
        self.state['initialized'] = True
        
        # 記錄初始化快照
        # Record initialization snapshot
        self.mounter.snapshot('MyAgent', self.state)
    
    def save_checkpoint(self, state_update):
        # 更新狀態
        # Update state
        self.state.update(state_update)
        
        # 記錄檢查點快照
        # Record checkpoint snapshot
        self.mounter.snapshot('MyAgent', self.state)
    
    def restore_from_checkpoint(self):
        # 恢復最後的檢查點
        # Restore last checkpoint
        snapshot = self.mounter.rehydrate('MyAgent')
        if snapshot:
            self.state = snapshot['state']
            return True
        return False

# 使用範例
# Usage example
agent = MyAgent()
agent.initialize()
agent.save_checkpoint({'task': 'processing', 'progress': 0.5})
agent.restore_from_checkpoint()
```

### 與其他模組整合 / Integration with Other Modules

```python
# 與 memory_archive_seed 整合
# Integration with memory_archive_seed
from memory_archive_seed import MemoryArchiveSeed
from memory_quick_mount import MemoryQuickMounter

archive = MemoryArchiveSeed()
mounter = MemoryQuickMounter()

# 從封存創建種子並掛載
# Create seed from archive and mount
seed = archive.create_seed({'data': 'value'})
# ... 將種子儲存為檔案並在配置中引用
# ... Save seed as file and reference in config
mounter.mount()
```

## 疑難排解 / Troubleshooting

### 問題：無法載入配置檔案 / Issue: Cannot Load Config File

**解決方案 / Solution:**
- 確認檔案路徑正確 / Verify file path is correct
- 確認檔案格式 (YAML/JSON) / Verify file format (YAML/JSON)
- 檢查檔案權限 / Check file permissions

### 問題：快照未儲存 / Issue: Snapshot Not Saved

**解決方案 / Solution:**
- 確認 snapshots 目錄存在且可寫 / Verify snapshots directory exists and is writable
- 檢查磁碟空間 / Check disk space
- 查看錯誤訊息 / Check error messages

### 問題：粒子壓縮格式異常 / Issue: Particle Compression Format Issue

**解決方案 / Solution:**
- 確認資料格式正確 / Verify data format is correct
- 使用 AdvancedParticleCompressor 處理巢狀結構 / Use AdvancedParticleCompressor for nested structures
- 檢查特殊字符 / Check for special characters

## 相關文檔 / Related Documentation

- [記憶封存種子說明](記憶封存種子說明.md)
- [本地執行說明](本地執行說明.md)
- [Particle Core README](../README.md)

## 版本歷史 / Version History

- **v1.0.0** (2025-12-31): 初始版本發布 / Initial release
  - 基礎粒子壓縮器 / Basic particle compressor
  - 進階巢狀壓縮 / Advanced nested compression
  - 記憶種子掛載 / Memory seed mounting
  - 狀態快照與重新載入 / State snapshot and rehydration
  - CLI 命令列介面 / CLI command-line interface

## 授權 / License

遵循專案主授權條款。

Follows the main project license terms.
