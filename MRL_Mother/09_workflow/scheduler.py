#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
scheduler.py — Async Task Scheduler / Priority Queue
origin_signature: MrLiouWord
layer: L7 LOOP
group: Y=3 MrLiouAIRuntime

Industry capability: background task queue for long-running agent operations —
                     the same pattern used in production AI pipelines to handle
                     async LLM calls, tool executions, and batch evaluations.
MRL extension: every task record is stamped with origin_signature and can be
               persisted + queried via the librarian index.

Key classes
-----------
  Task          — immutable task spec (id, fn, priority, metadata)
  TaskResult    — outcome record after execution
  TaskScheduler — threaded priority-queue scheduler with status tracking

Task status lifecycle
---------------------
  PENDING → RUNNING → DONE
                    ↘ FAILED

Usage (library)
---------------
    from scheduler import TaskScheduler

    sched = TaskScheduler()
    sched.start()

    tid = sched.submit(lambda: 2 + 2, name="add", priority=1)
    result = sched.wait(tid, timeout=5.0)
    print(result.output)   # 4

    sched.stop()

CLI
---
    python 09_workflow/scheduler.py demo
    python 09_workflow/scheduler.py status
"""

from __future__ import annotations

import argparse
import json
import queue
import threading
import time
import traceback
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional

ORIGIN_SIGNATURE = "MrLiouWord"


# ─── TaskStatus ──────────────────────────────────────────────────────────────

class TaskStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    DONE    = "done"
    FAILED  = "failed"
    CANCELLED = "cancelled"


# ─── Task ─────────────────────────────────────────────────────────────────────

@dataclass
class Task:
    """
    An immutable task specification.

    Fields
    ------
    fn          : zero-argument callable to execute
    task_id     : auto-generated UUID
    name        : human-readable label
    priority    : lower number = higher priority (like Python heapq)
    created_at_ms
    meta        : arbitrary metadata dict
    """

    fn: Callable[[], Any]
    task_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = "unnamed"
    priority: int = 5
    created_at_ms: int = field(default_factory=lambda: int(time.time() * 1000))
    meta: Dict[str, Any] = field(default_factory=dict)

    # For priority queue ordering (lower priority value = higher urgency)
    def __lt__(self, other: "Task") -> bool:
        if self.priority != other.priority:
            return self.priority < other.priority
        return self.created_at_ms < other.created_at_ms


# ─── TaskResult ──────────────────────────────────────────────────────────────

@dataclass
class TaskResult:
    """
    The outcome record after a task completes or fails.
    """

    task_id: str
    name: str
    status: TaskStatus
    output: Any = None
    error: Optional[str] = None
    tb: Optional[str] = None
    started_at_ms: int = 0
    ended_at_ms: int = 0
    elapsed_ms: int = 0
    priority: int = 5
    meta: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "task_id": self.task_id,
            "name": self.name,
            "status": self.status.value,
            "output": self.output,
            "error": self.error,
            "elapsed_ms": self.elapsed_ms,
            "started_at_ms": self.started_at_ms,
            "ended_at_ms": self.ended_at_ms,
            "priority": self.priority,
            "meta": self.meta,
            "origin_signature": ORIGIN_SIGNATURE,
        }


# ─── TaskScheduler ───────────────────────────────────────────────────────────

class TaskScheduler:
    """
    Thread-based priority queue scheduler.

    Spawns a background worker thread that continuously dequeues and executes
    tasks in priority order.  Thread-safe for concurrent ``submit`` calls.

    Parameters
    ----------
    workers     : int
        Number of parallel worker threads (default 1).
    max_queue   : int
        Maximum pending tasks before ``submit`` blocks (default 1000).
    """

    def __init__(self, workers: int = 1, max_queue: int = 1000) -> None:
        self._workers = workers
        self._q: queue.PriorityQueue = queue.PriorityQueue(maxsize=max_queue)
        self._results: Dict[str, TaskResult] = {}
        self._lock = threading.Lock()
        self._threads: List[threading.Thread] = []
        self._running = False
        self._stop_event = threading.Event()

    # ── Lifecycle ─────────────────────────────────────────────────────────────

    def start(self) -> None:
        """Start the worker thread(s)."""
        if self._running:
            return
        self._running = True
        self._stop_event.clear()
        for i in range(self._workers):
            t = threading.Thread(
                target=self._worker_loop,
                name=f"scheduler-worker-{i}",
                daemon=True,
            )
            t.start()
            self._threads.append(t)

    def stop(self, timeout: float = 5.0) -> None:
        """Signal workers to stop and wait for them to finish."""
        self._stop_event.set()
        # Unblock workers waiting on an empty queue
        for _ in self._threads:
            try:
                self._q.put_nowait((_SENTINEL_PRIORITY, _Sentinel()))
            except queue.Full:
                pass
        for t in self._threads:
            t.join(timeout=timeout)
        self._running = False
        self._threads.clear()

    # ── Submit ────────────────────────────────────────────────────────────────

    def submit(
        self,
        fn: Callable[[], Any],
        *,
        name: str = "task",
        priority: int = 5,
        meta: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Enqueue a task and return its task_id.

        Parameters
        ----------
        fn       : zero-argument callable
        name     : human-readable label
        priority : lower = higher urgency (1–10 recommended)
        meta     : extra metadata attached to the result
        """
        task = Task(fn=fn, name=name, priority=priority, meta=meta or {})
        # Record as PENDING immediately
        result = TaskResult(
            task_id=task.task_id,
            name=task.name,
            status=TaskStatus.PENDING,
            priority=priority,
            meta=task.meta,
        )
        with self._lock:
            self._results[task.task_id] = result

        self._q.put((task.priority, task))
        return task.task_id

    # ── Query ─────────────────────────────────────────────────────────────────

    def get_result(self, task_id: str) -> Optional[TaskResult]:
        with self._lock:
            return self._results.get(task_id)

    def wait(
        self,
        task_id: str,
        timeout: float = 30.0,
        poll_interval: float = 0.05,
    ) -> Optional[TaskResult]:
        """Block until the task reaches a terminal state or *timeout* expires."""
        deadline = time.time() + timeout
        while time.time() < deadline:
            result = self.get_result(task_id)
            if result and result.status in (TaskStatus.DONE, TaskStatus.FAILED, TaskStatus.CANCELLED):
                return result
            time.sleep(poll_interval)
        return self.get_result(task_id)

    def list_results(
        self,
        status_filter: Optional[TaskStatus] = None,
    ) -> List[Dict[str, Any]]:
        with self._lock:
            results = list(self._results.values())
        if status_filter:
            results = [r for r in results if r.status == status_filter]
        return [r.to_dict() for r in sorted(results, key=lambda r: r.started_at_ms or r.ended_at_ms)]

    def queue_size(self) -> int:
        return self._q.qsize()

    def stats(self) -> Dict[str, Any]:
        with self._lock:
            by_status: Dict[str, int] = {}
            for r in self._results.values():
                by_status[r.status.value] = by_status.get(r.status.value, 0) + 1
        return {
            "running": self._running,
            "workers": self._workers,
            "queue_size": self.queue_size(),
            "total_tasks": len(self._results),
            "by_status": by_status,
            "origin_signature": ORIGIN_SIGNATURE,
        }

    # ── Worker ────────────────────────────────────────────────────────────────

    def _worker_loop(self) -> None:
        while not self._stop_event.is_set():
            try:
                _, item = self._q.get(timeout=0.1)
            except queue.Empty:
                continue

            if isinstance(item, _Sentinel):
                break

            task: Task = item
            self._execute(task)
            self._q.task_done()

    def _execute(self, task: Task) -> None:
        started = int(time.time() * 1000)
        with self._lock:
            r = self._results.get(task.task_id)
            if r:
                r.status = TaskStatus.RUNNING
                r.started_at_ms = started

        t0 = time.time()
        output = None
        error = None
        tb_str = None
        status = TaskStatus.DONE

        try:
            output = task.fn()
        except Exception as exc:  # noqa: BLE001
            error = f"{type(exc).__name__}: {exc}"
            tb_str = traceback.format_exc()
            status = TaskStatus.FAILED
        finally:
            ended = int(time.time() * 1000)
            with self._lock:
                r = self._results.get(task.task_id)
                if r:
                    r.status = status
                    r.output = output
                    r.error = error
                    r.tb = tb_str
                    r.ended_at_ms = ended
                    r.elapsed_ms = int((time.time() - t0) * 1000)


# ─── Internal sentinel ───────────────────────────────────────────────────────

_SENTINEL_PRIORITY = 9999


class _Sentinel:
    """Used to unblock workers when stopping."""
    def __lt__(self, other: Any) -> bool:
        return False


# ─── CLI ─────────────────────────────────────────────────────────────────────

def _cmd_demo(_args: argparse.Namespace) -> None:
    sched = TaskScheduler(workers=2)
    sched.start()

    ids = []
    for i in range(5):
        priority = 5 - i  # earlier tasks have lower priority number = run first
        tid = sched.submit(
            lambda n=i: n * n,
            name=f"square_{i}",
            priority=priority,
        )
        ids.append(tid)
        print(f"Submitted task {tid[:8]}…  priority={priority}")

    print("\nWaiting for tasks to complete…")
    for tid in ids:
        r = sched.wait(tid, timeout=5.0)
        if r:
            print(f"  {r.name}: {r.output}  [{r.status.value}]  elapsed={r.elapsed_ms}ms")

    print("\n=== Scheduler stats ===")
    print(json.dumps(sched.stats(), ensure_ascii=False, indent=2))
    sched.stop()


def _cmd_status(_args: argparse.Namespace) -> None:
    sched = TaskScheduler()
    print(json.dumps(sched.stats(), ensure_ascii=False, indent=2))


def _build_argparser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="scheduler — async task scheduler")
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("demo", help="Run a scheduler demo (5 tasks, 2 workers)")
    sub.add_parser("status", help="Print scheduler stats")
    return p


def main() -> None:
    parser = _build_argparser()
    args = parser.parse_args()
    dispatch = {"demo": _cmd_demo, "status": _cmd_status}
    dispatch[args.cmd](args)


if __name__ == "__main__":
    main()
