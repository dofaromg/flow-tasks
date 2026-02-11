#!/usr/bin/env python3
"""
Tests for enhanced computational capabilities
測試增強的系統演算能力
"""

import sys
import os
import time
import random

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from logic_pipeline import LogicPipeline
from computational_primitives import (
    MatrixOperations,
    StatisticalOperations,
    GraphAlgorithms,
    ParallelComputations,
    TensorOperations,
    compute_statistics
)


def test_logic_pipeline_caching():
    """測試邏輯管線快取功能"""
    print("\n=== 測試邏輯管線快取 ===")
    
    pipeline = LogicPipeline(enable_cache=True)
    
    # First execution
    input_data = "test_data_123"
    result1 = pipeline.run_logic_chain(input_data)
    
    # Second execution (should hit cache)
    result2 = pipeline.run_logic_chain(input_data)
    
    assert result1 == result2, "Results should be identical"
    
    metrics = pipeline.get_metrics()
    print(f"  Cache hits: {metrics['cache_hits']}")
    print(f"  Cache misses: {metrics['cache_misses']}")
    print(f"  Cache hit rate: {metrics['cache_hit_rate']:.2%}")
    
    assert metrics['cache_hits'] >= 1, "Should have cache hits"
    print("  ✅ 快取功能正常")
    
    return True


def test_logic_pipeline_parallel_execution():
    """測試邏輯管線並行執行"""
    print("\n=== 測試邏輯管線並行執行 ===")
    
    pipeline = LogicPipeline(enable_cache=False, max_workers=4)
    
    # Prepare batch data
    batch_size = 100
    input_batch = [f"data_{i}" for i in range(batch_size)]
    
    # Sequential execution
    start_time = time.perf_counter()
    sequential_results = [pipeline.run_logic_chain(data) for data in input_batch]
    sequential_time = time.perf_counter() - start_time
    
    # Clear cache
    pipeline.clear_cache()
    
    # Parallel execution
    start_time = time.perf_counter()
    parallel_results = pipeline.run_logic_chain_parallel(input_batch)
    parallel_time = time.perf_counter() - start_time
    
    print(f"  Sequential: {sequential_time*1000:.2f}ms")
    print(f"  Parallel: {parallel_time*1000:.2f}ms")
    print(f"  Speedup: {sequential_time/parallel_time:.2f}x")
    
    assert sequential_results == parallel_results, "Results should match"
    print("  ✅ 並行執行正確")
    
    return True


def test_batch_simulate():
    """測試批次模擬"""
    print("\n=== 測試批次模擬功能 ===")
    
    pipeline = LogicPipeline(max_workers=4)
    
    input_batch = ["input_1", "input_2", "input_3"]
    results = pipeline.batch_simulate(input_batch, parallel=True)
    
    assert len(results) == len(input_batch), "Should have result for each input"
    
    for i, result in enumerate(results):
        assert result['input'] == input_batch[i], "Input should match"
        assert 'result' in result, "Should have result"
        assert 'steps' in result, "Should have steps"
    
    print(f"  Processed {len(results)} items")
    print("  ✅ 批次模擬功能正常")
    
    return True


def test_matrix_operations():
    """測試矩陣運算"""
    print("\n=== 測試矩陣運算 ===")
    
    mat_ops = MatrixOperations()
    
    # Matrix addition
    a = [[1, 2], [3, 4]]
    b = [[5, 6], [7, 8]]
    result = mat_ops.add(a, b)
    expected = [[6, 8], [10, 12]]
    assert result == expected, f"Addition failed: {result} != {expected}"
    print("  ✅ 矩陣加法")
    
    # Matrix multiplication
    c = [[1, 2], [3, 4]]
    d = [[2, 0], [1, 2]]
    result = mat_ops.multiply(c, d)
    expected = [[4, 4], [10, 8]]
    assert result == expected, f"Multiplication failed: {result} != {expected}"
    print("  ✅ 矩陣乘法")
    
    # Matrix transpose
    e = [[1, 2, 3], [4, 5, 6]]
    result = mat_ops.transpose(e)
    expected = [[1, 4], [2, 5], [3, 6]]
    assert result == expected, f"Transpose failed: {result} != {expected}"
    print("  ✅ 矩陣轉置")
    
    # Dot product
    vec1 = [1, 2, 3]
    vec2 = [4, 5, 6]
    result = mat_ops.dot_product(vec1, vec2)
    expected = 32  # 1*4 + 2*5 + 3*6
    assert result == expected, f"Dot product failed: {result} != {expected}"
    print("  ✅ 向量點積")
    
    # Determinant
    mat = [[1, 2], [3, 4]]
    result = mat_ops.determinant(mat)
    expected = -2  # 1*4 - 2*3
    assert result == expected, f"Determinant failed: {result} != {expected}"
    print("  ✅ 行列式計算")
    
    return True


def test_statistical_operations():
    """測試統計運算"""
    print("\n=== 測試統計運算 ===")
    
    stats = StatisticalOperations()
    
    data = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
    
    # Mean
    mean = stats.mean(data)
    assert abs(mean - 5.5) < 0.01, f"Mean failed: {mean}"
    print(f"  ✅ 平均值: {mean}")
    
    # Median
    median = stats.median(data)
    assert median == 5.5, f"Median failed: {median}"
    print(f"  ✅ 中位數: {median}")
    
    # Standard deviation
    std = stats.std_dev(data)
    print(f"  ✅ 標準差: {std:.2f}")
    
    # Percentile
    p90 = stats.percentile(data, 90)
    print(f"  ✅ 90百分位數: {p90}")
    
    # Correlation
    x = [1, 2, 3, 4, 5]
    y = [2, 4, 6, 8, 10]
    corr = stats.correlation(x, y)
    assert abs(corr - 1.0) < 0.01, f"Correlation should be 1.0: {corr}"
    print(f"  ✅ 相關係數: {corr:.4f}")
    
    # Compute statistics summary
    summary = compute_statistics(data)
    print(f"  ✅ 統計摘要: {len(summary)} 項指標")
    
    return True


def test_graph_algorithms():
    """測試圖算法"""
    print("\n=== 測試圖算法 ===")
    
    graph_algo = GraphAlgorithms()
    
    # Shortest path
    graph = {
        'A': ['B', 'C'],
        'B': ['D'],
        'C': ['D'],
        'D': ['E'],
        'E': []
    }
    path = graph_algo.shortest_path(graph, 'A', 'E')
    assert path == ['A', 'B', 'D', 'E'] or path == ['A', 'C', 'D', 'E'], f"Unexpected path: {path}"
    print(f"  ✅ 最短路徑: {' → '.join(path)}")
    
    # Topological sort
    dag = {
        'A': ['B', 'C'],
        'B': ['D'],
        'C': ['D'],
        'D': []
    }
    topo_order = graph_algo.topological_sort(dag)
    assert topo_order is not None, "Should find topological order"
    print(f"  ✅ 拓撲排序: {' → '.join(topo_order)}")
    
    # Find cycles
    cyclic_graph = {
        'A': ['B'],
        'B': ['C'],
        'C': ['A']
    }
    cycles = graph_algo.find_cycles(cyclic_graph)
    assert len(cycles) > 0, "Should find cycles"
    print(f"  ✅ 循環檢測: 找到 {len(cycles)} 個循環")
    
    return True


def test_parallel_computations():
    """測試並行計算"""
    print("\n=== 測試並行計算 ===")
    
    parallel = ParallelComputations()
    
    # Parallel map
    data = list(range(1000))
    result = parallel.parallel_map(lambda x: x * 2, data, max_workers=4)
    expected = [x * 2 for x in data]
    assert result == expected, "Parallel map failed"
    print("  ✅ 並行映射")
    
    # Parallel filter
    result = parallel.parallel_filter(lambda x: x % 2 == 0, data, max_workers=4)
    expected = [x for x in data if x % 2 == 0]
    assert result == expected, "Parallel filter failed"
    print("  ✅ 並行過濾")
    
    # Parallel reduce
    result = parallel.parallel_reduce(lambda x, y: x + y, data, max_workers=4)
    expected = sum(data)
    assert result == expected, f"Parallel reduce failed: {result} != {expected}"
    print("  ✅ 並行歸約")
    
    return True


def test_tensor_operations():
    """測試張量運算"""
    print("\n=== 測試張量運算 ===")
    
    tensor_ops = TensorOperations()
    
    # Flatten (using public API through reshape)
    data = [[1, 2], [3, 4]]
    # Test reshape which internally uses flatten
    reshaped = tensor_ops.reshape(data, (4,))
    assert reshaped == [1, 2, 3, 4], f"Reshape to 1D failed: {reshaped}"
    print("  ✅ 張量展平 (via reshape)")
    
    # Reshape back
    reshaped = tensor_ops.reshape([1, 2, 3, 4], (2, 2))
    assert reshaped == data, f"Reshape failed: {reshaped}"
    print("  ✅ 張量重塑")
    
    # Element-wise operation
    a = [[1, 2], [3, 4]]
    b = [[5, 6], [7, 8]]
    result = tensor_ops.element_wise_operation(a, b, lambda x, y: x + y)
    expected = [[6, 8], [10, 12]]
    assert result == expected, f"Element-wise operation failed: {result}"
    print("  ✅ 元素級運算")
    
    return True


def test_performance_benchmark():
    """效能基準測試"""
    print("\n=== 效能基準測試 ===")
    
    # Test with different batch sizes
    batch_sizes = [10, 50, 100, 200]
    
    for batch_size in batch_sizes:
        pipeline = LogicPipeline(enable_cache=False, max_workers=4)
        input_batch = [f"data_{i}" for i in range(batch_size)]
        
        # Measure parallel execution time
        start = time.perf_counter()
        results = pipeline.run_logic_chain_parallel(input_batch)
        elapsed = time.perf_counter() - start
        
        throughput = batch_size / elapsed
        print(f"  批次大小 {batch_size:3d}: {elapsed*1000:6.2f}ms ({throughput:7.1f} ops/sec)")
    
    print("  ✅ 效能基準測試完成")
    
    return True


def run_all_tests():
    """執行所有測試"""
    print("\n" + "="*60)
    print("增強系統演算能力測試")
    print("Enhanced Computational Capabilities Tests")
    print("="*60)
    
    tests = [
        ("邏輯管線快取", test_logic_pipeline_caching),
        ("邏輯管線並行執行", test_logic_pipeline_parallel_execution),
        ("批次模擬", test_batch_simulate),
        ("矩陣運算", test_matrix_operations),
        ("統計運算", test_statistical_operations),
        ("圖算法", test_graph_algorithms),
        ("並行計算", test_parallel_computations),
        ("張量運算", test_tensor_operations),
        ("效能基準", test_performance_benchmark),
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        try:
            if test_func():
                passed += 1
        except Exception as e:
            print(f"  ✗ {test_name} 失敗: {e}")
            import traceback
            traceback.print_exc()
            failed += 1
    
    print("\n" + "="*60)
    print(f"測試結果: {passed} 通過, {failed} 失敗")
    print("="*60)
    
    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
