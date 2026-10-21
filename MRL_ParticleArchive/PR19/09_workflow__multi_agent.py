#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
multi_agent.py — Multi-Agent Coordination Framework
origin_signature: MrLiouWord
layer: L7 LOOP
group: Y=3 FlowAgentRuntime

Industry capability: multi-agent task decomposition and coordination —
                     the pattern powering AutoGen, CrewAI, and similar
                     frameworks seen across the three major AI ecosystems.
MRL extension: agent roles, tasks, and inter-agent messages are all stamped
               with origin_signature and are WorldModule-trajectory-compatible.

Architecture
------------
  AgentRole         — named agent with a system prompt and tool set
  AgentMessage      — typed communication envelope between agents
  MultiAgentSession — orchestrates a group of agents on a shared goal
  Orchestrator      — decomposes goals into sub-tasks and assigns to agents

Usage (library)
---------------
    from multi_agent import MultiAgentSession, AgentRole

    planner = AgentRole("planner", system_prompt="Decompose the goal into sub-tasks.")
    coder   = AgentRole("coder",   system_prompt="Implement the given sub-task.")

    session = MultiAgentSession(goal="Build a hello-world program.")
    session.add_role(planner)
    session.add_role(coder)

    results = session.run_sequential()
    for r in results:
        print(r["agent"], "->", r["output"][:80])

CLI
---
    python 09_workflow/multi_agent.py demo
    python 09_workflow/multi_agent.py roles
"""

from __future__ import annotations

import argparse
import json
import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional

ORIGIN_SIGNATURE = "MrLiouWord"

# Type alias for a simple agent execution function
AgentFn = Callable[["AgentContext"], str]


# ─── AgentRole ───────────────────────────────────────────────────────────────

@dataclass
class AgentRole:
    """
    Declares an agent's identity, instructions, and capabilities.

    Fields
    ------
    name          : unique agent identifier within the session
    system_prompt : instructions for this agent's behaviour
    tools         : list of tool names this agent is allowed to call
    max_steps     : max ReAct iterations for this agent (default 10)
    meta          : arbitrary metadata dict
    """

    name: str
    system_prompt: str = ""
    tools: List[str] = field(default_factory=list)
    max_steps: int = 10
    meta: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "system_prompt": self.system_prompt,
            "tools": self.tools,
            "max_steps": self.max_steps,
            "meta": self.meta,
            "origin_signature": ORIGIN_SIGNATURE,
        }


# ─── AgentMessage ─────────────────────────────────────────────────────────────

@dataclass
class AgentMessage:
    """
    A typed communication envelope between agents.

    msg_type values
    ---------------
    task       — assign a task to an agent
    result     — agent returning its output
    handoff    — transferring control to another agent
    broadcast  — message to all agents
    """

    sender: str
    recipient: str
    content: str
    msg_type: str = "task"
    msg_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    ts_ms: int = field(default_factory=lambda: int(time.time() * 1000))
    meta: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "msg_id": self.msg_id,
            "sender": self.sender,
            "recipient": self.recipient,
            "content": self.content,
            "msg_type": self.msg_type,
            "ts_ms": self.ts_ms,
            "meta": self.meta,
            "origin_signature": ORIGIN_SIGNATURE,
        }


# ─── AgentContext ─────────────────────────────────────────────────────────────

@dataclass
class AgentContext:
    """
    Runtime context passed to an agent's execution function.

    Contains the agent's role, the current task, shared memory,
    the message inbox, and the full session goal.
    """

    role: AgentRole
    task: str
    goal: str
    inbox: List[AgentMessage] = field(default_factory=list)
    shared_memory: Dict[str, Any] = field(default_factory=dict)
    session_id: str = ""


# ─── MultiAgentSession ───────────────────────────────────────────────────────

class MultiAgentSession:
    """
    Coordinates multiple agents on a shared goal.

    Agents can run sequentially (passing outputs forward as context) or
    in a round-robin coordination loop.

    Parameters
    ----------
    goal       : str
        The top-level objective for all agents.
    session_id : str
        Auto-generated if not provided.
    """

    def __init__(self, goal: str, session_id: Optional[str] = None) -> None:
        self.goal = goal
        self.session_id = session_id or str(uuid.uuid4())
        self._roles: List[AgentRole] = []
        self._fns: Dict[str, AgentFn] = {}
        self._messages: List[AgentMessage] = []
        self._results: List[Dict[str, Any]] = []
        self._shared: Dict[str, Any] = {}
        self._created_at_ms = int(time.time() * 1000)

    # ── Setup ─────────────────────────────────────────────────────────────────

    def add_role(
        self,
        role: AgentRole,
        fn: Optional[AgentFn] = None,
    ) -> "MultiAgentSession":
        """
        Register an agent role.

        Parameters
        ----------
        role : AgentRole
        fn   : optional execution function ``(ctx: AgentContext) -> str``.
               If not provided, a default stub function is used that
               acknowledges the task and returns a placeholder answer.
        """
        self._roles.append(role)
        self._fns[role.name] = fn or _default_agent_fn
        return self

    # ── Execution ─────────────────────────────────────────────────────────────

    def run_sequential(
        self,
        tasks: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Run agents sequentially: each agent receives the previous agent's
        output as additional context.

        Parameters
        ----------
        tasks : optional list of per-agent task strings.
                If not provided, each agent receives the shared goal.

        Returns
        -------
        List of result records, one per agent.
        """
        if not self._roles:
            return []

        results: List[Dict[str, Any]] = []
        previous_output = ""

        for i, role in enumerate(self._roles):
            task = (tasks[i] if tasks and i < len(tasks) else self.goal)
            if previous_output:
                task = f"{task}\n\nPrevious agent output:\n{previous_output}"

            ctx = AgentContext(
                role=role,
                task=task,
                goal=self.goal,
                inbox=[m for m in self._messages if m.recipient in (role.name, "all")],
                shared_memory=self._shared,
                session_id=self.session_id,
            )

            t0 = time.time()
            try:
                output = self._fns[role.name](ctx)
                ok = True
                error = None
            except Exception as exc:  # noqa: BLE001
                output = ""
                ok = False
                error = f"{type(exc).__name__}: {exc}"

            elapsed = int((time.time() - t0) * 1000)

            rec: Dict[str, Any] = {
                "agent": role.name,
                "task": task,
                "output": output,
                "ok": ok,
                "error": error,
                "elapsed_ms": elapsed,
                "ts_ms": int(time.time() * 1000),
                "session_id": self.session_id,
                "origin_signature": ORIGIN_SIGNATURE,
            }
            results.append(rec)
            self._results.append(rec)
            previous_output = output

            # Post output as a result message
            msg = AgentMessage(
                sender=role.name,
                recipient="orchestrator",
                content=output,
                msg_type="result",
            )
            self._messages.append(msg)

        return results

    def run_round_robin(
        self,
        rounds: int = 3,
        task: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Run agents in a round-robin conversation for *rounds* iterations.

        Each agent reads all previous messages and adds its own response.

        Returns
        -------
        List of result records (rounds × agents entries).
        """
        results: List[Dict[str, Any]] = []
        base_task = task or self.goal

        for round_num in range(rounds):
            for role in self._roles:
                inbox = list(self._messages)
                context_text = "\n".join(
                    f"[{m.sender}]: {m.content}" for m in inbox[-10:]
                )
                full_task = (
                    f"Round {round_num + 1}/{rounds}\n"
                    f"Goal: {base_task}\n\n"
                    f"Recent conversation:\n{context_text}"
                )

                ctx = AgentContext(
                    role=role,
                    task=full_task,
                    goal=self.goal,
                    inbox=inbox,
                    shared_memory=self._shared,
                    session_id=self.session_id,
                )

                t0 = time.time()
                try:
                    output = self._fns[role.name](ctx)
                    ok = True
                    error = None
                except Exception as exc:  # noqa: BLE001
                    output = ""
                    ok = False
                    error = f"{type(exc).__name__}: {exc}"

                rec = {
                    "agent": role.name,
                    "round": round_num + 1,
                    "output": output,
                    "ok": ok,
                    "error": error,
                    "elapsed_ms": int((time.time() - t0) * 1000),
                    "ts_ms": int(time.time() * 1000),
                    "session_id": self.session_id,
                    "origin_signature": ORIGIN_SIGNATURE,
                }
                results.append(rec)
                self._results.append(rec)

                # Broadcast the response so subsequent agents see it
                msg = AgentMessage(
                    sender=role.name,
                    recipient="all",
                    content=output,
                    msg_type="broadcast",
                )
                self._messages.append(msg)

        return results

    # ── Query ─────────────────────────────────────────────────────────────────

    def summary(self) -> Dict[str, Any]:
        return {
            "session_id": self.session_id,
            "goal": self.goal,
            "agents": [r.name for r in self._roles],
            "total_results": len(self._results),
            "total_messages": len(self._messages),
            "created_at_ms": self._created_at_ms,
            "origin_signature": ORIGIN_SIGNATURE,
        }

    def all_results(self) -> List[Dict[str, Any]]:
        return list(self._results)

    def message_log(self) -> List[Dict[str, Any]]:
        return [m.to_dict() for m in self._messages]


# ─── Default agent function ──────────────────────────────────────────────────

def _default_agent_fn(ctx: AgentContext) -> str:
    """
    Stub agent function: acknowledges the task and returns a structured reply.
    Replace this with a real LLM call in production.
    """
    return (
        f"[{ctx.role.name}] Received task: {ctx.task[:100]}\n"
        f"System: {ctx.role.system_prompt[:80]}\n"
        f"Shared memory keys: {list(ctx.shared_memory.keys())}\n"
        f"(stub response — wire a real LLM via LLMGateway to replace this)"
    )


# ─── CLI ─────────────────────────────────────────────────────────────────────

def _cmd_demo(_args: argparse.Namespace) -> None:
    planner = AgentRole("planner", system_prompt="Decompose the goal into concrete sub-tasks.")
    researcher = AgentRole("researcher", system_prompt="Research each sub-task and gather information.")
    writer = AgentRole("writer", system_prompt="Synthesise the research into a clear answer.")

    sess = MultiAgentSession(goal="Explain what the MRL AI System does.")
    sess.add_role(planner)
    sess.add_role(researcher)
    sess.add_role(writer)

    results = sess.run_sequential()
    print(json.dumps(results, ensure_ascii=False, indent=2))
    print("\n=== Summary ===")
    print(json.dumps(sess.summary(), ensure_ascii=False, indent=2))


def _cmd_roles(_args: argparse.Namespace) -> None:
    roles = [
        AgentRole("planner",    "Decompose goals into sub-tasks."),
        AgentRole("researcher", "Gather facts relevant to the task."),
        AgentRole("writer",     "Compose the final answer."),
        AgentRole("critic",     "Review and improve the answer."),
        AgentRole("executor",   "Execute concrete actions (tool calls)."),
    ]
    print("Built-in agent role templates:")
    for r in roles:
        print(json.dumps(r.to_dict(), ensure_ascii=False, indent=2))


def _build_argparser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="multi_agent — multi-agent coordination")
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("demo", help="Run a 3-agent sequential demo")
    sub.add_parser("roles", help="List built-in agent role templates")
    return p


def main() -> None:
    parser = _build_argparser()
    args = parser.parse_args()
    dispatch = {"demo": _cmd_demo, "roles": _cmd_roles}
    dispatch[args.cmd](args)


if __name__ == "__main__":
    main()