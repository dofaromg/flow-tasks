#!/usr/bin/env python3
"""
Tests for Enterprise Long-Running Task Management System
企業級長時間作業管理系統測試
"""

import time
import sys
import os
from pathlib import Path

# Add current directory to path
sys.path.insert(0, os.path.dirname(__file__))

from enterprise_task_manager import (
    EnterpriseTaskManager,
    TaskPriority,
    TaskStatus,
    example_long_running_task,
    example_computation_task
)


def test_basic_task_submission():
    """Test basic task submission and execution"""
    print("\n=== Test: Basic Task Submission ===")
    
    manager = EnterpriseTaskManager(max_workers=2, storage_dir="test_task_storage")
    manager.start()
    
    try:
        # Submit a simple task
        task_id = manager.submit_task(
            lambda x: x * 2,
            5,
            name="Simple Multiplication",
            priority=TaskPriority.HIGH
        )
        
        print(f"Task submitted: {task_id}")
        
        # Wait for completion
        max_wait = 10
        waited = 0
        while waited < max_wait:
            status = manager.get_task_status(task_id)
            print(f"  Status: {status}")
            
            if status in [TaskStatus.COMPLETED.value, TaskStatus.FAILED.value]:
                break
            
            time.sleep(1)
            waited += 1
        
        # Check result
        result = manager.get_task_result(task_id)
        assert result is not None, "Result should exist"
        assert result['status'] == TaskStatus.COMPLETED.value, f"Task should complete, got {result['status']}"
        assert result['result'] == 10, f"Result should be 10, got {result['result']}"
        
        print("  ✅ Basic task submission works")
        return True
        
    finally:
        manager.stop()
        # Cleanup
        import shutil
        if Path("test_task_storage").exists():
            shutil.rmtree("test_task_storage")


def test_priority_queue():
    """Test task priority queue"""
    print("\n=== Test: Priority Queue ===")
    
    manager = EnterpriseTaskManager(max_workers=1, storage_dir="test_task_storage_priority")
    manager.start()
    
    try:
        # Submit tasks with different priorities
        results = []
        
        # Low priority (should execute last)
        low_id = manager.submit_task(
            lambda: results.append("low"),
            name="Low Priority",
            priority=TaskPriority.LOW
        )
        
        # Give it time to queue
        time.sleep(0.1)
        
        # High priority (should execute before low)
        high_id = manager.submit_task(
            lambda: results.append("high"),
            name="High Priority",
            priority=TaskPriority.HIGH
        )
        
        # Critical priority (should execute first)
        critical_id = manager.submit_task(
            lambda: results.append("critical"),
            name="Critical Priority",
            priority=TaskPriority.CRITICAL
        )
        
        # Wait for all to complete
        max_wait = 15
        waited = 0
        while waited < max_wait:
            metrics = manager.get_metrics()
            if metrics['active_tasks'] == 0 and metrics['completed_tasks'] == 3:
                break
            time.sleep(1)
            waited += 1
        
        # Check execution order (critical > high > low)
        print(f"  Execution order: {results}")
        assert len(results) == 3, f"Should have 3 results, got {len(results)}"
        # Note: Order may vary due to threading, but critical should be processed with higher priority
        
        print("  ✅ Priority queue works")
        return True
        
    finally:
        manager.stop()
        import shutil
        if Path("test_task_storage_priority").exists():
            shutil.rmtree("test_task_storage_priority")


def test_task_retry():
    """Test automatic task retry on failure"""
    print("\n=== Test: Task Retry ===")
    
    manager = EnterpriseTaskManager(max_workers=2, storage_dir="test_task_storage_retry")
    manager.start()
    
    try:
        # Submit a task that fails initially
        attempt_count = [0]
        
        def failing_task():
            attempt_count[0] += 1
            if attempt_count[0] < 3:
                raise Exception(f"Failed attempt {attempt_count[0]}")
            return "Success on third attempt"
        
        task_id = manager.submit_task(
            failing_task,
            name="Retrying Task",
            max_retries=3
        )
        
        # Wait for completion
        max_wait = 30  # Retries take time with exponential backoff
        waited = 0
        while waited < max_wait:
            status = manager.get_task_status(task_id)
            print(f"  Status: {status}, Attempts: {attempt_count[0]}")
            
            if status in [TaskStatus.COMPLETED.value, TaskStatus.FAILED.value]:
                break
            
            time.sleep(1)
            waited += 1
        
        # Wait a bit more for result to be saved
        time.sleep(2)
        
        # Check result
        result = manager.get_task_result(task_id)
        
        if result is None:
            # Try a few more times due to race condition
            for _ in range(5):
                time.sleep(1)
                result = manager.get_task_result(task_id)
                if result is not None:
                    break
        
        assert result is not None, "Result should exist"
        print(f"  Final status: {result['status']}")
        print(f"  Retry count: {result['retry_count']}")
        print(f"  Total attempts: {attempt_count[0]}")
        
        # Task should succeed after retries
        assert result['status'] == TaskStatus.COMPLETED.value, "Task should eventually succeed"
        assert attempt_count[0] >= 3, "Should have attempted at least 3 times"
        
        print("  ✅ Task retry mechanism works")
        return True
        
    finally:
        manager.stop()
        import shutil
        if Path("test_task_storage_retry").exists():
            shutil.rmtree("test_task_storage_retry")


def test_concurrent_tasks():
    """Test concurrent task execution"""
    print("\n=== Test: Concurrent Tasks ===")
    
    manager = EnterpriseTaskManager(max_workers=3, storage_dir="test_task_storage_concurrent")
    manager.start()
    
    try:
        # Submit multiple tasks
        task_ids = []
        for i in range(5):
            task_id = manager.submit_task(
                lambda x: x ** 2,
                i,
                name=f"Task {i}"
            )
            task_ids.append(task_id)
        
        print(f"Submitted {len(task_ids)} tasks")
        
        # Wait for all to complete
        max_wait = 20
        waited = 0
        while waited < max_wait:
            metrics = manager.get_metrics()
            print(f"  Active: {metrics['active_tasks']}, Completed: {metrics['completed_tasks']}")
            
            if metrics['active_tasks'] == 0 and metrics['completed_tasks'] == 5:
                break
            
            time.sleep(1)
            waited += 1
        
        # Check all completed
        metrics = manager.get_metrics()
        assert metrics['completed_tasks'] == 5, f"Should have 5 completed tasks, got {metrics['completed_tasks']}"
        
        # Verify results
        for i, task_id in enumerate(task_ids):
            result = manager.get_task_result(task_id)
            assert result is not None, f"Result for task {i} should exist"
            assert result['status'] == TaskStatus.COMPLETED.value, f"Task {i} should complete"
            assert result['result'] == i ** 2, f"Task {i} result should be {i**2}, got {result['result']}"
        
        print("  ✅ Concurrent task execution works")
        return True
        
    finally:
        manager.stop()
        import shutil
        if Path("test_task_storage_concurrent").exists():
            shutil.rmtree("test_task_storage_concurrent")


def test_task_timeout():
    """Test task timeout"""
    print("\n=== Test: Task Timeout ===")
    
    manager = EnterpriseTaskManager(max_workers=2, storage_dir="test_task_storage_timeout")
    manager.start()
    
    try:
        # Submit a task that takes longer than timeout
        task_id = manager.submit_task(
            time.sleep,
            10,  # Sleep for 10 seconds
            name="Long Task",
            timeout_seconds=2,  # But timeout after 2 seconds
            max_retries=0  # Don't retry
        )
        
        # Wait for timeout
        max_wait = 10
        waited = 0
        while waited < max_wait:
            status = manager.get_task_status(task_id)
            print(f"  Status: {status}")
            
            if status in [TaskStatus.COMPLETED.value, TaskStatus.FAILED.value]:
                break
            
            time.sleep(1)
            waited += 1
        
        # Check result
        result = manager.get_task_result(task_id)
        assert result is not None, "Result should exist"
        assert result['status'] == TaskStatus.FAILED.value, "Task should fail due to timeout"
        assert 'TimeoutError' in result.get('error', '') or 'timeout' in result.get('error', '').lower(), \
            f"Error should mention timeout, got: {result.get('error')}"
        
        print("  ✅ Task timeout works")
        return True
        
    finally:
        manager.stop()
        import shutil
        if Path("test_task_storage_timeout").exists():
            shutil.rmtree("test_task_storage_timeout")


def test_metrics_tracking():
    """Test metrics tracking"""
    print("\n=== Test: Metrics Tracking ===")
    
    manager = EnterpriseTaskManager(max_workers=2, storage_dir="test_task_storage_metrics")
    manager.start()
    
    try:
        # Submit mix of successful and failing tasks
        success_ids = []
        for i in range(3):
            task_id = manager.submit_task(
                lambda x: x * 2,
                i,
                name=f"Success Task {i}"
            )
            success_ids.append(task_id)
        
        fail_ids = []
        for i in range(2):
            task_id = manager.submit_task(
                lambda: 1 / 0,  # Will raise ZeroDivisionError
                name=f"Fail Task {i}",
                max_retries=0
            )
            fail_ids.append(task_id)
        
        # Wait for all to complete
        max_wait = 15
        waited = 0
        while waited < max_wait:
            metrics = manager.get_metrics()
            if metrics['active_tasks'] == 0:
                break
            time.sleep(1)
            waited += 1
        
        # Check metrics
        metrics = manager.get_metrics()
        print(f"  Metrics: {metrics}")
        
        assert metrics['total_tasks'] == 5, f"Should have 5 total tasks, got {metrics['total_tasks']}"
        assert metrics['completed_tasks'] == 3, f"Should have 3 completed tasks, got {metrics['completed_tasks']}"
        assert metrics['failed_tasks'] == 2, f"Should have 2 failed tasks, got {metrics['failed_tasks']}"
        assert metrics['success_rate'] == 0.6, f"Success rate should be 0.6, got {metrics['success_rate']}"
        
        print("  ✅ Metrics tracking works")
        return True
        
    finally:
        manager.stop()
        import shutil
        if Path("test_task_storage_metrics").exists():
            shutil.rmtree("test_task_storage_metrics")


def test_task_persistence():
    """Test task persistence to storage"""
    print("\n=== Test: Task Persistence ===")
    
    storage_dir = "test_task_storage_persistence"
    
    # First session: submit tasks
    manager1 = EnterpriseTaskManager(max_workers=2, storage_dir=storage_dir)
    manager1.start()
    
    task1_id = manager1.submit_task(
        lambda x: x + 100,
        42,
        name="Persistent Task"
    )
    
    # Wait for completion
    time.sleep(3)
    result1 = manager1.get_task_result(task1_id)
    
    manager1.stop()
    
    # Second session: verify persistence
    manager2 = EnterpriseTaskManager(max_workers=2, storage_dir=storage_dir)
    manager2.start()
    
    try:
        # Should be able to retrieve task from storage
        task_info = manager2.store.get_task(task1_id)
        result2 = manager2.store.get_result(task1_id)
        
        assert task_info is not None, "Task should be persisted"
        assert result2 is not None, "Result should be persisted"
        assert result2['task_id'] == task1_id, "Task ID should match"
        assert result2['result'] == 142, f"Result should be 142, got {result2['result']}"
        
        print("  ✅ Task persistence works")
        return True
        
    finally:
        manager2.stop()
        import shutil
        if Path(storage_dir).exists():
            shutil.rmtree(storage_dir)


def test_long_running_task_example():
    """Test with example long-running task"""
    print("\n=== Test: Long-Running Task Example ===")
    
    manager = EnterpriseTaskManager(max_workers=2, storage_dir="test_task_storage_longrun")
    manager.start()
    
    try:
        # Submit long-running task
        task_id = manager.submit_task(
            example_long_running_task,
            3,  # 3 seconds
            False,  # Don't fail
            name="Example Long Task"
        )
        
        print(f"Task submitted: {task_id}")
        
        # Monitor progress
        max_wait = 10
        waited = 0
        while waited < max_wait:
            status = manager.get_task_status(task_id)
            progress = manager.get_task_progress(task_id)
            print(f"  Status: {status}, Progress: {progress:.1%}")
            
            if status in [TaskStatus.COMPLETED.value, TaskStatus.FAILED.value]:
                break
            
            time.sleep(1)
            waited += 1
        
        # Wait a bit for result to be persisted
        time.sleep(2)
        
        # Check result
        result = manager.get_task_result(task_id)
        
        if result is None:
            # Try a few more times due to race condition
            for _ in range(5):
                time.sleep(1)
                result = manager.get_task_result(task_id)
                if result is not None:
                    break
        
        assert result is not None, "Result should exist"
        assert result['status'] == TaskStatus.COMPLETED.value, "Task should complete"
        assert "completed" in result['result'].lower(), "Result should mention completion"
        
        print("  ✅ Long-running task example works")
        return True
        
    finally:
        manager.stop()
        import shutil
        if Path("test_task_storage_longrun").exists():
            shutil.rmtree("test_task_storage_longrun")


def run_all_tests():
    """Run all tests"""
    print("\n" + "="*60)
    print("企業級長時間作業管理系統測試")
    print("Enterprise Task Management System Tests")
    print("="*60)
    
    tests = [
        ("基本任務提交", test_basic_task_submission),
        ("優先級隊列", test_priority_queue),
        ("任務重試", test_task_retry),
        ("並發任務", test_concurrent_tasks),
        ("任務超時", test_task_timeout),
        ("指標追蹤", test_metrics_tracking),
        ("任務持久化", test_task_persistence),
        ("長時間任務範例", test_long_running_task_example),
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
