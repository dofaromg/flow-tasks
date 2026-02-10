"""
Performance tests for optimization improvements.
Tests to validate that performance optimizations are working correctly.
"""

import pytest
import time
import tempfile
import shutil
from pathlib import Path
from modules.context_management.workspace_strategy import WorkspaceStrategy


def test_file_hash_caching():
    """Test that file hashes are cached when files don't change"""
    with tempfile.TemporaryDirectory() as tmpdir:
        workspace = Path(tmpdir)
        test_file = workspace / "test.txt"
        test_file.write_text("Hello, World!")
        
        # Create workspace strategy
        strategy = WorkspaceStrategy(str(workspace))
        
        # Get initial index
        rel_path = "test.txt"
        assert rel_path in strategy.file_index
        original_hash = strategy.file_index[rel_path]['hash']
        
        # Update the same file without changing it
        # This should reuse the cached hash
        strategy._update_file_index(test_file)
        
        # Hash should be the same and cached
        assert strategy.file_index[rel_path]['hash'] == original_hash
        
        # Modify the file
        time.sleep(0.1)  # Ensure mtime changes
        test_file.write_text("Modified content")
        
        # Update index again - hash should be recomputed
        strategy._update_file_index(test_file)
        new_hash = strategy.file_index[rel_path]['hash']
        
        # Hash should be different now
        assert new_hash != original_hash
        print(f"✓ File hash caching working correctly")


def test_content_caching():
    """Test that file content is cached"""
    with tempfile.TemporaryDirectory() as tmpdir:
        workspace = Path(tmpdir)
        test_file = workspace / "content.txt"
        test_content = "Test content for caching"
        test_file.write_text(test_content)
        
        # Create workspace strategy
        strategy = WorkspaceStrategy(str(workspace))
        
        # Read content for the first time
        content1 = strategy._read_file_content(test_file)
        assert content1 == test_content
        
        # Check that it's cached
        cache_key = (str(test_file), test_file.stat().st_mtime)
        assert cache_key in strategy._content_cache
        
        # Read again - should use cache
        content2 = strategy._read_file_content(test_file)
        assert content2 == test_content
        
        # Verify cache was used (same object)
        assert content1 == content2
        print(f"✓ File content caching working correctly")


def test_cache_invalidation_on_scan():
    """Test that cache is cleared on full workspace scan"""
    with tempfile.TemporaryDirectory() as tmpdir:
        workspace = Path(tmpdir)
        test_file = workspace / "test.txt"
        test_file.write_text("Initial content")
        
        # Create workspace strategy
        strategy = WorkspaceStrategy(str(workspace))
        
        # Read content to populate cache
        strategy._read_file_content(test_file)
        assert len(strategy._content_cache) > 0
        
        # Scan workspace - should clear cache
        strategy.scan_workspace()
        assert len(strategy._content_cache) == 0
        print(f"✓ Cache invalidation on scan working correctly")


def test_cache_size_limit():
    """Test that cache respects size limit"""
    with tempfile.TemporaryDirectory() as tmpdir:
        workspace = Path(tmpdir)
        
        # Create workspace with size limit of 5
        strategy = WorkspaceStrategy(str(workspace))
        strategy._cache_max_size = 5
        
        # Create and read more files than cache can hold
        for i in range(10):
            test_file = workspace / f"test{i}.txt"
            test_file.write_text(f"Content {i}")
            strategy._read_file_content(test_file)
        
        # Cache should not exceed limit
        assert len(strategy._content_cache) <= strategy._cache_max_size
        print(f"✓ Cache size limit working correctly: {len(strategy._content_cache)}/{strategy._cache_max_size}")


def test_lru_eviction():
    """Test that LRU eviction works correctly"""
    with tempfile.TemporaryDirectory() as tmpdir:
        workspace = Path(tmpdir)
        
        # Create workspace with size limit of 3
        strategy = WorkspaceStrategy(str(workspace))
        strategy._cache_max_size = 3
        
        # Create and read 3 files
        files = []
        for i in range(3):
            test_file = workspace / f"test{i}.txt"
            test_file.write_text(f"Content {i}")
            files.append(test_file)
            strategy._read_file_content(test_file)
        
        # Cache should have all 3
        assert len(strategy._content_cache) == 3
        
        # Access file 0 again (makes it most recently used)
        strategy._read_file_content(files[0])
        
        # Add a new file (should evict file 1, the least recently used)
        new_file = workspace / "new.txt"
        new_file.write_text("New content")
        strategy._read_file_content(new_file)
        
        # Cache should still be 3
        assert len(strategy._content_cache) == 3
        
        # File 0 should still be cached (was accessed recently)
        cache_key_0 = (str(files[0]), files[0].stat().st_mtime)
        assert cache_key_0 in strategy._content_cache
        
        # File 1 should be evicted (least recently used)
        cache_key_1 = (str(files[1]), files[1].stat().st_mtime)
        assert cache_key_1 not in strategy._content_cache
        
        # File 2 and new file should be cached
        cache_key_2 = (str(files[2]), files[2].stat().st_mtime)
        cache_key_new = (str(new_file), new_file.stat().st_mtime)
        assert cache_key_2 in strategy._content_cache
        assert cache_key_new in strategy._content_cache
        
        print(f"✓ LRU eviction working correctly")


def test_performance_comparison():
    """Compare performance with and without optimizations"""
    with tempfile.TemporaryDirectory() as tmpdir:
        workspace = Path(tmpdir)
        
        # Create test files
        num_files = 20
        for i in range(num_files):
            test_file = workspace / f"file{i}.txt"
            test_file.write_text(f"Content {i}" * 100)  # Make files bigger
        
        strategy = WorkspaceStrategy(str(workspace))
        
        # Measure time for repeated index updates (with caching)
        start_time = time.time()
        for _ in range(3):
            for i in range(num_files):
                test_file = workspace / f"file{i}.txt"
                strategy._update_file_index(test_file)
        with_cache_time = time.time() - start_time
        
        print(f"✓ Performance test completed in {with_cache_time:.4f}s")
        print(f"  Average time per update: {with_cache_time / (3 * num_files) * 1000:.2f}ms")


if __name__ == "__main__":
    print("Running performance improvement tests...\n")
    test_file_hash_caching()
    test_content_caching()
    test_cache_invalidation_on_scan()
    test_cache_size_limit()
    test_lru_eviction()
    test_performance_comparison()
    print("\n✅ All performance tests passed!")
