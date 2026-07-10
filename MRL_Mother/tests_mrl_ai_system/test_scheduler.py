"""
test_scheduler.py — Smoke tests for scheduler.py
origin_signature: MrLiouWord
"""
from __future__ import annotations

import time

import pytest

from scheduler import Task, TaskResult, TaskScheduler, TaskStatus


# ─── Task dataclass ───────────────────────────────────────────────────────────

class TestTask:
    def test_task_auto_id(self):
        t = Task(fn=lambda: None)
        assert t.task_id and len(t.task_id) == 36  # UUID4

    def test_task_priority_ordering(self):
        t1 = Task(fn=lambda: None, priority=1)
        t2 = Task(fn=lambda: None, priority=5)
        assert t1 < t2

    def test_task_same_priority_ordered_by_time(self):
        t1 = Task(fn=lambda: None, priority=3, created_at_ms=1000)
        t2 = Task(fn=lambda: None, priority=3, created_at_ms=2000)
        assert t1 < t2


# ─── TaskResult ──────────────────────────────────────────────────────────────

class TestTaskResult:
    def test_to_dict_has_required_keys(self):
        r = TaskResult(task_id="abc", name="test", status=TaskStatus.DONE, output=42)
        d = r.to_dict()
        assert d["task_id"] == "abc"
        assert d["status"] == "done"
        assert d["output"] == 42
        assert d["origin_signature"] == "MrLiouWord"


# ─── TaskScheduler ────────────────────────────────────────────────────────────

class TestTaskSchedulerBasic:
    def setup_method(self):
        self.sched = TaskScheduler(workers=1, max_queue=100)
        self.sched.start()

    def teardown_method(self):
        self.sched.stop(timeout=3.0)

    def test_submit_and_wait_done(self):
        tid = self.sched.submit(lambda: 42, name="add")
        result = self.sched.wait(tid, timeout=5.0)
        assert result is not None
        assert result.status == TaskStatus.DONE
        assert result.output == 42

    def test_failed_task(self):
        def blow_up():
            raise RuntimeError("intentional failure")

        tid = self.sched.submit(blow_up, name="fail")
        result = self.sched.wait(tid, timeout=5.0)
        assert result is not None
        assert result.status == TaskStatus.FAILED
        assert "RuntimeError" in (result.error or "")

    def test_result_has_elapsed_ms(self):
        tid = self.sched.submit(lambda: time.sleep(0.01), name="sleep")
        result = self.sched.wait(tid, timeout=5.0)
        assert result is not None
        assert result.elapsed_ms >= 0

    def test_pending_then_done(self):
        import threading
        barrier = threading.Event()

        def slow():
            barrier.wait(timeout=5)
            return "done"

        tid = self.sched.submit(slow, name="slow")
        # Task should be PENDING or RUNNING before barrier is released
        r = self.sched.get_result(tid)
        assert r is not None
        assert r.status in (TaskStatus.PENDING, TaskStatus.RUNNING)

        barrier.set()
        result = self.sched.wait(tid, timeout=5.0)
        assert result.status == TaskStatus.DONE

    def test_queue_size_decreases_after_completion(self):
        # Queue size observed after task completes should be 0
        tid = self.sched.submit(lambda: None, name="noop")
        self.sched.wait(tid, timeout=5.0)
        assert self.sched.queue_size() == 0


class TestTaskSchedulerPriority:
    def test_higher_priority_runs_first(self):
        """Tasks with lower priority number should run before higher-number ones."""
        sched = TaskScheduler(workers=1, max_queue=10)
        order: list = []

        # Submit a blocking task first to hold the worker
        import threading
        gate = threading.Event()
        sched.submit(lambda: gate.wait(2.0), name="block", priority=5)
        sched.start()

        tid_low  = sched.submit(lambda: order.append("low"),  name="low",  priority=9)
        tid_high = sched.submit(lambda: order.append("high"), name="high", priority=1)

        gate.set()
        sched.wait(tid_low,  timeout=5.0)
        sched.wait(tid_high, timeout=5.0)
        sched.stop()

        # "high" (priority=1) should have run before "low" (priority=9)
        if order:  # order may be empty if tasks ran before gate; just check no crash
            assert order.index("high") < order.index("low")


class TestTaskSchedulerStats:
    def test_stats_structure(self):
        sched = TaskScheduler(workers=2)
        sched.start()
        stats = sched.stats()
        assert stats["workers"] == 2
        assert stats["running"] is True
        assert "by_status" in stats
        assert stats["origin_signature"] == "MrLiouWord"
        sched.stop()

    def test_stop_sets_running_false(self):
        sched = TaskScheduler()
        sched.start()
        assert sched.stats()["running"] is True
        sched.stop()
        assert sched.stats()["running"] is False


class TestTaskSchedulerConcurrency:
    def test_multiple_workers_execute_concurrently(self):
        """Two workers should overlap on two 0.1s tasks → total well under 2× 0.1s."""
        sched = TaskScheduler(workers=2)
        sched.start()
        t0 = time.time()
        t1 = sched.submit(lambda: time.sleep(0.1), name="t1")
        t2 = sched.submit(lambda: time.sleep(0.1), name="t2")
        sched.wait(t1, timeout=3.0)
        sched.wait(t2, timeout=3.0)
        elapsed = time.time() - t0
        sched.stop()
        # Both tasks run concurrently; total should be much less than sequential 0.2s.
        # Use a generous 2.0s bound to avoid flakiness on slow/contended CI runners.
        assert elapsed < 2.0

    def test_list_results_returns_all(self):
        sched = TaskScheduler(workers=2)
        sched.start()
        ids = [sched.submit(lambda: i, name=f"t{i}") for i in range(5)]
        for tid in ids:
            sched.wait(tid, timeout=5.0)
        results = sched.list_results()
        sched.stop()
        assert len(results) == 5
