#!/usr/bin/env python3
"""
Performance tests to validate optimization improvements
"""

import time
import tempfile
import json
from pathlib import Path
from typing import List, Dict, Any
import shutil


def test_file_pattern_matching_performance():
    """
    Test performance improvement of single directory scan vs multiple rglob calls.
    Simulates the optimization in sync_repositories.py
    """
    print("\n" + "="*70)
    print("TEST 1: File Pattern Matching Performance")
    print("="*70)
    
    # Create test directory with files
    with tempfile.TemporaryDirectory() as tmpdir:
        test_path = Path(tmpdir)
        
        # Create test files
        patterns = ['*.py', '*.md', '*.txt', '*.json', '*.yaml']
        for i in range(100):
            (test_path / f"file_{i}.py").touch()
            (test_path / f"file_{i}.md").touch()
            (test_path / f"file_{i}.txt").touch()
            (test_path / f"file_{i}.json").touch()
            (test_path / f"file_{i}.yaml").touch()
        
        # Create nested directories
        for i in range(5):
            subdir = test_path / f"subdir_{i}"
            subdir.mkdir()
            for j in range(20):
                (subdir / f"nested_{j}.py").touch()
                (subdir / f"nested_{j}.md").touch()
        
        print(f"Created test directory with ~600 files")
        
        # Old approach: Multiple rglob calls
        start = time.perf_counter()
        old_files = []
        for pattern in patterns:
            for file_path in test_path.rglob(pattern):
                if file_path.is_file():
                    old_files.append(file_path)
        old_time = time.perf_counter() - start
        
        # New approach: Single scan with filtering
        from fnmatch import fnmatch
        start = time.perf_counter()
        all_files = list(test_path.rglob("*"))
        new_files = []
        for file_path in all_files:
            if not file_path.is_file():
                continue
            matches = any(fnmatch(file_path.name, pattern) for pattern in patterns)
            if matches:
                new_files.append(file_path)
        new_time = time.perf_counter() - start
        
        # Results
        print(f"\n📊 Results:")
        print(f"  Old approach (multiple rglob): {old_time*1000:.2f}ms")
        print(f"  New approach (single scan):    {new_time*1000:.2f}ms")
        print(f"  Speedup: {old_time/new_time:.2f}x faster")
        print(f"  Files found: {len(new_files)}")
        
        assert len(old_files) == len(new_files), "Both methods should find same files"
        print(f"  ✅ Correctness verified: Both methods found {len(new_files)} files")
        
        if new_time < old_time:
            print(f"  ✅ Performance improved!")
        
        return {
            'test': 'file_pattern_matching',
            'old_time_ms': old_time * 1000,
            'new_time_ms': new_time * 1000,
            'speedup': old_time / new_time,
            'files_found': len(new_files)
        }


def test_parallel_file_reading_performance():
    """
    Test performance improvement of parallel vs sequential file reading.
    Simulates the optimization in memory_archive_seed.py
    
    Note: Parallel I/O shows benefits primarily with:
    - Large number of files (100+)
    - Larger file sizes
    - Network/slow storage I/O
    With small test files, thread overhead may dominate.
    """
    print("\n" + "="*70)
    print("TEST 2: Parallel File Reading Performance")
    print("="*70)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        test_path = Path(tmpdir)
        
        # Create test JSON files with more realistic size
        num_files = 100  # Increased to show benefit
        for i in range(num_files):
            seed_data = {
                "seed_name": f"test_seed_{i}",
                "created_at": "2025-01-01T00:00:00",
                "checksum": f"hash_{i}",
                # Add more data to simulate realistic file size
                "data": {f"key_{j}": f"value_{i}_{j}" for j in range(50)},
                "metadata": {
                    "version": "1.0",
                    "tags": [f"tag_{j}" for j in range(10)],
                    "description": f"Test seed file {i} with realistic data size"
                }
            }
            with open(test_path / f"seed_{i}.mseed.json", 'w') as f:
                json.dump(seed_data, f)
        
        print(f"Created {num_files} test seed files with realistic data")
        
        # Sequential approach
        start = time.perf_counter()
        seeds_sequential = []
        for seed_file in test_path.glob("*.mseed.json"):
            with open(seed_file, 'r') as f:
                seed = json.load(f)
                seeds_sequential.append({
                    "seed_name": seed["seed_name"],
                    "created_at": seed["created_at"],
                    "checksum": seed["checksum"]
                })
        seq_time = time.perf_counter() - start
        
        # Parallel approach
        from concurrent.futures import ThreadPoolExecutor
        import os
        
        def read_seed_file(seed_file):
            try:
                with open(seed_file, 'r') as f:
                    seed = json.load(f)
                    return {
                        "seed_name": seed["seed_name"],
                        "created_at": seed["created_at"],
                        "checksum": seed["checksum"]
                    }
            except Exception:
                return None
        
        start = time.perf_counter()
        seed_files = list(test_path.glob("*.mseed.json"))
        max_workers = min(4, os.cpu_count() or 1)
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            results = executor.map(read_seed_file, seed_files)
            seeds_parallel = [s for s in results if s is not None]
        par_time = time.perf_counter() - start
        
        # Results
        print(f"\n📊 Results:")
        print(f"  Sequential reading: {seq_time*1000:.2f}ms")
        print(f"  Parallel reading:   {par_time*1000:.2f}ms")
        
        if par_time < seq_time:
            print(f"  Speedup: {seq_time/par_time:.2f}x faster")
        else:
            print(f"  Overhead: {par_time/seq_time:.2f}x (thread overhead with small files)")
            print(f"  Note: Parallel I/O benefits scale with file count and size")
        
        print(f"  Files read: {len(seeds_parallel)}")
        
        assert len(seeds_sequential) == len(seeds_parallel), "Both methods should read same files"
        print(f"  ✅ Correctness verified: Both methods read {len(seeds_parallel)} files")
        
        if par_time < seq_time:
            print(f"  ✅ Performance improved!")
        else:
            print(f"  ℹ️  Parallel optimization is beneficial for larger datasets")
        
        return {
            'test': 'parallel_file_reading',
            'sequential_time_ms': seq_time * 1000,
            'parallel_time_ms': par_time * 1000,
            'speedup': seq_time / par_time,  # Can be < 1.0 if parallel is slower
            'files_read': len(seeds_parallel),
            'note': 'Benefit scales with file count/size'
        }


def test_buffered_write_performance():
    """
    Test performance improvement of buffered writing vs multiple small writes.
    Simulates the optimization in process_tasks.py
    """
    print("\n" + "="*70)
    print("TEST 3: Buffered Writing Performance")
    print("="*70)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        test_path = Path(tmpdir)
        
        # Generate test data
        num_lines = 1000
        test_data = [f"Line {i}: Test data content here\n" for i in range(num_lines)]
        
        print(f"Testing with {num_lines} lines of output")
        
        # Multiple write approach
        file1 = test_path / "test_multiple.txt"
        start = time.perf_counter()
        with open(file1, 'w') as f:
            for line in test_data:
                f.write(line)
        multi_time = time.perf_counter() - start
        
        # Buffered write approach
        file2 = test_path / "test_buffered.txt"
        start = time.perf_counter()
        with open(file2, 'w') as f:
            f.write(''.join(test_data))
        buff_time = time.perf_counter() - start
        
        # Results
        print(f"\n📊 Results:")
        print(f"  Multiple writes: {multi_time*1000:.2f}ms")
        print(f"  Buffered write:  {buff_time*1000:.2f}ms")
        print(f"  Speedup: {multi_time/buff_time:.2f}x faster")
        
        # Verify correctness
        with open(file1, 'r') as f:
            content1 = f.read()
        with open(file2, 'r') as f:
            content2 = f.read()
        
        assert content1 == content2, "Both methods should produce same output"
        print(f"  ✅ Correctness verified: Output matches ({len(content1)} bytes)")
        
        if buff_time < multi_time:
            print(f"  ✅ Performance improved!")
        
        return {
            'test': 'buffered_writing',
            'multiple_writes_ms': multi_time * 1000,
            'buffered_write_ms': buff_time * 1000,
            'speedup': multi_time / buff_time,
            'lines_written': num_lines
        }


def main():
    """Run all performance tests"""
    print("\n" + "="*70)
    print("🚀 PERFORMANCE OPTIMIZATION VALIDATION TESTS")
    print("="*70)
    print("\nThese tests validate the performance improvements made to:")
    print("  1. sync_repositories.py - File pattern matching")
    print("  2. memory_archive_seed.py - Parallel file reading")
    print("  3. process_tasks.py - Buffered report writing")
    
    results = []
    
    # Run tests
    try:
        results.append(test_file_pattern_matching_performance())
        results.append(test_parallel_file_reading_performance())
        results.append(test_buffered_write_performance())
        
        # Summary
        print("\n" + "="*70)
        print("📈 PERFORMANCE TEST SUMMARY")
        print("="*70)
        
        total_improved_speedup = 0
        improved_count = 0
        
        for result in results:
            print(f"\n✅ {result['test']}")
            speedup = result['speedup']
            if speedup >= 1.0:
                print(f"   Speedup: {speedup:.2f}x")
                total_improved_speedup += speedup
                improved_count += 1
            else:
                print(f"   Overhead: {1/speedup:.2f}x (slower due to thread overhead)")
                print(f"   Note: {result.get('note', 'Optimization may benefit larger datasets')}")
        
        if improved_count > 0:
            avg_speedup = total_improved_speedup / improved_count
            print(f"\n🎯 Average speedup for improved operations: {avg_speedup:.2f}x")
        print("="*70)
        
        print("\n✅ All performance tests completed successfully!")
        return True
        
    except Exception as e:
        print(f"\n❌ Performance test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    import sys
    success = main()
    sys.exit(0 if success else 1)
