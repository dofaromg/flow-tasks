#!/usr/bin/env python3
"""
Performance Benchmark for Context Management Strategies
上下文管理策略效能基準測試
"""

import time
from datetime import datetime
from typing import List, Dict, Any
import tempfile
import shutil
from pathlib import Path

from modules.context_management import (
    ContextItem,
    WorkspaceStrategy,
    SlidingWindowStrategy,
    SummaryStrategy,
    RAGStrategy,
    HybridStrategy
)


def create_test_items(count: int, content_length: int = 100) -> List[ContextItem]:
    """Create test context items"""
    items = []
    for i in range(count):
        content = f"Test content item {i}. " * (content_length // 20)
        items.append(ContextItem(
            id=f"item-{i}",
            content=content,
            metadata={"index": i, "category": f"cat-{i % 10}"},
            timestamp=datetime.now(),
            priority=i % 10
        ))
    return items


def benchmark_strategy(strategy, items: List[ContextItem], name: str) -> Dict[str, Any]:
    """Benchmark a single strategy"""
    print(f"\n{'='*60}")
    print(f"Testing {name}")
    print(f"{'='*60}")
    
    # Test add
    start = time.time()
    for item in items:
        strategy.add(item)
    add_time = time.time() - start
    
    # Test retrieve without query
    start = time.time()
    results = strategy.retrieve(limit=10)
    retrieve_simple_time = time.time() - start
    
    # Test retrieve with query
    start = time.time()
    results = strategy.retrieve(query="test content", limit=10)
    retrieve_query_time = time.time() - start
    
    # Test compress
    start = time.time()
    compressed = strategy.compress()
    compress_time = time.time() - start
    
    results = {
        "name": name,
        "items_count": len(items),
        "add_time": add_time,
        "retrieve_simple_time": retrieve_simple_time,
        "retrieve_query_time": retrieve_query_time,
        "compress_time": compress_time,
        "items_per_second": len(items) / add_time if add_time > 0 else 0,
        "final_item_count": len(strategy.context_items),
        "compression_ratio": len(strategy.context_items) / len(items) if items else 1.0
    }
    
    # Print results
    print(f"Add time: {add_time:.4f}s ({results['items_per_second']:.0f} items/s)")
    print(f"Retrieve (simple): {retrieve_simple_time:.4f}s")
    print(f"Retrieve (query): {retrieve_query_time:.4f}s")
    print(f"Compress time: {compress_time:.4f}s")
    print(f"Final items: {results['final_item_count']} (ratio: {results['compression_ratio']:.2%})")
    
    return results


def run_benchmarks():
    """Run all benchmarks"""
    print("="*60)
    print("Context Management Strategy Performance Benchmarks")
    print("上下文管理策略效能基準測試")
    print("="*60)
    
    # Test with different item counts
    test_sizes = [100, 1000]
    all_results = []
    
    for size in test_sizes:
        print(f"\n\n{'#'*60}")
        print(f"Testing with {size} items")
        print(f"{'#'*60}")
        
        items = create_test_items(size)
        
        # Test 1: Sliding Window Strategy
        window = SlidingWindowStrategy(window_size=50, overlap_size=5)
        results = benchmark_strategy(window, items, "SlidingWindowStrategy")
        results["test_size"] = size
        all_results.append(results)
        
        # Test 2: Summary Strategy
        summary = SummaryStrategy(segment_size=10, preserve_recent=5)
        results = benchmark_strategy(summary, items, "SummaryStrategy")
        results["test_size"] = size
        all_results.append(results)
        
        # Test 3: RAG Strategy (TF-IDF only)
        rag = RAGStrategy(use_vector_db=False)
        results = benchmark_strategy(rag, items, "RAGStrategy (TF-IDF)")
        results["test_size"] = size
        all_results.append(results)
        
        # Test 4: Workspace Strategy
        temp_dir = tempfile.mkdtemp()
        try:
            # Create test files
            for i in range(min(size, 100)):  # Limit files to 100 for speed
                Path(temp_dir, f"test_{i}.txt").write_text(f"Test content {i}")
            
            workspace = WorkspaceStrategy(workspace_path=temp_dir)
            # Don't add items, just test retrieval
            start = time.time()
            workspace.scan_workspace()
            scan_time = time.time() - start
            
            start = time.time()
            results = workspace.retrieve(query="test", limit=10)
            retrieve_time = time.time() - start
            
            print(f"\n{'='*60}")
            print(f"Testing WorkspaceStrategy")
            print(f"{'='*60}")
            print(f"Scan time: {scan_time:.4f}s")
            print(f"Retrieve time: {retrieve_time:.4f}s")
            print(f"Files indexed: {workspace.get_file_count()}")
            
            all_results.append({
                "name": "WorkspaceStrategy",
                "test_size": size,
                "scan_time": scan_time,
                "retrieve_query_time": retrieve_time,
                "files_indexed": workspace.get_file_count()
            })
        finally:
            shutil.rmtree(temp_dir)
        
        # Test 5: Hybrid Strategy
        hybrid = HybridStrategy(
            strategies=[
                SlidingWindowStrategy(window_size=50),
                SummaryStrategy(segment_size=10)
            ],
            weights=[0.6, 0.4]
        )
        results = benchmark_strategy(hybrid, items, "HybridStrategy (2 strategies)")
        results["test_size"] = size
        all_results.append(results)
    
    # Summary
    print(f"\n\n{'#'*60}")
    print("Performance Summary")
    print(f"{'#'*60}\n")
    
    print(f"{'Strategy':<30} {'Size':<10} {'Add (s)':<12} {'Items/s':<12} {'Compression':<12}")
    print("-" * 80)
    
    for result in all_results:
        if "add_time" in result:
            print(f"{result['name']:<30} {result['test_size']:<10} "
                  f"{result['add_time']:<12.4f} "
                  f"{result['items_per_second']:<12.0f} "
                  f"{result['compression_ratio']:<12.2%}")
    
    # Check if 1000 items < 1 second goal is met
    print(f"\n{'='*60}")
    print("Performance Goal: 1000 items < 1 second")
    print(f"{'='*60}\n")
    
    for result in all_results:
        if result.get("test_size") == 1000 and "add_time" in result:
            status = "✅ PASS" if result["add_time"] < 1.0 else "❌ FAIL"
            print(f"{result['name']:<30} {result['add_time']:.4f}s {status}")
    
    print("\n✅ Benchmark completed!")


if __name__ == "__main__":
    run_benchmarks()
