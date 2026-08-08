#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MRL_task_orchestrator.py — Production Task Orchestration Engine
origin_signature: MrLiouWord
layer: L7 LOOP
group: Y=3 MrLiouAIRuntime

Combines scheduler.py + multi_agent.py into a production task engine with:
  - Task status: QUEUED / RUNNING / WAITING_TOOL / DONE / FAILED / SEALED
  - Task sealing with merkle chain integration
  - Error trace preservation for failed tasks
  - Full task lifecycle tracking

This is the production-ready orchestrator that ties together:
  - TaskScheduler (background execution)
  - MultiAgentSession (agent coordination)
  - MerkleChain (immutable audit trail)
  - Conversation/Memory integration

Usage (library)
---------------
    from MRL_task_orchestrator import TaskOrchestrator, TaskStatus

    orch = TaskOrchestrator()
    orch.start()

    task_id = orch.submit_task(
        goal="Analyze the repo structure",
        task_type="agent",
        agents=["analyzer", "summarizer"]
    )

    result = orch.wait_for_task(task_id)
    print(result["status"])  # DONE | FAILED
    print(result["output"])

    # Seal the task result
    seal_record = orch.seal_task(task_id)

CLI
---
    python 09_workflow/MRL_task_orchestrator.py submit --goal "Test task"
    python 09_workflow/MRL_task_orchestrator.py status --task-id <id>
    python 09_workflow/MRL_task_orchestrator.py seal --task-id <id>
"""

from __future__ import annotations

import argparse
import json
import pathlib
import sys
import time
import traceback
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional

ORIGIN_SIGNATURE = "MrLiouWord"

_REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent

# ── Ensure module paths ───────────────────────────────────────────────────────

def _ensure_paths() -> None:
    for sub in [
        _REPO_ROOT / "09_workflow",
        _REPO_ROOT / "03_memory" / "merkle",
    ]:
        p = str(sub)
        if p not in sys.path:
            sys.path.insert(0, p)

_ensure_paths()


def _try_import(module: str, attr: str) -> Any:
    try:
        import importlib
        mod = importlib.import_module(module)
        return getattr(mod, attr)
    except Exception:  # noqa: BLE001
        return None


# ─── TaskStatus ───────────────────────────────────────────────────────────────

class TaskStatus(str, Enum):
    """Extended task status for production orchestration."""
    QUEUED = "queued"           # Submitted but not started
    RUNNING = "running"         # Currently executing
    WAITING_TOOL = "waiting_tool"  # Waiting for tool execution
    DONE = "done"              # Completed successfully
    FAILED = "failed"          # Raised exception
    SEALED = "sealed"          # Result sealed to merkle chain


# ─── OrchestratedTask ─────────────────────────────────────────────────────────

@dataclass
class OrchestratedTask:
    """
    Enhanced task record with full lifecycle tracking.
    """
    task_id: str
    goal: str
    task_type: str  # "simple" | "agent" | "multi_agent"
    status: TaskStatus
    created_at_ms: int
    started_at_ms: Optional[int] = None
    ended_at_ms: Optional[int] = None
    elapsed_ms: Optional[int] = None
    output: Any = None
    error: Optional[str] = None
    error_trace: Optional[str] = None
    meta: Dict[str, Any] = field(default_factory=dict)
    seal_record: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "task_id": self.task_id,
            "goal": self.goal,
            "task_type": self.task_type,
            "status": self.status.value,
            "created_at_ms": self.created_at_ms,
            "started_at_ms": self.started_at_ms,
            "ended_at_ms": self.ended_at_ms,
            "elapsed_ms": self.elapsed_ms,
            "output": self.output,
            "error": self.error,
            "error_trace": self.error_trace,
            "meta": self.meta,
            "seal_record": self.seal_record,
            "origin_signature": ORIGIN_SIGNATURE,
        }


# ─── TaskOrchestrator ─────────────────────────────────────────────────────────

class TaskOrchestrator:
    """
    Production task orchestration engine.

    Combines TaskScheduler + MultiAgentSession + MerkleChain to provide:
      - Task queueing with priority
      - Agent coordination
      - Immutable audit trail
      - Error preservation
      - Result sealing
    """

    def __init__(self) -> None:
        self._scheduler: Any = None
        self._chain: Any = None
        self._tasks: Dict[str, OrchestratedTask] = {}
        self._initialized = False

    def start(self) -> None:
        """Initialize the orchestrator and start the task scheduler."""
        if self._initialized:
            return

        # Initialize scheduler
        TaskScheduler = _try_import("scheduler", "TaskScheduler")
        if TaskScheduler:
            self._scheduler = TaskScheduler(workers=2)
            self._scheduler.start()

        # Initialize merkle chain for sealing
        MerkleChain = _try_import("memory_chain", "MerkleChain")
        if MerkleChain:
            try:
                data_dir = _REPO_ROOT / "03_memory" / "_data" / "memory_chain"
                self._chain = MerkleChain(data_dir)
            except Exception:  # noqa: BLE001
                self._chain = None

        self._initialized = True

    def stop(self, timeout: float = 5.0) -> None:
        """Stop the orchestrator and shut down workers."""
        if self._scheduler:
            self._scheduler.stop(timeout=timeout)
        self._initialized = False

    # ── Task submission ───────────────────────────────────────────────────────

    def submit_task(
        self,
        goal: str,
        task_type: str = "simple",
        priority: int = 5,
        agents: Optional[List[str]] = None,
        meta: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Submit a task to the orchestrator.

        Parameters
        ----------
        goal      : The task objective
        task_type : "simple" | "agent" | "multi_agent"
        priority  : Task priority (1-10, lower = higher urgency)
        agents    : List of agent names (for multi_agent tasks)
        meta      : Additional metadata

        Returns
        -------
        task_id : UUID string
        """
        task_id = str(uuid.uuid4())
        task = OrchestratedTask(
            task_id=task_id,
            goal=goal,
            task_type=task_type,
            status=TaskStatus.QUEUED,
            created_at_ms=int(time.time() * 1000),
            meta=meta or {},
        )

        if agents:
            task.meta["agents"] = agents

        self._tasks[task_id] = task

        # Submit to scheduler
        if self._scheduler:
            def _execute() -> Any:
                return self._execute_task(task_id)

            self._scheduler.submit(
                fn=_execute,
                name=f"task_{task_id[:8]}",
                priority=priority,
            )

        return task_id

    # ── Task execution ────────────────────────────────────────────────────────

    def _execute_task(self, task_id: str) -> Any:
        """Execute a task based on its type."""
        task = self._tasks.get(task_id)
        if not task:
            return {"error": "Task not found"}

        task.status = TaskStatus.RUNNING
        task.started_at_ms = int(time.time() * 1000)

        try:
            if task.task_type == "simple":
                output = self._execute_simple(task)
            elif task.task_type == "agent":
                output = self._execute_agent(task)
            elif task.task_type == "multi_agent":
                output = self._execute_multi_agent(task)
            else:
                output = {"error": f"Unknown task type: {task.task_type}"}

            task.output = output
            task.status = TaskStatus.DONE

        except Exception as exc:  # noqa: BLE001
            task.error = f"{type(exc).__name__}: {exc}"
            task.error_trace = traceback.format_exc()
            task.status = TaskStatus.FAILED
            task.output = None

        finally:
            task.ended_at_ms = int(time.time() * 1000)
            if task.started_at_ms:
                task.elapsed_ms = task.ended_at_ms - task.started_at_ms

        return task.to_dict()

    def _execute_simple(self, task: OrchestratedTask) -> Dict[str, Any]:
        """Execute a simple task (stub for now)."""
        return {
            "task_id": task.task_id,
            "goal": task.goal,
            "result": f"[Stub] Completed: {task.goal}",
        }

    def _execute_agent(self, task: OrchestratedTask) -> Dict[str, Any]:
        """Execute a single agent task."""
        # Wire to actual agent planner in production
        return {
            "task_id": task.task_id,
            "goal": task.goal,
            "result": f"[Agent stub] Analyzed: {task.goal}",
        }

    def _execute_multi_agent(self, task: OrchestratedTask) -> Dict[str, Any]:
        """Execute a multi-agent coordinated task."""
        MultiAgentSession = _try_import("multi_agent", "MultiAgentSession")
        AgentRole = _try_import("multi_agent", "AgentRole")

        if not MultiAgentSession or not AgentRole:
            return {"error": "MultiAgentSession unavailable"}

        agents = task.meta.get("agents", [])
        session = MultiAgentSession(goal=task.goal)

        # Create default roles
        for agent_name in agents:
            role = AgentRole(
                name=agent_name,
                system_prompt=f"You are {agent_name}, helping to accomplish: {task.goal}",
            )
            session.add_role(role)

        # Execute sequentially
        results = session.run_sequential()

        return {
            "task_id": task.task_id,
            "goal": task.goal,
            "session_id": session.session_id,
            "agent_results": results,
            "summary": session.summary(),
        }

    # ── Task query ────────────────────────────────────────────────────────────

    def get_task(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get task status and result."""
        task = self._tasks.get(task_id)
        if task:
            return task.to_dict()
        return None

    def wait_for_task(
        self,
        task_id: str,
        timeout: float = 30.0,
        poll_interval: float = 0.1,
    ) -> Optional[Dict[str, Any]]:
        """Block until task reaches terminal state or timeout."""
        deadline = time.time() + timeout
        while time.time() < deadline:
            task = self._tasks.get(task_id)
            if task and task.status in (TaskStatus.DONE, TaskStatus.FAILED, TaskStatus.SEALED):
                return task.to_dict()
            time.sleep(poll_interval)
        return self.get_task(task_id)

    def list_tasks(
        self,
        status_filter: Optional[TaskStatus] = None,
    ) -> List[Dict[str, Any]]:
        """List all tasks, optionally filtered by status."""
        tasks = list(self._tasks.values())
        if status_filter:
            tasks = [t for t in tasks if t.status == status_filter]
        return [t.to_dict() for t in sorted(tasks, key=lambda t: t.created_at_ms)]

    # ── Task sealing ──────────────────────────────────────────────────────────

    def seal_task(self, task_id: str) -> Dict[str, Any]:
        """
        Seal a task result to the merkle chain.

        Parameters
        ----------
        task_id : UUID of the task to seal

        Returns
        -------
        Seal record with merkle entry details
        """
        task = self._tasks.get(task_id)
        if not task:
            return {"error": "Task not found"}

        if task.status not in (TaskStatus.DONE, TaskStatus.FAILED):
            return {"error": f"Cannot seal task in status: {task.status.value}"}

        if not self._chain:
            return {"error": "MerkleChain unavailable"}

        # Create seal payload
        payload = {
            "task_id": task.task_id,
            "goal": task.goal,
            "status": task.status.value,
            "output": task.output,
            "error": task.error,
            "elapsed_ms": task.elapsed_ms,
            "created_at_ms": task.created_at_ms,
            "sealed_at_ms": int(time.time() * 1000),
        }

        try:
            entry = self._chain.append(
                payload=payload,
                tags=["task_seal", task.task_type],
                layer="L7_LOOP",
                meta={"task_id": task_id},
            )

            seal_record = {
                "entry_id": entry["entry_id"],
                "merkle_hash": entry["merkle"],
                "sealed_at_ms": entry["timestamp_ms"],
                "origin_signature": ORIGIN_SIGNATURE,
            }

            task.seal_record = seal_record
            task.status = TaskStatus.SEALED

            return seal_record

        except Exception as exc:  # noqa: BLE001
            return {"error": f"Seal failed: {exc}"}


# ─── CLI ─────────────────────────────────────────────────────────────────────

_GLOBAL_ORCH: Optional[TaskOrchestrator] = None


def _get_orch() -> TaskOrchestrator:
    global _GLOBAL_ORCH
    if _GLOBAL_ORCH is None:
        _GLOBAL_ORCH = TaskOrchestrator()
        _GLOBAL_ORCH.start()
    return _GLOBAL_ORCH


def _cmd_submit(args: argparse.Namespace) -> None:
    orch = _get_orch()
    task_id = orch.submit_task(
        goal=args.goal,
        task_type=args.type,
        priority=args.priority,
        agents=args.agents.split(",") if args.agents else None,
    )
    print(f"Task submitted: {task_id}")
    if args.wait:
        print("Waiting for completion...")
        result = orch.wait_for_task(task_id, timeout=args.timeout)
        print(json.dumps(result, ensure_ascii=False, indent=2))


def _cmd_status(args: argparse.Namespace) -> None:
    orch = _get_orch()
    result = orch.get_task(args.task_id)
    if result:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(f"Task not found: {args.task_id}")


def _cmd_seal(args: argparse.Namespace) -> None:
    orch = _get_orch()
    seal_record = orch.seal_task(args.task_id)
    print(json.dumps(seal_record, ensure_ascii=False, indent=2))


def _cmd_list(args: argparse.Namespace) -> None:
    orch = _get_orch()
    status_filter = TaskStatus(args.status) if args.status else None
    tasks = orch.list_tasks(status_filter=status_filter)
    print(f"Total tasks: {len(tasks)}")
    for task in tasks:
        print(f"  {task['task_id'][:8]}…  {task['status']:12s}  {task['goal'][:60]}")


def _build_argparser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="MRL_task_orchestrator — Production task orchestration"
    )
    sub = p.add_subparsers(dest="cmd", required=True)

    # submit
    s = sub.add_parser("submit", help="Submit a new task")
    s.add_argument("--goal", required=True, help="Task objective")
    s.add_argument("--type", default="simple", choices=["simple", "agent", "multi_agent"])
    s.add_argument("--priority", type=int, default=5)
    s.add_argument("--agents", help="Comma-separated agent names (for multi_agent)")
    s.add_argument("--wait", action="store_true", help="Wait for completion")
    s.add_argument("--timeout", type=float, default=30.0)

    # status
    st = sub.add_parser("status", help="Get task status")
    st.add_argument("--task-id", required=True)

    # seal
    se = sub.add_parser("seal", help="Seal task to merkle chain")
    se.add_argument("--task-id", required=True)

    # list
    l = sub.add_parser("list", help="List tasks")
    l.add_argument("--status", choices=[s.value for s in TaskStatus])

    return p


def main() -> None:
    parser = _build_argparser()
    args = parser.parse_args()
    dispatch = {
        "submit": _cmd_submit,
        "status": _cmd_status,
        "seal": _cmd_seal,
        "list": _cmd_list,
    }
    dispatch[args.cmd](args)


if __name__ == "__main__":
    main()