#!/usr/bin/env python3
"""
Performance Benchmark Script
Run this before and after optimizations to measure improvements

Usage:
    python scripts/benchmark_performance.py
    
This script benchmarks:
1. Logic pipeline execution
2. Checksum generation with caching
3. Parallel file reading
4. Task processing
"""

import time
import sys
import tempfile
import shutil
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from particle_core.src.logic_pipeline import LogicPipeline
from particle_core.src.rebuild_fn import FunctionRestorer
from particle_core.src.memory_archive_seed import MemoryArchiveSeed

# Try to import rag_index (optional, requires sklearn)
try:
    from rag_index import read_files, build_index
    HAS_RAG_INDEX = True
except ImportError:
    HAS_RAG_INDEX = False
    print("Note: rag_index benchmarks skipped (sklearn not installed)")


def benchmark_logic_pipeline(iterations: int = 1000):
    """Benchmark logic pipeline execution."""
    print(f"\n{'='*60}")
    print("Benchmarking Logic Pipeline")
    print(f"{'='*60}")
    
    pipeline = LogicPipeline()
    
    # Warm-up
    for _ in range(10):
        pipeline.simulate("Warm-up")
    
    start = time.perf_counter()
    for i in range(iterations):
        pipeline.simulate(f"Test input {i}")
    end = time.perf_counter()
    
    elapsed = end - start
    ops_per_sec = iterations / elapsed
    avg_ms = (elapsed / iterations) * 1000
    
    print(f"  Iterations: {iterations}")
    print(f"  Total time: {elapsed:.3f}s")
    print(f"  Average: {avg_ms:.3f}ms per operation")
    print(f"  Throughput: {ops_per_sec:.0f} operations/second")


def benchmark_function_restorer(iterations: int = 1000):
    """Benchmark function restoration."""
    print(f"\n{'='*60}")
    print("Benchmarking Function Restorer")
    print(f"{'='*60}")
    
    restorer = FunctionRestorer()
    test_compressed = "SEED(X) = STORE(RECURSE(FLOW(MARK(STRUCTURE(X)))))"
    
    # Warm-up
    for _ in range(10):
        restorer.decompress_fn(test_compressed)
    
    start = time.perf_counter()
    for _ in range(iterations):
        steps = restorer.decompress_fn(test_compressed)
        compressed = restorer.compress_fn(steps)
    end = time.perf_counter()
    
    elapsed = end - start
    ops_per_sec = iterations / elapsed
    avg_ms = (elapsed / iterations) * 1000
    
    print(f"  Iterations: {iterations}")
    print(f"  Total time: {elapsed:.3f}s")
    print(f"  Average: {avg_ms:.3f}ms per operation")
    print(f"  Throughput: {ops_per_sec:.0f} operations/second")


def benchmark_checksum(iterations: int = 100):
    """Benchmark checksum generation with caching."""
    print(f"\n{'='*60}")
    print("Benchmarking Checksum Generation (with caching)")
    print(f"{'='*60}")
    
    archive = MemoryArchiveSeed()
    
    # Create different test data to test cache effectiveness
    test_data_samples = [
        {"text": f"Test data {i}", "numbers": list(range(100)), "nested": {"key": f"value{i}"}}
        for i in range(10)
    ]
    
    # Test with cache misses (different data each time)
    start = time.perf_counter()
    for i in range(iterations):
        archive._generate_checksum(test_data_samples[i % len(test_data_samples)])
    end = time.perf_counter()
    
    elapsed_varied = end - start
    ops_per_sec_varied = iterations / elapsed_varied
    avg_ms_varied = (elapsed_varied / iterations) * 1000
    
    # Test with cache hits (same data repeated)
    same_data = test_data_samples[0]
    start = time.perf_counter()
    for _ in range(iterations):
        archive._generate_checksum(same_data)
    end = time.perf_counter()
    
    elapsed_same = end - start
    ops_per_sec_same = iterations / elapsed_same
    avg_ms_same = (elapsed_same / iterations) * 1000
    
    print(f"  Varied data (cache misses):")
    print(f"    Iterations: {iterations}")
    print(f"    Total time: {elapsed_varied:.3f}s")
    print(f"    Average: {avg_ms_varied:.3f}ms per operation")
    print(f"    Throughput: {ops_per_sec_varied:.0f} operations/second")
    
    print(f"\n  Same data (cache hits):")
    print(f"    Iterations: {iterations}")
    print(f"    Total time: {elapsed_same:.3f}s")
    print(f"    Average: {avg_ms_same:.3f}ms per operation")
    print(f"    Throughput: {ops_per_sec_same:.0f} operations/second")
    
    if elapsed_varied > 0:
        speedup = elapsed_varied / elapsed_same
        print(f"\n  Cache speedup: {speedup:.1f}x")


def benchmark_file_reading():
    """Benchmark file reading with parallel I/O."""
    if not HAS_RAG_INDEX:
        print(f"\n{'='*60}")
        print("Benchmarking Parallel File Reading - SKIPPED")
        print("  (sklearn not installed)")
        print(f"{'='*60}")
        return
    
    print(f"\n{'='*60}")
    print("Benchmarking Parallel File Reading")
    print(f"{'='*60}")
    
    # Create temp directory with test files
    temp_dir = Path(tempfile.mkdtemp())
    try:
        # Create 100 test files with varying sizes
        file_count = 100
        print(f"  Creating {file_count} test files...")
        
        for i in range(file_count):
            content = f"# Test file {i}\n" + ("# Content line\n" * (100 + i % 50))
            (temp_dir / f"test_{i}.py").write_text(content)
        
        # Benchmark file reading
        print(f"  Reading files with parallel I/O...")
        start = time.perf_counter()
        documents, paths = read_files(temp_dir)
        end = time.perf_counter()
        
        elapsed = end - start
        files_per_sec = len(paths) / elapsed
        avg_ms = (elapsed / len(paths)) * 1000
        
        total_size = sum(len(doc) for doc in documents)
        throughput_mb = (total_size / (1024 * 1024)) / elapsed
        
        print(f"  Files read: {len(paths)}")
        print(f"  Total size: {total_size / 1024:.1f} KB")
        print(f"  Total time: {elapsed:.3f}s")
        print(f"  Average: {avg_ms:.3f}ms per file")
        print(f"  Throughput: {files_per_sec:.0f} files/second")
        print(f"  Data rate: {throughput_mb:.2f} MB/second")
    
    finally:
        shutil.rmtree(temp_dir)


def benchmark_memory_seed_operations(iterations: int = 100):
    """Benchmark memory seed create/restore operations."""
    print(f"\n{'='*60}")
    print("Benchmarking Memory Seed Operations")
    print(f"{'='*60}")
    
    # Create temp directory for seeds
    temp_dir = Path(tempfile.mkdtemp())
    try:
        archive = MemoryArchiveSeed(storage_path=str(temp_dir))
        
        test_data = {
            "text": "Test memory seed data",
            "logic_chain": ["structure", "mark", "flow", "recurse", "store"],
            "metadata": {"author": "Benchmark", "type": "test"}
        }
        
        # Benchmark seed creation
        start = time.perf_counter()
        seed_names = []
        for i in range(iterations):
            result = archive.create_seed(
                particle_data=test_data,
                seed_name=f"bench_seed_{i}"
            )
            seed_names.append(result['seed_name'])
        end = time.perf_counter()
        
        elapsed_create = end - start
        ops_per_sec_create = iterations / elapsed_create
        avg_ms_create = (elapsed_create / iterations) * 1000
        
        print(f"  Create Operations:")
        print(f"    Iterations: {iterations}")
        print(f"    Total time: {elapsed_create:.3f}s")
        print(f"    Average: {avg_ms_create:.3f}ms per operation")
        print(f"    Throughput: {ops_per_sec_create:.0f} operations/second")
        
        # Benchmark seed restoration
        start = time.perf_counter()
        for seed_name in seed_names:
            archive.restore_seed(seed_name)
        end = time.perf_counter()
        
        elapsed_restore = end - start
        ops_per_sec_restore = iterations / elapsed_restore
        avg_ms_restore = (elapsed_restore / iterations) * 1000
        
        print(f"\n  Restore Operations:")
        print(f"    Iterations: {iterations}")
        print(f"    Total time: {elapsed_restore:.3f}s")
        print(f"    Average: {avg_ms_restore:.3f}ms per operation")
        print(f"    Throughput: {ops_per_sec_restore:.0f} operations/second")
    
    finally:
        shutil.rmtree(temp_dir)


def main():
    """Run all benchmarks."""
    print("\n" + "="*60)
    print("Performance Benchmark Suite")
    print("="*60)
    print("\nThis benchmark measures the performance of key operations")
    print("in the flow-tasks repository after optimizations.")
    print("\nNote: Results may vary based on system performance.")
    
    try:
        # Run all benchmarks
        benchmark_logic_pipeline(iterations=1000)
        benchmark_function_restorer(iterations=1000)
        benchmark_checksum(iterations=100)
        benchmark_file_reading()
        benchmark_memory_seed_operations(iterations=100)
        
        print("\n" + "="*60)
        print("All Benchmarks Complete!")
        print("="*60)
        print("\nResults show the performance of optimized implementations:")
        print("  ✓ Parallel file I/O (ThreadPoolExecutor)")
        print("  ✓ Checksum caching (LRU cache)")
        print("  ✓ Bounded memory traces (deque)")
        print("  ✓ Efficient glob patterns")
        print("\n")
        
    except Exception as e:
        print(f"\n❌ Benchmark failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
