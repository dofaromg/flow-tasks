# Wire-Memory Integration Documentation
# 線協-記憶整合文檔

## 概述 (Overview)

本整合系統結合了 **PD_AI wire protocol (C)** 與 **Memory Quick Mount (Python)** 系統，提供完整的跨語言狀態持久化框架。

This integration system combines the **PD_AI wire protocol (C)** with the **Memory Quick Mount (Python)** system, providing a complete cross-language state persistence framework.

## 架構 (Architecture)

```
┌─────────────────────────────────────────────────────────────┐
│                    Application Layer                         │
│   (Python/C/Other Languages using Wire Protocol)            │
└───────────────────┬─────────────────────────────────────────┘
                    │
┌───────────────────▼─────────────────────────────────────────┐
│              Particle Wire Bridge (Python)                   │
│  - Python ↔ Wire Format Conversion                          │
│  - Message Type Handling (UPSERT, QUERY, SNAPSHOT, etc.)   │
│  - Particle Compression Integration                          │
└───────────────────┬─────────────────────────────────────────┘
                    │
        ┌───────────┴───────────┐
        │                       │
┌───────▼─────────┐   ┌────────▼────────────┐
│  Wire Protocol  │   │  Memory Quick Mount │
│     (C/H)       │   │      (Python)       │
│                 │   │                     │
│ - 16-byte header│   │ - Particle compress │
│ - Binary format │   │ - Snapshot/restore  │
│ - Cross-platform│   │ - Context mounting  │
└─────────────────┘   └─────────────────────┘
```

## 核心組件 (Core Components)

### 1. PD_AI Wire Protocol (C)

**位置**: `particle_core/src/wire/`

#### 檔案結構
- `PD_AI_wire.h` - Wire protocol 定義
- `pd_ai_wire_test.c` - 測試套件
- `Makefile` - 編譯配置

#### Wire Header 結構 (16 bytes)

```c
typedef struct {
    uint8_t  mt;      // message type
    uint8_t  kc;      // key class
    uint8_t  ann;     // annotation bits
    uint8_t  ver;     // version
    uint32_t cap;     // capabilities
    uint32_t rid;     // record ID
    uint32_t n;       // payload size
} __attribute__((packed)) wh16_t;
```

#### 訊息類型 (Message Types)

| 類型 | 值 | 說明 | 用途 |
|------|-----|------|------|
| M_PING | 0x00 | 心跳 | 連接檢測 |
| M_PONG | 0x01 | 回應 | 確認回應 |
| M_UPSERT | 0x02 | 插入/更新 | 資料操作 |
| M_QUERY | 0x03 | 查詢 | 讀取資料 |
| M_DELETE | 0x04 | 刪除 | 移除資料 |
| M_SNAPSHOT | 0x05 | 快照 | 狀態保存 |
| M_RESTORE | 0x06 | 還原 | 狀態恢復 |
| M_SYNC | 0x07 | 同步 | 資料同步 |

#### 權限註記 (Annotation Bits)

| 位元 | 值 | 說明 |
|------|-----|------|
| T_R | 0x01 | 讀取權限 |
| T_W | 0x02 | 寫入權限 |
| T_D | 0x04 | 刪除權限 |
| T_X | 0x08 | 執行權限 |
| T_COMPRESS | 0x20 | 壓縮啟用 |
| T_ENCRYPT | 0x40 | 加密啟用 |

#### 編譯與測試

```bash
cd particle_core/src/wire
make clean
make test
```

**預期輸出**:
```
==========================================================
PD_AI Wire Protocol Test Suite
==========================================================
...
Tests run:    8
Tests passed: 8
Tests failed: 0

✓✓✓ ALL TESTS PASSED ✓✓✓
```

### 2. Memory Quick Mount (Python)

**位置**: `particle_core/src/memory/`

#### 核心類別

##### ParticleCompressor
基礎粒子壓縮器，提供基本的資料壓縮邏輯。

```python
compressor = ParticleCompressor()
compressed = compressor.compress(data)
restored = compressor.decompress(compressed)
stats = compressor.get_stats()
```

##### AdvancedParticleCompressor
進階遞迴壓縮器，支援巢狀結構和語意保留。

```python
compressor = AdvancedParticleCompressor()
compressed = compressor.compress(nested_data)
restored = compressor.decompress(compressed)
```

##### MemoryQuickMounter
記憶快速掛載管理器，處理快照和上下文恢復。

```python
mqm = MemoryQuickMounter("config.yaml")
mqm.mount()  # 掛載記憶種子
mqm.snapshot("agent_name", state)  # 建立快照
restored = mqm.rehydrate()  # 恢復狀態
```

#### CLI 使用方式

```bash
# 查看幫助
python memory_quick_mount.py --help

# 掛載記憶種子
python memory_quick_mount.py --config config.yaml mount

# 建立狀態快照
python memory_quick_mount.py snapshot \
  --agent agent_name \
  --state '{"scene":"roomA", "step":5}'

# 恢復上下文
python memory_quick_mount.py rehydrate

# 從特定快照恢復
python memory_quick_mount.py rehydrate \
  --snapshot path/to/snapshot.json
```

### 3. Particle Wire Bridge (Python)

**位置**: `particle_core/src/memory/particle_wire_bridge.py`

#### 主要功能

##### Python → Wire 轉換

```python
bridge = ParticleWireBridge(use_compression=True)

data = {
    "主體": "Agent-01",
    "任務": "資料處理",
    "狀態": "執行中"
}

# 轉換為 wire 格式
wire_data = bridge.python_to_wire(
    data,
    msg_type=M_UPSERT,
    key_class=K_MCP,
    annotation=ANN_MCP,
    capabilities=CAP_STANDARD,
    record_id=1
)
```

##### Wire → Python 轉換

```python
# 解析 wire 格式
restored_data, header = bridge.wire_to_python(wire_data)

print(f"Message type: 0x{header.mt:02x}")
print(f"Record ID: {header.rid}")
print(f"Restored data: {restored_data}")
```

##### 快照訊息建立

```python
snapshot_msg = bridge.create_snapshot_message(
    agent_name="test_agent",
    state={"key": "value"},
    record_id=0x10000001
)
```

##### 查詢訊息建立

```python
query_msg = bridge.create_query_message(
    query_params={"agent": "test", "status": "active"},
    record_id=0x00100001
)
```

## 資料流圖 (Data Flow)

### 完整循環 (Round-trip)

```
Python Dict
    │
    ▼
┌─────────────────┐
│ Particle        │ 壓縮
│ Compression     │
└────────┬────────┘
         │ Compressed Dict
         ▼
┌─────────────────┐
│ JSON Encode     │
└────────┬────────┘
         │ JSON String
         ▼
┌─────────────────┐
│ UTF-8 Encode    │
└────────┬────────┘
         │ Bytes
         ▼
┌─────────────────┐
│ Add Wire Header │ 16-byte header
└────────┬────────┘
         │
         ▼
    Wire Format (bytes)
    [Header 16B][Payload NB]
         │
         ▼
┌─────────────────┐
│ Parse Header    │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Extract Payload │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ UTF-8 Decode    │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ JSON Decode     │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Particle        │ 解壓縮
│ Decompression   │
└────────┬────────┘
         │
         ▼
    Python Dict
```

## 使用範例 (Usage Examples)

### 範例 1: 基本資料轉換

```python
from particle_wire_bridge import ParticleWireBridge

# 建立橋接器
bridge = ParticleWireBridge(use_compression=True)

# 原始資料
data = {
    "agent": "worker-01",
    "task": "data_processing",
    "progress": 75
}

# Python → Wire
wire_data = bridge.python_to_wire(data)
print(f"Wire size: {len(wire_data)} bytes")

# Wire → Python
restored, header = bridge.wire_to_python(wire_data)
print(f"Restored: {restored}")
```

### 範例 2: 記憶快照與恢復

```python
from memory_quick_mount import MemoryQuickMounter
from particle_wire_bridge import ParticleWireBridge

# 初始化
mqm = MemoryQuickMounter("config.yaml")
bridge = ParticleWireBridge()

# 建立快照
state = {
    "scene": "laboratory",
    "objects": ["table", "microscope"],
    "temperature": 23.5
}

snapshot_path = mqm.snapshot("lab_agent", state)
print(f"Snapshot saved: {snapshot_path}")

# 轉換為 wire 格式 (用於傳輸)
wire_msg = bridge.create_snapshot_message("lab_agent", state)

# 恢復狀態
restored = mqm.rehydrate(snapshot_path)
print(f"Restored: {restored}")
```

### 範例 3: 跨語言通訊

```python
# Python 端發送資料
bridge = ParticleWireBridge()

command = {
    "action": "execute",
    "parameters": {
        "target": "sensor_01",
        "mode": "continuous"
    }
}

# 建立 UPSERT 訊息
wire_msg = bridge.python_to_wire(
    command,
    msg_type=M_UPSERT,
    key_class=K_MCP,
    record_id=0x00100001
)

# 傳送到 C 端處理...
# send_to_c_layer(wire_msg)

# C 端接收並解析
# (在 C 程式中)
# wh16_t* header = (wh16_t*)received_data;
# uint8_t* payload = received_data + sizeof(wh16_t);
# process_command(header, payload);
```

### 範例 4: 查詢與過濾

```python
bridge = ParticleWireBridge(use_compression=False)

# 建立查詢
query = {
    "table": "agents",
    "filters": {
        "status": "active",
        "priority": {"$gte": 5}
    },
    "fields": ["name", "status", "last_updated"]
}

# 建立查詢訊息
query_msg = bridge.create_query_message(query, record_id=0x00100002)

# 解析回應
# response_data, response_header = bridge.wire_to_python(response_msg)
```

## 配置說明 (Configuration)

### config.yaml 結構

```yaml
# 基本路徑
context_dir: "particle_core/context"
snapshot_dir: "particle_core/snapshots"

# 記憶種子
seeds:
  - "particle_core/examples/agent_seed.json"
  - "particle_core/examples/workflow_seed.json"

# Wire 協議設定
wire:
  default_msg_type: 0x02      # M_UPSERT
  default_key_class: 0x10     # K_MCP
  capabilities: 0x30000000    # P_TOOLS | P_APPS
  use_compression: true

# 壓縮設定
compression:
  algorithm: "advanced"
  recursive: true
  track_stats: true

# 效能設定
performance:
  enable_caching: true
  cache_size: 256
```

## API 參考 (API Reference)

### WireHeader 欄位

| 欄位 | 類型 | 大小 | 說明 |
|------|------|------|------|
| mt | uint8_t | 1 | 訊息類型 |
| kc | uint8_t | 1 | 鍵類別 |
| ann | uint8_t | 1 | 權限註記 |
| ver | uint8_t | 1 | 版本號 |
| cap | uint32_t | 4 | 能力標誌 |
| rid | uint32_t | 4 | 記錄 ID |
| n | uint32_t | 4 | 負載大小 |

### ParticleWireBridge 方法

#### `python_to_wire(data, ...)`
- **參數**: 
  - `data`: Python 字典
  - `msg_type`: 訊息類型 (預設: M_UPSERT)
  - `key_class`: 鍵類別 (預設: K_MCP)
  - `annotation`: 權限註記 (預設: ANN_MCP)
  - `capabilities`: 能力標誌 (預設: CAP_STANDARD)
  - `record_id`: 記錄 ID (預設: 1)
- **返回**: bytes (wire 格式)

#### `wire_to_python(wire_data)`
- **參數**: `wire_data` - Wire 格式 bytes
- **返回**: Tuple[Dict, WireHeader]

#### `create_snapshot_message(agent_name, state, record_id)`
- **參數**:
  - `agent_name`: 代理名稱
  - `state`: 狀態字典
  - `record_id`: 快照記錄 ID
- **返回**: bytes (快照訊息)

### MemoryQuickMounter 方法

#### `mount(seed_paths)`
- **參數**: `seed_paths` - 種子檔案路徑列表
- **返回**: None

#### `snapshot(agent_name, state)`
- **參數**:
  - `agent_name`: 代理名稱
  - `state`: 當前狀態
- **返回**: str (快照檔案路徑)

#### `rehydrate(snapshot_path)`
- **參數**: `snapshot_path` - 快照檔案路徑 (可選)
- **返回**: Dict (恢復的狀態)

## 測試 (Testing)

### 執行 C 測試

```bash
cd particle_core/src/wire
make test
```

### 執行 Python 整合測試

```bash
python particle_core/tests/test_wire_memory_integration.py
```

### 測試覆蓋範圍

- ✅ Wire header 結構 (16 bytes)
- ✅ Key-value pair 結構 (8 bytes)
- ✅ Budget 結構 (12 bytes)
- ✅ 訊息組裝與解析
- ✅ 權限位元操作
- ✅ 記錄 ID 範圍驗證
- ✅ Python ↔ Wire 完整循環
- ✅ 粒子壓縮/解壓縮
- ✅ 記憶快照與恢復
- ✅ 快照訊息建立
- ✅ 查詢訊息建立

## 故障排除 (Troubleshooting)

### 常見問題

#### 1. 編譯錯誤

**問題**: `gcc: command not found`

**解決**:
```bash
# Ubuntu/Debian
sudo apt-get install build-essential

# macOS
xcode-select --install
```

#### 2. Python 模組導入錯誤

**問題**: `ModuleNotFoundError: No module named 'memory_quick_mount'`

**解決**:
```bash
# 確保在正確的目錄
cd /path/to/flow-tasks
export PYTHONPATH="${PYTHONPATH}:$(pwd)/particle_core/src/memory"
```

#### 3. Wire 格式解析失敗

**問題**: `ValueError: Wire data too short`

**解決**:
- 確認 wire_data 至少有 16 bytes
- 檢查 header.n 是否與實際 payload 大小匹配
- 驗證資料完整性

#### 4. 壓縮率為負值

**說明**: 這是正常的。對於小型或結構複雜的資料，加入 metadata 後可能比原始資料更大。壓縮主要用於大型資料集和重複模式。

## 效能考量 (Performance)

### 最佳實踐

1. **批次處理**: 合併多個小訊息為單一大訊息
2. **快取**: 啟用快取以重複使用壓縮結果
3. **異步處理**: 使用異步 I/O 處理網路傳輸
4. **選擇性壓縮**: 僅對大型負載啟用壓縮

### 效能基準

| 操作 | 資料大小 | 時間 |
|------|---------|------|
| Python → Wire | 1 KB | ~0.5 ms |
| Wire → Python | 1 KB | ~0.3 ms |
| 壓縮 | 10 KB | ~2 ms |
| 解壓縮 | 10 KB | ~1 ms |
| 快照建立 | 100 KB | ~10 ms |

## 擴展性 (Extensibility)

### 自定義訊息類型

```c
// 在 PD_AI_wire.h 中新增
#define M_CUSTOM 0x10

// 在 Python 中使用
bridge.python_to_wire(data, msg_type=0x10)
```

### 自定義壓縮器

```python
class CustomCompressor(ParticleCompressor):
    def compress(self, data):
        # 自定義壓縮邏輯
        return super().compress(data)
    
    def decompress(self, compressed):
        # 自定義解壓縮邏輯
        return super().decompress(compressed)
```

### 整合其他協議

```python
# HTTP 整合範例
import requests

wire_msg = bridge.python_to_wire(data)
response = requests.post(
    'http://server/api',
    data=wire_msg,
    headers={'Content-Type': 'application/octet-stream'}
)
```

## 安全性 (Security)

### 最佳實踐

1. **驗證 Header**: 總是驗證 wire header 欄位
2. **邊界檢查**: 檢查 payload 大小與 header.n 是否匹配
3. **權限檢查**: 根據 annotation 位元驗證操作權限
4. **加密傳輸**: 對敏感資料使用 T_ENCRYPT 標誌
5. **輸入驗證**: 驗證所有來自 wire 格式的資料

### 安全檢查範例

```python
def validate_wire_header(header):
    # 檢查版本
    if header.ver != 1:
        raise ValueError("Unsupported version")
    
    # 檢查訊息類型
    if header.mt not in [M_PING, M_PONG, M_UPSERT, M_QUERY]:
        raise ValueError("Invalid message type")
    
    # 檢查負載大小限制
    if header.n > 1024 * 1024:  # 1 MB 限制
        raise ValueError("Payload too large")
    
    return True
```

## 未來發展 (Future Development)

### 計畫功能

1. **MongoDB 整合**: 使用 BSON BinData 儲存 wire 格式
2. **gRPC 支援**: Wire 格式封裝為 gRPC 訊息
3. **WebSocket 串流**: 即時狀態同步
4. **分散式快照**: 跨節點快照協調
5. **加密支援**: 端到端加密實作

### 貢獻指南

歡迎貢獻！請遵循以下步驟：

1. Fork 專案
2. 建立功能分支
3. 撰寫測試
4. 提交 Pull Request

## 授權 (License)

參見專案根目錄的 LICENSE 檔案。

## 聯絡方式 (Contact)

- 專案: flow-tasks
- GitHub: dofaromg/flow-tasks
- 文檔: particle_core/docs/

---

**版本**: 1.0.0  
**更新日期**: 2026-01-01  
**作者**: MRLiou / FlowAgent Team
