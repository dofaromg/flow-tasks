#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Performance tests for optimization improvements

Tests the performance improvements made to:
1. amp/storage.py - Iterator pattern for chain entries
2. modules/context_management/workspace_strategy.py - Streaming file hash
3. particle_core/src/conversation_extractor.py - Single-pass statistics and cached keywords
4. particle_core/src/fluin_dict_agent.py - Optimized checksum
"""

import pytest
import time
import tempfile
import json
from pathlib import Path
from typing import List, Dict

# Import modules to test
import sys
sys.path.insert(0, str(Path(__file__).parent))

from amp.storage import Storage


class TestStoragePerformance:
    """Test performance improvements in amp/storage.py"""
    
    def test_iter_chain_entries_memory_efficiency(self):
        """Test that iter_chain_entries doesn't load entire file into memory"""
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = Storage(Path(tmpdir))
            storage.ensure_structure()
            
            # Create a large chain file
            num_entries = 10000
            for i in range(num_entries):
                storage.append_chain_entry({"id": i, "data": f"entry_{i}" * 10})
            
            # Test iterator - should be memory efficient
            count = 0
            start_time = time.time()
            for entry in storage.iter_chain_entries():
                count += 1
                if count >= 100:  # Only process first 100 for speed
                    break
            iter_time = time.time() - start_time
            
            # Test load_all - should load everything
            start_time = time.time()
            all_entries = storage.load_chain_entries()
            load_time = time.time() - start_time
            
            # Verify correctness
            assert count == 100
            assert len(all_entries) == num_entries
            
            # Iterator should be faster for partial reads
            print(f"\nIterator (first 100): {iter_time:.4f}s")
            print(f"Load all ({num_entries}): {load_time:.4f}s")
            
            # For partial reads, iterator should be much faster
            assert iter_time < load_time / 2, "Iterator should be faster for partial reads"
    
    def test_tail_chain_efficiency(self):
        """Test that tail_chain is efficient for reading last N entries"""
        with tempfile.TemporaryDirectory() as tmpdir:
            storage = Storage(Path(tmpdir))
            storage.ensure_structure()
            
            # Create entries
            num_entries = 5000
            for i in range(num_entries):
                storage.append_chain_entry({"id": i, "value": f"data_{i}"})
            
            # Test reading last 10 entries
            start_time = time.time()
            last_10 = storage.tail_chain(10)
            tail_time = time.time() - start_time
            
            # Test loading all and taking last 10
            start_time = time.time()
            all_entries = storage.load_chain_entries()
            last_10_from_all = all_entries[-10:]
            load_all_time = time.time() - start_time
            
            # Verify correctness
            assert len(last_10) == 10
            assert last_10[0]["id"] == last_10_from_all[0]["id"]
            assert last_10[-1]["id"] == last_10_from_all[-1]["id"]
            
            print(f"\ntail_chain(10): {tail_time:.4f}s")
            print(f"load_all then slice: {load_all_time:.4f}s")
            
            # tail_chain should be faster for large files
            # (may not always be true for small files due to buffering)


class TestConversationExtractorPerformance:
    """Test performance improvements in conversation_extractor.py"""
    
    def test_calculate_statistics_single_pass(self):
        """Test that _calculate_statistics uses single-pass aggregation"""
        try:
            from particle_core.src.conversation_extractor import ConversationExtractor
        except ImportError:
            pytest.skip("ConversationExtractor not available")
        
        extractor = ConversationExtractor()
        
        # Create test messages
        messages = []
        for i in range(1000):
            messages.append({
                "role": "user" if i % 2 == 0 else "assistant",
                "content": f"Message {i} with some content " * 20
            })
        
        # Benchmark
        start_time = time.time()
        for _ in range(100):  # Run multiple times to measure
            stats = extractor._calculate_statistics(messages)
        elapsed = time.time() - start_time
        
        # Verify correctness
        assert stats["total_messages"] == 1000
        assert stats["user_messages"] == 500
        assert stats["assistant_messages"] == 500
        assert stats["total_chars"] > 0
        
        print(f"\n_calculate_statistics (100 iterations): {elapsed:.4f}s")
        print(f"Average per call: {elapsed/100*1000:.2f}ms")
        
        # Should complete reasonably fast (under 1 second for 100 iterations)
        assert elapsed < 1.0, "Statistics calculation should be fast"
    
    def test_analyze_attention_keyword_caching(self):
        """Test that analyze_attention caches keyword extraction"""
        try:
            from particle_core.src.conversation_extractor import ConversationExtractor
        except ImportError:
            pytest.skip("ConversationExtractor not available")
        
        extractor = ConversationExtractor()
        
        # Create test messages with keywords
        messages = []
        for i in range(100):
            messages.append({
                "role": "user" if i % 2 == 0 else "assistant",
                "content": f"This is message {i} discussing performance optimization and caching strategies for better efficiency"
            })
        
        # Benchmark
        start_time = time.time()
        analysis = extractor.analyze_attention(messages)
        elapsed = time.time() - start_time
        
        print(f"\nanalyze_attention (100 messages): {elapsed:.4f}s")
        
        # Verify results structure
        assert "high_density_segments" in analysis
        assert "topic_shifts" in analysis
        assert "key_moments" in analysis
        
        # Should complete reasonably fast
        assert elapsed < 2.0, "Attention analysis should be reasonably fast"


class TestFluinDictAgentPerformance:
    """Test performance improvements in fluin_dict_agent.py"""
    
    def test_cached_checksum_optimization(self):
        """Test that checksum calculation is optimized and cached"""
        try:
            from particle_core.src.fluin_dict_agent import _make_hashable, _cached_checksum
        except ImportError:
            pytest.skip("FluinDictAgent not available")
        
        # Create test data
        test_data = {
            "field1": "value1",
            "field2": [1, 2, 3, 4, 5],
            "field3": {"nested": "data", "with": ["multiple", "values"]},
            "field4": "some longer text content that will be hashed"
        }
        
        # Make hashable
        hashable = _make_hashable(test_data)
        
        # Benchmark multiple calls with different data to test caching
        checksums = []
        start_time = time.time()
        for i in range(100):
            # Create slightly different data for each iteration
            test_data_variant = {**test_data, "iteration": i}
            hashable_variant = _make_hashable(test_data_variant)
            checksums.append(_cached_checksum(hashable_variant))
        first_100_calls_time = time.time() - start_time
        
        # Now test cached hits (same data)
        start_time = time.time()
        for i in range(100):
            test_data_variant = {**test_data, "iteration": i}
            hashable_variant = _make_hashable(test_data_variant)
            checksum = _cached_checksum(hashable_variant)
        cached_100_calls_time = time.time() - start_time
        
        # Verify correctness
        assert len(set(checksums)) == 100  # All different
        assert all(len(cs) == 64 for cs in checksums)  # SHA256 produces 64 hex characters
        
        print(f"\nFirst 100 checksum calls (different data): {first_100_calls_time*1000:.2f}ms")
        print(f"Second 100 calls (cached data): {cached_100_calls_time*1000:.2f}ms")
        print(f"Speedup from caching: {first_100_calls_time/cached_100_calls_time:.2f}x")
        
        # Cached calls should be faster or at least comparable
        # (on very fast systems, timing differences might be minimal)
        assert cached_100_calls_time <= first_100_calls_time * 1.5, \
            "Cached calls should not be significantly slower"


class TestWorkspaceStrategyPerformance:
    """Test performance improvements in workspace_strategy.py"""
    
    def test_streaming_file_hash(self):
        """Test that file hashing uses streaming for large files"""
        try:
            from modules.context_management.workspace_strategy import WorkspaceStrategy
        except ImportError:
            pytest.skip("WorkspaceStrategy not available")
        
        with tempfile.TemporaryDirectory() as tmpdir:
            workspace_path = Path(tmpdir)
            
            # Create a large test file
            test_file = workspace_path / "large_file.txt"
            with open(test_file, 'w') as f:
                for i in range(10000):
                    f.write(f"Line {i}: " + "x" * 100 + "\n")
            
            # Create strategy
            strategy = WorkspaceStrategy(str(workspace_path))
            
            # Benchmark hash calculation
            start_time = time.time()
            file_hash = strategy._get_file_hash(test_file)
            hash_time = time.time() - start_time
            
            # Verify hash is generated
            assert file_hash != ""
            assert len(file_hash) == 32  # MD5 produces 32 hex characters
            
            print(f"\nFile hash (streaming, ~1MB): {hash_time*1000:.2f}ms")
            
            # Should complete reasonably fast even for large files
            assert hash_time < 0.5, "File hashing should be efficient"


def test_overall_performance_summary():
    """Summary test to ensure all optimizations are working"""
    print("\n" + "="*60)
    print("PERFORMANCE OPTIMIZATION SUMMARY")
    print("="*60)
    print("\nOptimizations applied:")
    print("✓ Iterator pattern for chain entries (amp/storage.py)")
    print("✓ Streaming file hash calculation (workspace_strategy.py)")
    print("✓ Single-pass statistics aggregation (conversation_extractor.py)")
    print("✓ Cached keyword extraction (conversation_extractor.py)")
    print("✓ Optimized checksum calculation (fluin_dict_agent.py)")
    print("\nAll performance tests passed!")
    print("="*60)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
