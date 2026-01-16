# Memory Cache Disk Mapping Documentation
# 記憶快取磁碟映射文檔

## 概述 (Overview)

Memory Cache Disk Mapping System provides LRU (Least Recently Used) cache with automatic disk persistence for efficient state management.

記憶快取磁碟映射系統提供 LRU（最近最少使用）快取，配合自動磁碟持久化，實現高效的狀態管理。

## 核心功能 (Core Features)

### 1. LRU Cache 策略

- **最近最少使用淘汰**: 自動淘汰最久未使用的項目
- **自動大小管理**: 配置最大快取大小
- **存取統計追蹤**: 命中率、未命中率、淘汰次數等

### 2. Automatic Disk Persistence 自動磁碟持久化

- **淘汰項目持久化**: 被淘汰的項目自動保存到磁碟
- **背景自動同步**: 定期將快取內容同步到磁碟
- **啟動時預熱**: 從磁碟載入既有快取項目

### 3. Integration with Memory Quick Mount

- **無縫整合**: 與 Memory Quick Mount 系統完全整合
- **快取感知快照**: 快照時自動快取狀態
- **快速恢復**: 優先從快取恢復，提升效能

## 架構 (Architecture)

```
┌─────────────────────────────────────────────────────────────┐
│                   Application Layer                          │
│           (Memory Quick Mount / User Code)                   │
└──────────────────────────┬──────────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────────┐
│              MemoryCacheDiskMapper                           │
│         High-level cache interface                           │
│  - get_state() / set_state()                                │
│  - Cache statistics                                          │
│  - Shutdown management                                       │
└──────────────────────────┬──────────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────────┐
│                    LRUCache                                  │
│         Core LRU implementation                              │
│  - OrderedDict-based LRU                                    │
│  - Eviction policy                                           │
│  - Disk I/O operations                                       │
└──────────────────────────┬──────────────────────────────────┘
                           │
              ┌────────────┴────────────┐
              │                         │
┌─────────────▼────────────┐   ┌───────▼──────────────┐
│   Memory Cache           │   │   Disk Storage       │
│   (OrderedDict)          │   │   (JSON files)       │
│                          │   │                      │
│ - Fast access            │   │ - Persistence        │
│ - Limited size           │   │ - Unlimited storage  │
│ - Volatile               │   │ - Durable            │
└──────────────────────────┘   └──────────────────────┘
```

## 配置 (Configuration)

### config.yaml 設定

```yaml
# Cache directory
cache_dir: "particle_core/cache"

# Performance settings
performance:
  # Enable caching
  enable_caching: true
  
  # Maximum cache size (number of entries)
  cache_size: 256
```

### Python 配置

```python
from particle_core.src.memory.memory_cache_disk import MemoryCacheDiskMapper

config = {
    "performance": {
        "enable_caching": True,
        "cache_size": 256
    },
    "cache_dir": "particle_core/cache"
}

mapper = MemoryCacheDiskMapper(config)
```

## API Reference

### LRUCache Class

#### Constructor

```python
LRUCache(
    max_size: int = 256,
    cache_dir: str = "particle_core/cache",
    auto_persist: bool = True,
    persist_interval: int = 30
)
```

**參數 (Parameters)**:
- `max_size`: 快取最大項目數 (Maximum cache entries)
- `cache_dir`: 磁碟快取目錄 (Disk cache directory)
- `auto_persist`: 啟用自動持久化 (Enable auto-persistence)
- `persist_interval`: 自動持久化間隔（秒）(Auto-persist interval in seconds)

#### Methods

##### get(key: str) → Optional[Any]

Get value from cache (LRU access).

```python
value = cache.get("my_key")
if value is not None:
    print(f"Cache hit: {value}")
else:
    print("Cache miss")
```

##### put(key: str, value: Any)

Put value into cache.

```python
cache.put("my_key", {"data": "value"})
```

##### delete(key: str) → bool

Delete key from cache and disk.

```python
deleted = cache.delete("my_key")
```

##### clear()

Clear all cache entries.

```python
cache.clear()
```

##### get_stats() → Dict[str, Any]

Get cache statistics.

```python
stats = cache.get_stats()
print(f"Hit rate: {stats['hit_rate']:.2%}")
print(f"Cache size: {stats['cache_size']}/{stats['max_size']}")
```

**返回的統計資訊 (Returned statistics)**:
- `hits`: 快取命中次數
- `misses`: 快取未命中次數
- `evictions`: 淘汰次數
- `disk_reads`: 磁碟讀取次數
- `disk_writes`: 磁碟寫入次數
- `total_requests`: 總請求數
- `cache_size`: 當前快取大小
- `max_size`: 最大快取大小
- `hit_rate`: 命中率 (0.0-1.0)
- `utilization`: 使用率 (0.0-1.0)

##### persist_all()

Manually persist all cache entries to disk.

```python
cache.persist_all()
```

##### shutdown()

Shutdown cache and persist final state.

```python
cache.shutdown()
```

### MemoryCacheDiskMapper Class

#### Constructor

```python
MemoryCacheDiskMapper(config: Optional[Dict[str, Any]] = None)
```

#### Methods

##### get_state(key: str) → Optional[Any]

Get state from cache.

```python
state = mapper.get_state("agent_1")
```

##### set_state(key: str, state: Any)

Set state in cache.

```python
mapper.set_state("agent_1", {"status": "active"})
```

##### delete_state(key: str) → bool

Delete state from cache.

```python
deleted = mapper.delete_state("agent_1")
```

##### get_cache_stats() → Dict[str, Any]

Get cache statistics.

```python
stats = mapper.get_cache_stats()
```

##### persist()

Manually trigger cache persistence.

```python
mapper.persist()
```

##### shutdown()

Shutdown cache system.

```python
mapper.shutdown()
```

### MemoryQuickMounter Integration

新增的快取感知方法 (New cache-aware methods):

##### get_cached_state(key: str) → Optional[Dict[str, Any]]

Get state from cache.

```python
state = mqm.get_cached_state("agent:worker-01")
```

##### set_cached_state(key: str, state: Dict[str, Any])

Set state in cache.

```python
mqm.set_cached_state("agent:worker-01", state)
```

##### snapshot_with_cache(agent_name: str, state: Dict[str, Any]) → str

Create snapshot and cache it.

```python
snapshot_path = mqm.snapshot_with_cache("worker-01", state)
```

##### rehydrate_with_cache(snapshot_path: Optional[str] = None, agent_name: Optional[str] = None) → Dict[str, Any]

Rehydrate with cache lookup (優先從快取恢復).

```python
# 優先從快取恢復 (Try cache first)
state = mqm.rehydrate_with_cache(agent_name="worker-01")

# 從快照恢復 (Fall back to snapshot)
state = mqm.rehydrate_with_cache(snapshot_path="path/to/snapshot.json")
```

##### get_cache_stats() → Dict[str, Any]

Get cache statistics.

```python
stats = mqm.get_cache_stats()
print(f"Hit rate: {stats['hit_rate']:.2%}")
```

##### persist_cache()

Manually persist cache.

```python
mqm.persist_cache()
```

##### shutdown()

Shutdown and cleanup.

```python
mqm.shutdown()
```

## 使用範例 (Usage Examples)

### Example 1: Basic Cache Operations

```python
from memory_cache_disk import MemoryCacheDiskMapper

# Initialize mapper
config = {
    "performance": {"enable_caching": True, "cache_size": 100},
    "cache_dir": "particle_core/cache"
}
mapper = MemoryCacheDiskMapper(config)

# Store states
states = {
    "agent_1": {"status": "active", "task": "processing"},
    "agent_2": {"status": "idle", "task": None},
    "agent_3": {"status": "error", "task": "failed"}
}

for key, state in states.items():
    mapper.set_state(key, state)

# Retrieve states
for key in states.keys():
    state = mapper.get_state(key)
    print(f"{key}: {state}")

# Check statistics
stats = mapper.get_cache_stats()
print(f"Hit rate: {stats['hit_rate']:.2%}")

# Cleanup
mapper.shutdown()
```

### Example 2: MemoryQuickMounter with Cache

```python
from memory_quick_mount import MemoryQuickMounter

# Initialize with cache enabled
mqm = MemoryQuickMounter("config.yaml")

# Create snapshot with caching
state = {
    "scene": "laboratory",
    "objects": ["microscope", "samples"],
    "temperature": 23.5
}

snapshot_path = mqm.snapshot_with_cache("lab_agent", state)

# Later, quick restore from cache
restored = mqm.rehydrate_with_cache(agent_name="lab_agent")
print(f"Restored: {restored}")

# Check cache performance
stats = mqm.get_cache_stats()
print(f"Cache hit rate: {stats['hit_rate']:.2%}")
print(f"Cache utilization: {stats['utilization']:.2%}")

# Cleanup
mqm.shutdown()
```

### Example 3: Cache Warmup and Persistence

```python
from memory_cache_disk import LRUCache

# Create cache (automatically warms up from disk)
cache = LRUCache(
    max_size=50,
    cache_dir="/path/to/cache",
    auto_persist=True,
    persist_interval=60  # Persist every 60 seconds
)

# Cache automatically loads existing entries from disk
print("Cache warmed up from disk")

# Use cache...
cache.put("key1", "value1")
cache.put("key2", "value2")

# Automatic persistence runs in background
# Manual persist if needed
cache.persist_all()

# Shutdown (final persist)
cache.shutdown()
```

## 效能考量 (Performance Considerations)

### Best Practices

1. **選擇適當的快取大小 (Choose appropriate cache size)**
   - 考慮記憶體限制 (Consider memory constraints)
   - 平衡命中率與記憶體使用 (Balance hit rate vs memory usage)
   - 建議：256-1024 個項目 (Recommended: 256-1024 entries)

2. **調整自動持久化間隔 (Adjust auto-persist interval)**
   - 頻繁持久化：資料更安全但效能較低 (Frequent: safer but slower)
   - 較長間隔：效能更好但風險較高 (Longer: faster but riskier)
   - 建議：30-60 秒 (Recommended: 30-60 seconds)

3. **適當的鍵命名 (Proper key naming)**
   - 使用描述性鍵名 (Use descriptive keys)
   - 避免過長的鍵 (Avoid overly long keys)
   - 範例：`agent:worker-01`, `state:scene-laboratory`

4. **定期清理 (Regular cleanup)**
   - 刪除不再需要的項目 (Delete unused entries)
   - 監控磁碟使用量 (Monitor disk usage)
   - 定期清空過時快取 (Periodically clear stale cache)

### Performance Metrics

| Operation | Time Complexity | Typical Time |
|-----------|----------------|--------------|
| get() - Memory hit | O(1) | < 1 μs |
| get() - Disk hit | O(1) | 1-5 ms |
| put() | O(1) | < 1 μs |
| Eviction | O(1) | 1-5 ms (disk write) |
| persist_all() | O(n) | n × 1-5 ms |

## 故障排除 (Troubleshooting)

### Cache not enabled

**問題**: Cache operations don't work

**解決方案**:
```python
# Check config
config = {
    "performance": {
        "enable_caching": True,  # Ensure this is True
        "cache_size": 256
    }
}
```

### Disk write errors

**問題**: "Failed to save cache entry to disk"

**解決方案**:
- Ensure cache directory exists and is writable
- Check disk space
- Verify file permissions

### High miss rate

**問題**: Low cache hit rate

**解決方案**:
- Increase cache size
- Check access patterns (sequential vs random)
- Review eviction behavior

### Memory usage too high

**問題**: Cache consuming too much memory

**解決方案**:
- Decrease `cache_size` configuration
- Enable compression for large objects
- Consider object size limits

## 測試 (Testing)

Run the test suite:

```bash
# Run all cache tests
python particle_core/tests/test_memory_cache_disk.py

# Run specific test
python -c "from test_memory_cache_disk import test_lru_basic_operations; test_lru_basic_operations()"

# Run demo
python particle_core/src/memory/memory_cache_disk.py
```

## 未來增強 (Future Enhancements)

1. **多層快取 (Multi-tier caching)**
   - L1: Memory cache
   - L2: Disk cache
   - L3: Remote cache (Redis, Memcached)

2. **壓縮支援 (Compression support)**
   - Compress large objects before disk write
   - Reduce disk space usage

3. **快取預熱策略 (Cache warmup strategies)**
   - Priority-based warmup
   - Predictive pre-loading

4. **分散式快取 (Distributed caching)**
   - Share cache across nodes
   - Cache synchronization

5. **TTL 支援 (TTL support)**
   - Time-to-live for cache entries
   - Automatic expiration

---

**版本 (Version)**: 1.0.0  
**更新日期 (Last Updated)**: 2026-01-02  
**作者 (Author)**: FlowAgent Team
