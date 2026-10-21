#!/usr/bin/env python3
"""
Enterprise Long-Running Task Management System
企業級長時間作業管理系統

Provides comprehensive task scheduling, execution, monitoring, and management
for long-running enterprise operations.

Features:
- Asynchronous task execution
- Task queue with priority support
- Progress tracking and reporting
- Automatic retry with exponential backoff
- Task persistence and recovery
- Worker pool management
- Metrics and monitoring
"""

import asyncio
import json
import time
import uuid
import threading
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor, Future
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Dict, List, Any, Optional, Callable, Union
from dataclasses import dataclass, asdict
from queue import PriorityQueue, Empty
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class TaskStatus(Enum):
    """Task execution status"""
    PENDING = "pending"
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    RETRYING = "retrying"


class TaskPriority(Enum):
    """Task priority levels"""
    LOW = 3
    NORMAL = 2
    HIGH = 1
    CRITICAL = 0


@dataclass
class TaskResult:
    """Task execution result"""
    task_id: str
    status: str
    result: Any = None
    error: Optional[str] = None
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    duration_seconds: float = 0.0
    retry_count: int = 0
    progress: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return asdict(self)


@dataclass
class Task:
    """Task definition"""
    task_id: str
    name: str
    func: Callable
    args: tuple = ()
    kwargs: Dict[str, Any] = None
    priority: TaskPriority = TaskPriority.NORMAL
    max_retries: int = 3
    timeout_seconds: Optional[int] = None
    created_at: str = None
    scheduled_for: Optional[str] = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.kwargs is None:
            self.kwargs = {}
        if self.created_at is None:
            self.created_at = datetime.now().isoformat()
        if self.metadata is None:
            self.metadata = {}
    
    def __lt__(self, other):
        """For priority queue comparison"""
        return self.priority.value < other.priority.value


class TaskStore:
    """Persistent task storage using JSON"""
    
    def __init__(self, storage_dir: str = "task_storage"):
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(exist_ok=True)
        self.tasks_file = self.storage_dir / "tasks.json"
        self.results_file = self.storage_dir / "results.json"
        self._lock = threading.Lock()
        
    def save_task(self, task: Task) -> None:
        """Save task to storage"""
        with self._lock:
            tasks = self._load_tasks()
            tasks[task.task_id] = {
                "task_id": task.task_id,
                "name": task.name,
                "priority": task.priority.name,
                "max_retries": task.max_retries,
                "timeout_seconds": task.timeout_seconds,
                "created_at": task.created_at,
                "scheduled_for": task.scheduled_for,
                "metadata": task.metadata
            }
            self._save_tasks(tasks)
    
    def save_result(self, result: TaskResult) -> None:
        """Save task result to storage"""
        with self._lock:
            results = self._load_results()
            results[result.task_id] = result.to_dict()
            self._save_results(results)
    
    def get_task(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get task by ID"""
        tasks = self._load_tasks()
        return tasks.get(task_id)
    
    def get_result(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get task result by ID"""
        results = self._load_results()
        return results.get(task_id)
    
    def get_all_tasks(self) -> Dict[str, Any]:
        """Get all tasks"""
        return self._load_tasks()
    
    def get_all_results(self) -> Dict[str, Any]:
        """Get all results"""
        return self._load_results()
    
    def _load_tasks(self) -> Dict[str, Any]:
        """Load tasks from file"""
        if self.tasks_file.exists():
            with open(self.tasks_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}
    
    def _save_tasks(self, tasks: Dict[str, Any]) -> None:
        """Save tasks to file"""
        with open(self.tasks_file, 'w', encoding='utf-8') as f:
            json.dump(tasks, f, indent=2, ensure_ascii=False)
    
    def _load_results(self) -> Dict[str, Any]:
        """Load results from file"""
        if self.results_file.exists():
            try:
                with open(self.results_file, 'r', encoding='utf-8') as f:
                    content = f.read().strip()
                    if not content:
                        return {}
                    return json.loads(content)
            except (json.JSONDecodeError, IOError):
                return {}
        return {}
    
    def _save_results(self, results: Dict[str, Any]) -> None:
        """Save results to file"""
        with open(self.results_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)


class TaskExecutor:
    """Execute tasks with progress tracking and error handling"""
    
    def __init__(self, max_workers: int = 4, use_processes: bool = False):
        self.max_workers = max_workers
        self.use_processes = use_processes
        self.executor = None
        self._active_tasks: Dict[str, Future] = {}
        self._task_status: Dict[str, TaskStatus] = {}
        self._task_progress: Dict[str, float] = {}
        self._lock = threading.Lock()
        
    def start(self):
        """Start the executor"""
        if self.use_processes:
            self.executor = ProcessPoolExecutor(max_workers=self.max_workers)
        else:
            self.executor = ThreadPoolExecutor(max_workers=self.max_workers)
        logger.info(f"Task executor started with {self.max_workers} workers")
    
    def stop(self):
        """Stop the executor"""
        if self.executor:
            self.executor.shutdown(wait=True)
            logger.info("Task executor stopped")
    
    def execute_task(
        self,
        task: Task,
        progress_callback: Optional[Callable[[str, float], None]] = None
    ) -> TaskResult:
        """Execute a single task"""
        start_time = datetime.now()
        result = TaskResult(
            task_id=task.task_id,
            status=TaskStatus.RUNNING.value,
            start_time=start_time.isoformat()
        )
        
        retry_count = 0
        max_retries = task.max_retries
        
        while retry_count <= max_retries:
            try:
                # Update status
                with self._lock:
                    self._task_status[task.task_id] = TaskStatus.RUNNING
                    self._task_progress[task.task_id] = 0.0
                
                # Execute task with timeout
                if task.timeout_seconds:
                    future = self.executor.submit(task.func, *task.args, **task.kwargs)
                    task_result = future.result(timeout=task.timeout_seconds)
                else:
                    task_result = task.func(*task.args, **task.kwargs)
                
                # Update progress
                if progress_callback:
                    progress_callback(task.task_id, 1.0)
                
                # Success
                end_time = datetime.now()
                result.status = TaskStatus.COMPLETED.value
                result.result = task_result
                result.end_time = end_time.isoformat()
                result.duration_seconds = (end_time - start_time).total_seconds()
                result.retry_count = retry_count
                result.progress = 1.0
                
                with self._lock:
                    self._task_status[task.task_id] = TaskStatus.COMPLETED
                    self._task_progress[task.task_id] = 1.0
                
                logger.info(f"Task {task.task_id} completed successfully")
                break
                
            except Exception as e:
                retry_count += 1
                error_msg = f"{type(e).__name__}: {str(e)}"
                
                if retry_count <= max_retries:
                    # Retry with exponential backoff
                    wait_time = min(2 ** retry_count, 60)  # Max 60 seconds
                    logger.warning(
                        f"Task {task.task_id} failed (attempt {retry_count}/{max_retries}), "
                        f"retrying in {wait_time}s: {error_msg}"
                    )
                    
                    with self._lock:
                        self._task_status[task.task_id] = TaskStatus.RETRYING
                    
                    time.sleep(wait_time)
                else:
                    # Max retries exceeded
                    end_time = datetime.now()
                    result.status = TaskStatus.FAILED.value
                    result.error = error_msg
                    result.end_time = end_time.isoformat()
                    result.duration_seconds = (end_time - start_time).total_seconds()
                    result.retry_count = retry_count - 1
                    
                    with self._lock:
                        self._task_status[task.task_id] = TaskStatus.FAILED
                    
                    logger.error(f"Task {task.task_id} failed after {max_retries} retries: {error_msg}")
                    break
        
        return result
    
    def get_task_status(self, task_id: str) -> Optional[TaskStatus]:
        """Get current task status"""
        with self._lock:
            return self._task_status.get(task_id)
    
    def get_task_progress(self, task_id: str) -> float:
        """Get current task progress (0.0 to 1.0)"""
        with self._lock:
            return self._task_progress.get(task_id, 0.0)


class EnterpriseTaskManager:
    """
    Enterprise-level long-running task management system
    企業級長時間作業管理系統
    """
    
    def __init__(
        self,
        max_workers: int = 4,
        storage_dir: str = "task_storage",
        use_processes: bool = False
    ):
        self.max_workers = max_workers
        self.storage_dir = storage_dir
        self.use_processes = use_processes
        
        # Components
        self.store = TaskStore(storage_dir)
        self.executor = TaskExecutor(max_workers, use_processes)
        self.task_queue = PriorityQueue()
        
        # State
        self._running = False
        self._worker_thread = None
        self._submitted_tasks: Dict[str, Task] = {}
        self._lock = threading.Lock()
        
        # Metrics
        self._metrics = {
            "total_tasks": 0,
            "completed_tasks": 0,
            "failed_tasks": 0,
            "cancelled_tasks": 0,
            "active_tasks": 0,
            "total_execution_time": 0.0
        }
    
    def start(self):
        """Start the task manager"""
        self.executor.start()
        self._running = True
        self._worker_thread = threading.Thread(target=self._process_queue, daemon=True)
        self._worker_thread.start()
        logger.info("Enterprise Task Manager started")
    
    def stop(self):
        """Stop the task manager"""
        self._running = False
        if self._worker_thread:
            self._worker_thread.join(timeout=5.0)
        self.executor.stop()
        logger.info("Enterprise Task Manager stopped")
    
    def submit_task(
        self,
        func: Callable,
        *args,
        name: str = None,
        priority: TaskPriority = TaskPriority.NORMAL,
        max_retries: int = 3,
        timeout_seconds: Optional[int] = None,
        scheduled_for: Optional[datetime] = None,
        metadata: Dict[str, Any] = None,
        **kwargs
    ) -> str:
        """
        Submit a task for execution
        
        Args:
            func: Function to execute
            *args: Positional arguments for the function
            name: Task name (optional)
            priority: Task priority
            max_retries: Maximum number of retries
            timeout_seconds: Task timeout in seconds
            scheduled_for: Schedule task for future execution
            metadata: Additional task metadata
            **kwargs: Keyword arguments for the function
        
        Returns:
            Task ID
        """
        task_id = str(uuid.uuid4())
        task_name = name or func.__name__
        
        task = Task(
            task_id=task_id,
            name=task_name,
            func=func,
            args=args,
            kwargs=kwargs,
            priority=priority,
            max_retries=max_retries,
            timeout_seconds=timeout_seconds,
            scheduled_for=scheduled_for.isoformat() if scheduled_for else None,
            metadata=metadata or {}
        )
        
        # Save task
        self.store.save_task(task)
        
        # Queue task
        with self._lock:
            self._submitted_tasks[task_id] = task
            self._metrics["total_tasks"] += 1
            self._metrics["active_tasks"] += 1
        
        self.task_queue.put(task)
        
        logger.info(f"Task {task_id} ({task_name}) submitted with priority {priority.name}")
        return task_id
    
    def _process_queue(self):
        """Process tasks from the queue (runs in separate thread)"""
        while self._running:
            try:
                # Get task from queue (timeout to check _running periodically)
                task = self.task_queue.get(timeout=1.0)
                
                # Check if scheduled for future
                if task.scheduled_for:
                    scheduled_time = datetime.fromisoformat(task.scheduled_for)
                    if datetime.now() < scheduled_time:
                        # Re-queue for later
                        self.task_queue.put(task)
                        time.sleep(1.0)
                        continue
                
                # Execute task
                result = self.executor.execute_task(task)
                
                # Save result
                self.store.save_result(result)
                
                # Update metrics
                with self._lock:
                    self._metrics["active_tasks"] -= 1
                    if result.status == TaskStatus.COMPLETED.value:
                        self._metrics["completed_tasks"] += 1
                    elif result.status == TaskStatus.FAILED.value:
                        self._metrics["failed_tasks"] += 1
                    self._metrics["total_execution_time"] += result.duration_seconds
                
            except Empty:
                continue
            except Exception as e:
                logger.error(f"Error processing queue: {e}")
    
    def get_task_status(self, task_id: str) -> Optional[str]:
        """Get task status"""
        status = self.executor.get_task_status(task_id)
        if status:
            return status.value
        
        # Check if in queue
        with self._lock:
            if task_id in self._submitted_tasks:
                return TaskStatus.QUEUED.value
        
        # Check storage
        result = self.store.get_result(task_id)
        if result:
            return result.get("status")
        
        return None
    
    def get_task_result(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get task result"""
        return self.store.get_result(task_id)
    
    def get_task_progress(self, task_id: str) -> float:
        """Get task progress (0.0 to 1.0)"""
        return self.executor.get_task_progress(task_id)
    
    def cancel_task(self, task_id: str) -> bool:
        """Cancel a pending task"""
        # Cannot cancel running tasks in this implementation
        # Only remove from queue if pending
        with self._lock:
            if task_id in self._submitted_tasks:
                # Mark as cancelled
                result = TaskResult(
                    task_id=task_id,
                    status=TaskStatus.CANCELLED.value,
                    end_time=datetime.now().isoformat()
                )
                self.store.save_result(result)
                self._metrics["cancelled_tasks"] += 1
                self._metrics["active_tasks"] -= 1
                del self._submitted_tasks[task_id]
                logger.info(f"Task {task_id} cancelled")
                return True
        
        return False
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get task execution metrics"""
        with self._lock:
            metrics = self._metrics.copy()
        
        # Calculate derived metrics
        if metrics["completed_tasks"] > 0:
            metrics["average_execution_time"] = (
                metrics["total_execution_time"] / metrics["completed_tasks"]
            )
        else:
            metrics["average_execution_time"] = 0.0
        
        if metrics["total_tasks"] > 0:
            metrics["success_rate"] = (
                metrics["completed_tasks"] / metrics["total_tasks"]
            )
        else:
            metrics["success_rate"] = 0.0
        
        return metrics
    
    def get_all_tasks(self) -> List[Dict[str, Any]]:
        """Get all tasks with their results"""
        tasks = self.store.get_all_tasks()
        results = self.store.get_all_results()
        
        task_list = []
        for task_id, task_info in tasks.items():
            result = results.get(task_id, {})
            task_list.append({
                **task_info,
                "result": result
            })
        
        return task_list


# Convenience functions
def example_long_running_task(duration: int = 5, fail: bool = False) -> str:
    """Example long-running task for testing"""
    logger.info(f"Starting long-running task (duration: {duration}s)")
    
    for i in range(duration):
        time.sleep(1)
        logger.info(f"Progress: {(i+1)/duration:.1%}")
        
        if fail and i == duration - 1:
            raise Exception("Task failed as requested")
    
    return f"Task completed after {duration} seconds"


def example_computation_task(n: int = 1000000) -> Dict[str, Any]:
    """Example computation task"""
    logger.info(f"Starting computation with n={n}")
    
    # Simulate heavy computation
    result = sum(i * i for i in range(n))
    
    return {
        "n": n,
        "result": result,
        "computation_type": "sum of squares"
    }


if __name__ == "__main__":
    # Demo usage
    print("=== Enterprise Task Manager Demo ===\n")
    
    # Create and start manager
    manager = EnterpriseTaskManager(max_workers=2)
    manager.start()
    
    try:
        # Submit various tasks
        print("Submitting tasks...")
        
        task1_id = manager.submit_task(
            example_long_running_task,
            3,
            name="Quick Task",
            priority=TaskPriority.HIGH
        )
        print(f"  Task 1 submitted: {task1_id}")
        
        task2_id = manager.submit_task(
            example_long_running_task,
            5,
            name="Medium Task",
            priority=TaskPriority.NORMAL
        )
        print(f"  Task 2 submitted: {task2_id}")
        
        task3_id = manager.submit_task(
            example_computation_task,
            1000000,
            name="Computation Task",
            priority=TaskPriority.LOW
        )
        print(f"  Task 3 submitted: {task3_id}")
        
        # Monitor tasks
        print("\nMonitoring tasks...")
        while True:
            time.sleep(2)
            
            metrics = manager.get_metrics()
            print(f"\nMetrics:")
            print(f"  Active: {metrics['active_tasks']}")
            print(f"  Completed: {metrics['completed_tasks']}")
            print(f"  Failed: {metrics['failed_tasks']}")
            print(f"  Success Rate: {metrics['success_rate']:.1%}")
            
            # Check individual tasks
            for task_id, name in [(task1_id, "Task 1"), (task2_id, "Task 2"), (task3_id, "Task 3")]:
                status = manager.get_task_status(task_id)
                progress = manager.get_task_progress(task_id)
                print(f"  {name}: {status} ({progress:.1%})")
            
            # Exit when all done
            if metrics['active_tasks'] == 0:
                break
        
        # Show results
        print("\n=== Final Results ===")
        all_tasks = manager.get_all_tasks()
        for task in all_tasks:
            print(f"\nTask: {task['name']}")
            print(f"  ID: {task['task_id']}")
            print(f"  Status: {task['result'].get('status', 'unknown')}")
            if task['result'].get('duration_seconds'):
                print(f"  Duration: {task['result']['duration_seconds']:.2f}s")
            if task['result'].get('result'):
                print(f"  Result: {str(task['result']['result'])[:100]}")
        
        print("\n=== Final Metrics ===")
        final_metrics = manager.get_metrics()
        for key, value in final_metrics.items():
            print(f"  {key}: {value}")
        
    finally:
        # Cleanup
        print("\nStopping manager...")
        manager.stop()
        print("Demo completed!")
