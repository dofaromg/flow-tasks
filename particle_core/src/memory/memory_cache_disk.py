#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Memory Cache Disk Mapping System
記憶快取磁碟映射系統

Provides LRU cache with automatic disk persistence for memory state management.

Features:
- LRU (Least Recently Used) cache eviction policy
- Automatic persistence to disk
- Cache warmup from disk on startup
- Cache hit/miss statistics tracking
- Configurable cache size and persistence intervals
"""

import json
import time
import threading
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime
from collections import OrderedDict


class LRUCache:
    """
    LRU Cache with disk persistence
    LRU 快取配合磁碟持久化
    
    Implements Least Recently Used eviction policy with automatic
    synchronization to disk storage.
    """
    
    def __init__(
        self,
        max_size: int = 256,
        cache_dir: str = "particle_core/cache",
        auto_persist: bool = True,
        persist_interval: int = 30
    ):
        """
        Initialize LRU Cache
        
        Args:
            max_size: Maximum number of cache entries
            cache_dir: Directory for cache persistence
            auto_persist: Enable automatic background persistence
            persist_interval: Seconds between auto-persist operations
        """
        self.max_size = max_size
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # OrderedDict maintains insertion order, perfect for LRU
        self.cache: OrderedDict = OrderedDict()
        
        # Statistics
        self.stats = {
            "hits": 0,
            "misses": 0,
            "evictions": 0,
            "disk_reads": 0,
            "disk_writes": 0,
            "total_requests": 0
        }
        
        # Auto-persistence
        self.auto_persist = auto_persist
        self.persist_interval = persist_interval
        self._persist_lock = threading.Lock()
        self._persist_thread = None
        self._stop_persist = threading.Event()
        
        # Load cache from disk on startup
        self._warmup_from_disk()
        
        # Start auto-persist thread
        if self.auto_persist:
            self._start_auto_persist()
    
    def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache (LRU access)
        
        Args:
            key: Cache key
            
        Returns:
            Cached value or None if not found
        """
        self.stats["total_requests"] += 1
        
        if key in self.cache:
            # Move to end (most recently used)
            self.cache.move_to_end(key)
            self.stats["hits"] += 1
            return self.cache[key]["value"]
        else:
            self.stats["misses"] += 1
            # Try to load from disk
            disk_value = self._load_from_disk(key)
            if disk_value is not None:
                self.put(key, disk_value, from_disk=True)
                return disk_value
            return None
    
    def put(self, key: str, value: Any, from_disk: bool = False):
        """
        Put value into cache
        
        Args:
            key: Cache key
            value: Value to cache
            from_disk: Internal flag indicating load from disk
        """
        if not from_disk:
            self.stats["total_requests"] += 1
        
        # If key exists, move to end
        if key in self.cache:
            self.cache.move_to_end(key)
        
        # Add/update entry
        self.cache[key] = {
            "value": value,
            "timestamp": datetime.now().isoformat(),
            "access_count": self.cache.get(key, {}).get("access_count", 0) + 1
        }
        
        # Evict if over capacity
        if len(self.cache) > self.max_size:
            # Remove least recently used (first item)
            evicted_key, evicted_value = self.cache.popitem(last=False)
            self.stats["evictions"] += 1
            # Persist evicted item to disk
            self._save_to_disk(evicted_key, evicted_value)
    
    def delete(self, key: str) -> bool:
        """
        Delete key from cache and disk
        
        Args:
            key: Cache key to delete
            
        Returns:
            True if key was deleted, False if not found
        """
        deleted = False
        
        # Remove from memory cache
        if key in self.cache:
            del self.cache[key]
            deleted = True
        
        # Remove from disk
        disk_path = self._get_disk_path(key)
        if disk_path.exists():
            disk_path.unlink()
            deleted = True
        
        return deleted
    
    def clear(self):
        """Clear all cache entries from memory and disk"""
        self.cache.clear()
        
        # Clear disk cache
        for cache_file in self.cache_dir.glob("*.cache.json"):
            cache_file.unlink()
        
        # Reset statistics
        self.stats = {
            "hits": 0,
            "misses": 0,
            "evictions": 0,
            "disk_reads": 0,
            "disk_writes": 0,
            "total_requests": 0
        }
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics
        
        Returns:
            Dictionary with cache statistics
        """
        hit_rate = (
            self.stats["hits"] / self.stats["total_requests"]
            if self.stats["total_requests"] > 0 else 0.0
        )
        
        return {
            **self.stats,
            "cache_size": len(self.cache),
            "max_size": self.max_size,
            "hit_rate": hit_rate,
            "utilization": len(self.cache) / self.max_size
        }
    
    def persist_all(self):
        """Manually persist all cache entries to disk"""
        with self._persist_lock:
            for key, entry in self.cache.items():
                self._save_to_disk(key, entry)
            print(f"💾 Persisted {len(self.cache)} cache entries to disk")
    
    def _get_disk_path(self, key: str) -> Path:
        """Get disk path for cache key"""
        # Use hash of key to avoid filesystem issues
        import hashlib
        key_hash = hashlib.md5(key.encode('utf-8')).hexdigest()
        return self.cache_dir / f"{key_hash}.cache.json"
    
    def _save_to_disk(self, key: str, entry: Dict[str, Any]):
        """Save cache entry to disk"""
        try:
            disk_path = self._get_disk_path(key)
            disk_data = {
                "key": key,
                "entry": entry,
                "persisted_at": datetime.now().isoformat()
            }
            with open(disk_path, 'w', encoding='utf-8') as f:
                json.dump(disk_data, f, ensure_ascii=False, indent=2)
            self.stats["disk_writes"] += 1
        except Exception as e:
            print(f"⚠ Failed to save cache entry to disk: {e}")
    
    def _load_from_disk(self, key: str) -> Optional[Any]:
        """Load cache entry from disk"""
        try:
            disk_path = self._get_disk_path(key)
            if disk_path.exists():
                with open(disk_path, 'r', encoding='utf-8') as f:
                    disk_data = json.load(f)
                self.stats["disk_reads"] += 1
                return disk_data["entry"]["value"]
        except Exception as e:
            print(f"⚠ Failed to load cache entry from disk: {e}")
        return None
    
    def _warmup_from_disk(self):
        """Load existing cache entries from disk on startup"""
        print(f"🔥 Warming up cache from disk...")
        loaded = 0
        
        for cache_file in self.cache_dir.glob("*.cache.json"):
            if loaded >= self.max_size:
                break
            
            try:
                with open(cache_file, 'r', encoding='utf-8') as f:
                    disk_data = json.load(f)
                
                key = disk_data["key"]
                entry = disk_data["entry"]
                
                # Add to cache without triggering disk write
                self.cache[key] = entry
                loaded += 1
                self.stats["disk_reads"] += 1
            except Exception as e:
                print(f"⚠ Failed to load cache file {cache_file.name}: {e}")
        
        if loaded > 0:
            print(f"  ✓ Loaded {loaded} cache entries from disk")
        else:
            print(f"  ℹ No cache entries found on disk")
    
    def _start_auto_persist(self):
        """Start background thread for automatic persistence"""
        def persist_worker():
            while not self._stop_persist.is_set():
                # Wait for persist interval or stop event
                if self._stop_persist.wait(timeout=self.persist_interval):
                    break
                
                # Persist cache to disk
                if len(self.cache) > 0:
                    self.persist_all()
        
        self._persist_thread = threading.Thread(target=persist_worker, daemon=True)
        self._persist_thread.start()
        print(f"🔄 Auto-persist enabled (interval: {self.persist_interval}s)")
    
    def shutdown(self):
        """Shutdown cache and persist final state"""
        # Stop auto-persist thread
        if self._persist_thread:
            self._stop_persist.set()
            self._persist_thread.join(timeout=5)
        
        # Final persist
        self.persist_all()
        print("🛑 Cache shutdown complete")
    
    def __del__(self):
        """Destructor - ensure cache is persisted"""
        try:
            if hasattr(self, 'auto_persist') and self.auto_persist:
                self.shutdown()
        except:
            pass


class MemoryCacheDiskMapper:
    """
    Memory Cache Disk Mapper
    記憶快取磁碟映射器
    
    High-level interface for memory caching with disk persistence.
    Integrates with Memory Quick Mount system.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize Memory Cache Disk Mapper
        
        Args:
            config: Configuration dictionary
        """
        if config is None:
            config = {}
        
        # Extract performance settings
        perf_config = config.get("performance", {})
        cache_enabled = perf_config.get("enable_caching", True)
        cache_size = perf_config.get("cache_size", 256)
        
        # Extract cache directory
        cache_dir = config.get("cache_dir", "particle_core/cache")
        
        # Initialize cache
        if cache_enabled:
            self.cache = LRUCache(
                max_size=cache_size,
                cache_dir=cache_dir,
                auto_persist=True,
                persist_interval=30
            )
            self.enabled = True
        else:
            self.cache = None
            self.enabled = False
            print("⚠ Cache disabled in configuration")
    
    def get_state(self, key: str) -> Optional[Any]:
        """
        Get state from cache
        
        Args:
            key: State identifier
            
        Returns:
            Cached state or None
        """
        if not self.enabled:
            return None
        return self.cache.get(key)
    
    def set_state(self, key: str, state: Any):
        """
        Set state in cache
        
        Args:
            key: State identifier
            state: State data to cache
        """
        if not self.enabled:
            return
        self.cache.put(key, state)
    
    def delete_state(self, key: str) -> bool:
        """
        Delete state from cache
        
        Args:
            key: State identifier
            
        Returns:
            True if deleted, False otherwise
        """
        if not self.enabled:
            return False
        return self.cache.delete(key)
    
    def clear_cache(self):
        """Clear all cached states"""
        if self.enabled:
            self.cache.clear()
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics
        
        Returns:
            Cache statistics dictionary
        """
        if not self.enabled:
            return {"enabled": False}
        
        return {
            "enabled": True,
            **self.cache.get_stats()
        }
    
    def persist(self):
        """Manually trigger cache persistence to disk"""
        if self.enabled:
            self.cache.persist_all()
    
    def shutdown(self):
        """Shutdown cache system"""
        if self.enabled:
            self.cache.shutdown()


def main():
    """Demo and test for Memory Cache Disk Mapper"""
    print("=" * 60)
    print("Memory Cache Disk Mapping System Demo")
    print("=" * 60)
    
    # Create mapper with test config
    config = {
        "performance": {
            "enable_caching": True,
            "cache_size": 10
        },
        "cache_dir": "/tmp/test_cache"
    }
    
    mapper = MemoryCacheDiskMapper(config)
    
    # Test cache operations
    print("\n1. Testing cache operations...")
    
    # Put some states
    for i in range(5):
        state = {
            "agent": f"agent_{i}",
            "status": "active",
            "data": f"test_data_{i}"
        }
        mapper.set_state(f"state_{i}", state)
        print(f"  ✓ Cached state_{i}")
    
    # Get states
    print("\n2. Retrieving cached states...")
    for i in range(5):
        state = mapper.get_state(f"state_{i}")
        if state:
            print(f"  ✓ Retrieved state_{i}: {state['agent']}")
    
    # Check statistics
    print("\n3. Cache statistics:")
    stats = mapper.get_cache_stats()
    for key, value in stats.items():
        if isinstance(value, float):
            print(f"  {key}: {value:.2%}" if key in ["hit_rate", "utilization"] else f"  {key}: {value:.2f}")
        else:
            print(f"  {key}: {value}")
    
    # Test cache miss
    print("\n4. Testing cache miss...")
    missing = mapper.get_state("nonexistent")
    print(f"  Result: {missing} (expected None)")
    
    # Persist to disk
    print("\n5. Persisting cache to disk...")
    mapper.persist()
    
    # Show final stats
    print("\n6. Final statistics:")
    stats = mapper.get_cache_stats()
    print(f"  Cache size: {stats['cache_size']}/{stats['max_size']}")
    print(f"  Hit rate: {stats['hit_rate']:.2%}")
    print(f"  Disk writes: {stats['disk_writes']}")
    
    # Shutdown
    print("\n7. Shutting down cache...")
    mapper.shutdown()
    
    print("\n✓ Demo complete!")


if __name__ == "__main__":
    main()
