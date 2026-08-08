#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test suite for Memory Cache Disk Mapping System
記憶快取磁碟映射系統測試套件
"""

import sys
import json
import time
import tempfile
from pathlib import Path

# Add memory module to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src' / 'memory'))

from memory_cache_disk import LRUCache, MemoryCacheDiskMapper


def test_lru_basic_operations():
    """Test basic LRU cache operations"""
    print("\n" + "=" * 60)
    print("Test 1: Basic LRU Operations")
    print("=" * 60)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        cache = LRUCache(max_size=3, cache_dir=tmpdir, auto_persist=False)
        
        # Test put and get
        cache.put("key1", "value1")
        cache.put("key2", "value2")
        cache.put("key3", "value3")
        
        # Verify all keys are in cache (without accessing them, so order is preserved)
        assert len(cache.cache) == 3, "Cache should have 3 entries"
        
        print("  ✓ Put operations work correctly")
        
        # Now access key1 to verify get works (this moves it to end)
        assert cache.get("key1") == "value1", "Failed to retrieve key1"
        
        print("  ✓ Get operations work correctly")
        
        # Test LRU eviction
        # Order is now: key2 (oldest), key3, key1 (most recent due to get)
        cache.put("key4", "value4")  # Should evict key2 (least recently used)
        
        # key2 should be evicted from memory but saved to disk
        # When we try to get it, it will be loaded from disk and added back to cache
        assert "key2" not in cache.cache, "key2 should be evicted from memory cache"
        
        # But it should still be retrievable from disk
        value2 = cache.get("key2")
        assert value2 == "value2", "key2 should be loadable from disk"
        
        # Now key2 is back in memory cache (loaded from disk)
        assert "key2" in cache.cache, "key2 should be back in memory after disk load"
        
        print("  ✓ LRU eviction works correctly")
        
        # Check stats
        stats = cache.get_stats()
        assert stats["cache_size"] == 3, "Cache size should be 3"
        assert stats["evictions"] >= 1, "Should have at least 1 eviction"
        
        print(f"  ✓ Statistics: {stats['cache_size']} entries, {stats['evictions']} evictions")
        
    print("✓✓✓ Test 1 PASSED ✓✓✓")
    return True


def test_disk_persistence():
    """Test disk persistence functionality"""
    print("\n" + "=" * 60)
    print("Test 2: Disk Persistence")
    print("=" * 60)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create cache and add data
        cache1 = LRUCache(max_size=5, cache_dir=tmpdir, auto_persist=False)
        
        for i in range(5):
            cache1.put(f"key{i}", f"value{i}")
        
        # Manually persist
        cache1.persist_all()
        print(f"  ✓ Persisted 5 entries to disk")
        
        # Check disk files
        cache_files = list(Path(tmpdir).glob("*.cache.json"))
        assert len(cache_files) == 5, f"Should have 5 cache files, got {len(cache_files)}"
        print(f"  ✓ Found {len(cache_files)} cache files on disk")
        
        # Create new cache and warmup
        cache2 = LRUCache(max_size=10, cache_dir=tmpdir, auto_persist=False)
        
        # Verify warmup loaded data
        assert cache2.get("key0") == "value0", "Warmup failed for key0"
        assert cache2.get("key4") == "value4", "Warmup failed for key4"
        
        stats = cache2.get_stats()
        assert stats["cache_size"] == 5, "Should have loaded 5 entries"
        assert stats["disk_reads"] >= 5, "Should have read from disk"
        
        print(f"  ✓ Warmup loaded {stats['cache_size']} entries from disk")
        print(f"  ✓ Disk reads: {stats['disk_reads']}")
        
    print("✓✓✓ Test 2 PASSED ✓✓✓")
    return True


def test_cache_hit_rate():
    """Test cache hit rate tracking"""
    print("\n" + "=" * 60)
    print("Test 3: Cache Hit Rate")
    print("=" * 60)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        cache = LRUCache(max_size=3, cache_dir=tmpdir, auto_persist=False)
        
        # Add some data
        cache.put("a", 1)
        cache.put("b", 2)
        cache.put("c", 3)
        
        # Generate some hits
        cache.get("a")
        cache.get("a")
        cache.get("b")
        
        # Generate some misses
        cache.get("d")
        cache.get("e")
        
        stats = cache.get_stats()
        
        # 3 puts + 5 gets = 8 total requests
        # 3 hits (a, a, b), 2 misses (d, e)
        assert stats["total_requests"] == 8, f"Total requests should be 8, got {stats['total_requests']}"
        assert stats["hits"] == 3, f"Hits should be 3, got {stats['hits']}"
        assert stats["misses"] == 2, f"Misses should be 2, got {stats['misses']}"
        
        hit_rate = stats["hit_rate"]
        expected_rate = 3 / 8  # 37.5%
        
        print(f"  ✓ Total requests: {stats['total_requests']}")
        print(f"  ✓ Hits: {stats['hits']}")
        print(f"  ✓ Misses: {stats['misses']}")
        print(f"  ✓ Hit rate: {hit_rate:.2%} (expected: {expected_rate:.2%})")
        
        assert abs(hit_rate - expected_rate) < 0.01, "Hit rate calculation incorrect"
        
    print("✓✓✓ Test 3 PASSED ✓✓✓")
    return True


def test_cache_mapper_integration():
    """Test MemoryCacheDiskMapper integration"""
    print("\n" + "=" * 60)
    print("Test 4: Cache Mapper Integration")
    print("=" * 60)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        config = {
            "performance": {
                "enable_caching": True,
                "cache_size": 5
            },
            "cache_dir": tmpdir
        }
        
        mapper = MemoryCacheDiskMapper(config)
        
        # Test state operations
        states = {
            "agent_1": {"status": "active", "data": "test1"},
            "agent_2": {"status": "idle", "data": "test2"},
            "agent_3": {"status": "processing", "data": "test3"}
        }
        
        # Set states
        for key, state in states.items():
            mapper.set_state(key, state)
        
        print(f"  ✓ Set {len(states)} states")
        
        # Get states
        for key, expected_state in states.items():
            retrieved = mapper.get_state(key)
            assert retrieved is not None, f"Failed to retrieve {key}"
            assert retrieved["status"] == expected_state["status"], f"State mismatch for {key}"
        
        print(f"  ✓ Retrieved all {len(states)} states correctly")
        
        # Check stats
        stats = mapper.get_cache_stats()
        assert stats["enabled"], "Cache should be enabled"
        assert stats["cache_size"] == 3, f"Cache size should be 3, got {stats['cache_size']}"
        
        print(f"  ✓ Cache stats: {stats['cache_size']} entries, hit rate: {stats['hit_rate']:.2%}")
        
        # Test delete
        deleted = mapper.delete_state("agent_1")
        assert deleted, "Failed to delete state"
        assert mapper.get_state("agent_1") is None, "State should be deleted"
        
        print("  ✓ State deletion works correctly")
        
        # Shutdown
        mapper.shutdown()
        print("  ✓ Shutdown completed")
        
    print("✓✓✓ Test 4 PASSED ✓✓✓")
    return True


def test_memory_quick_mount_cache_integration():
    """Test MemoryQuickMounter with cache integration"""
    print("\n" + "=" * 60)
    print("Test 5: MemoryQuickMounter Cache Integration")
    print("=" * 60)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create config
        config_path = Path(tmpdir) / "config.json"
        config = {
            "context_dir": str(Path(tmpdir) / "context"),
            "snapshot_dir": str(Path(tmpdir) / "snapshots"),
            "cache_dir": str(Path(tmpdir) / "cache"),
            "performance": {
                "enable_caching": True,
                "cache_size": 10
            }
        }
        
        with open(config_path, 'w') as f:
            json.dump(config, f)
        
        # Import and test
        from memory_quick_mount import MemoryQuickMounter
        
        mqm = MemoryQuickMounter(str(config_path))
        
        # Test cached state operations
        state = {"scene": "room_a", "objects": ["table", "chair"], "temp": 22.5}
        
        mqm.set_cached_state("test_agent", state)
        print("  ✓ Set cached state")
        
        retrieved = mqm.get_cached_state("test_agent")
        assert retrieved is not None, "Failed to retrieve cached state"
        assert retrieved["scene"] == "room_a", "State mismatch"
        
        print("  ✓ Retrieved cached state correctly")
        
        # Test snapshot with cache
        snapshot_path = mqm.snapshot_with_cache("test_agent", state)
        assert Path(snapshot_path).exists(), "Snapshot file should exist"
        
        print(f"  ✓ Created snapshot with cache: {Path(snapshot_path).name}")
        
        # Test cache stats
        cache_stats = mqm.get_cache_stats()
        assert cache_stats["enabled"], "Cache should be enabled"
        assert cache_stats["cache_size"] > 0, "Cache should have entries"
        
        print(f"  ✓ Cache stats: {cache_stats['cache_size']} entries, hit rate: {cache_stats['hit_rate']:.2%}")
        
        # Shutdown
        mqm.shutdown()
        print("  ✓ Shutdown completed")
        
    print("✓✓✓ Test 5 PASSED ✓✓✓")
    return True


def run_all_tests():
    """Run all cache system tests"""
    print("\n")
    print("╔" + "=" * 58 + "╗")
    print("║" + " " * 10 + "Memory Cache Disk Test Suite" + " " * 20 + "║")
    print("╚" + "=" * 58 + "╝")
    
    tests = [
        ("Basic LRU Operations", test_lru_basic_operations),
        ("Disk Persistence", test_disk_persistence),
        ("Cache Hit Rate", test_cache_hit_rate),
        ("Cache Mapper Integration", test_cache_mapper_integration),
        ("MemoryQuickMounter Integration", test_memory_quick_mount_cache_integration)
    ]
    
    passed = 0
    failed = 0
    
    for name, test_func in tests:
        try:
            if test_func():
                passed += 1
            else:
                failed += 1
                print(f"\n✗ {name} FAILED")
        except Exception as e:
            failed += 1
            print(f"\n✗ {name} FAILED with exception:")
            print(f"  {type(e).__name__}: {e}")
            import traceback
            traceback.print_exc()
    
    # Summary
    print("\n")
    print("=" * 60)
    print("Test Summary")
    print("=" * 60)
    print(f"Total tests: {len(tests)}")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    
    if failed == 0:
        print("\n✓✓✓ ALL TESTS PASSED ✓✓✓")
        return 0
    else:
        print(f"\n✗✗✗ {failed} TEST(S) FAILED ✗✗✗")
        return 1


if __name__ == "__main__":
    exit_code = run_all_tests()
    sys.exit(exit_code)
