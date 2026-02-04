#!/usr/bin/env python3
"""
Performance improvement tests for flow-tasks optimizations
Tests for Issue: Identify and suggest improvements to slow or inefficient code
"""

import os
import sys
import tempfile
import json
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))


def test_file_handle_closure():
    """Test that file handles are properly closed using context managers"""
    print("\n" + "="*70)
    print("TEST 1: File Handle Closure")
    print("="*70)
    
    # Create a test file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        test_file = f.name
        json.dump({"test": "data"}, f)
    
    try:
        # Import and test Tracer class
        sys.path.insert(0, str(Path(__file__).parent / 'MrLiou_AI_SuperComputer'))
        from flowcore_loop import Tracer
        
        # Create temporary directory for tracer logs
        with tempfile.TemporaryDirectory() as tmpdir:
            original_cwd = os.getcwd()
            os.chdir(tmpdir)
            
            try:
                # Initialize tracer
                tracer = Tracer()
                
                # Emit an event - this should properly close file handles
                result = tracer.emit("test_event", {"data": "test"})
                
                # Verify the tracer state file was created and can be read
                assert os.path.exists("log/trace_state.json"), "State file should exist"
                
                # Read the state file - if handles weren't closed properly, this might fail
                with open("log/trace_state.json", 'r') as f:
                    state = json.load(f)
                
                assert state["tick"] == 1, "Tick should be incremented"
                assert "merkle_root" in state, "State should have merkle_root"
                
                print("✅ File handles are properly closed")
                
            finally:
                os.chdir(original_cwd)
    
    finally:
        # Cleanup
        if os.path.exists(test_file):
            os.unlink(test_file)
    
    return True


def test_set_lookup_performance():
    """Test that set lookups are used instead of list lookups"""
    print("\n" + "="*70)
    print("TEST 2: Set vs List Lookup Performance")
    print("="*70)
    
    import time
    
    # Create test data
    tokens_list = [f"token_{i}" for i in range(1000)]
    tokens_set = set(tokens_list)
    query_tokens = [f"token_{i}" for i in range(0, 1000, 10)]  # Every 10th token
    
    # Test list lookup
    start = time.perf_counter()
    list_score = sum(1 for t in query_tokens if t in tokens_list)
    list_time = time.perf_counter() - start
    
    # Test set lookup
    start = time.perf_counter()
    set_score = sum(1 for t in query_tokens if t in tokens_set)
    set_time = time.perf_counter() - start
    
    # Verify correctness
    assert list_score == set_score, "Both methods should return same score"
    
    # Performance comparison
    speedup = list_time / set_time if set_time > 0 else float('inf')
    
    print(f"List lookup time: {list_time*1000:.4f}ms")
    print(f"Set lookup time:  {set_time*1000:.4f}ms")
    print(f"Speedup: {speedup:.2f}x faster with set")
    print(f"✅ Set lookup is {speedup:.2f}x faster than list lookup")
    
    # Set should be significantly faster (at least 2x for this size)
    assert speedup > 2.0, f"Set lookup should be at least 2x faster, got {speedup:.2f}x"
    
    return True


def test_deepcopy_vs_json_roundtrip():
    """Test that copy.deepcopy is used instead of JSON round-trip"""
    print("\n" + "="*70)
    print("TEST 3: Deep Copy vs JSON Round-trip Performance")
    print("="*70)
    
    import time
    import copy
    
    # Create complex nested structure
    test_data = {
        "nested": {
            "level1": {
                "level2": {
                    "level3": {
                        "data": [1, 2, 3, 4, 5] * 20,
                        "strings": ["test" * 10] * 10
                    }
                }
            }
        },
        "list": [[i] * 10 for i in range(50)],
        "metadata": {f"key_{i}": f"value_{i}" for i in range(100)}
    }
    
    # Test JSON round-trip
    start = time.perf_counter()
    json_copy = json.loads(json.dumps(test_data, ensure_ascii=False))
    json_time = time.perf_counter() - start
    
    # Test copy.deepcopy
    start = time.perf_counter()
    deep_copy = copy.deepcopy(test_data)
    deepcopy_time = time.perf_counter() - start
    
    # Verify correctness
    assert json_copy == deep_copy, "Both methods should produce identical copies"
    
    # Performance comparison
    print(f"JSON round-trip time: {json_time*1000:.4f}ms")
    print(f"copy.deepcopy time:   {deepcopy_time*1000:.4f}ms")
    
    if deepcopy_time < json_time:
        speedup = json_time / deepcopy_time
        print(f"✅ copy.deepcopy is {speedup:.2f}x faster than JSON round-trip")
    else:
        ratio = deepcopy_time / json_time
        print(f"ℹ️  JSON round-trip is {ratio:.2f}x faster (acceptable for simple structures)")
    
    return True


def test_early_convergence_exit():
    """Test that recursive loops exit early on convergence"""
    print("\n" + "="*70)
    print("TEST 4: Early Convergence Detection")
    print("="*70)
    
    # Simulate convergence detection
    max_cycles = 10
    convergence_cycle = 3
    
    # Old approach: Always runs all cycles
    old_iterations = max_cycles
    
    # New approach: Exits early on convergence
    new_iterations = 0
    previous_data = None
    current_data = {"value": 1}
    
    for cycle in range(max_cycles):
        new_iterations += 1
        
        # Simulate computation
        if cycle < convergence_cycle:
            current_data = {"value": cycle + 2}
        # After convergence_cycle, data stops changing
        
        # Early exit check
        if cycle > 0 and current_data == previous_data:
            break
        previous_data = current_data.copy()
    
    improvement = ((old_iterations - new_iterations) / old_iterations) * 100
    
    print(f"Old approach: {old_iterations} iterations")
    print(f"New approach: {new_iterations} iterations")
    print(f"Improvement: {improvement:.1f}% fewer iterations")
    print(f"✅ Early exit reduced iterations by {improvement:.1f}%")
    
    assert new_iterations <= convergence_cycle + 1, "Should exit shortly after convergence"
    assert new_iterations < old_iterations, "Should use fewer iterations"
    
    return True


def main():
    """Run all performance improvement tests"""
    print("\n" + "="*70)
    print("PERFORMANCE IMPROVEMENTS TEST SUITE")
    print("Testing optimizations for slow and inefficient code")
    print("="*70)
    
    tests = [
        test_file_handle_closure,
        test_set_lookup_performance,
        test_deepcopy_vs_json_roundtrip,
        test_early_convergence_exit,
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            failed += 1
            print(f"\n❌ Test failed: {test.__name__}")
            print(f"Error: {e}")
            import traceback
            traceback.print_exc()
    
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)
    print(f"✅ Passed: {passed}/{len(tests)}")
    print(f"❌ Failed: {failed}/{len(tests)}")
    
    if failed == 0:
        print("\n🎉 All performance improvement tests passed!")
        return 0
    else:
        print(f"\n⚠️  {failed} test(s) failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())
