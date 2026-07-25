#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
agent_planner.py — ReAct-Style Plan → Act → Observe Agent Loop
origin_signature: MrLiouWord
layer: L7 LOOP
group: Y=3 MrLiouAIRuntime

Industry capability: ReAct (Reasoning + Acting) agent loop.
MRL extension: every step is recorded as a trajectory entry compatible with
               the WorldModule trajectory format and MerkleChain payload.

The agent alternates between three step types:

  THINK   — reason about the current state and decide next action
  ACT     — invoke a tool from the ToolRegistry
  OBSERVE — record the tool output and decide whether to continue or stop

A session runs until the agent emits a FINISH action or the step limit is
reached (preventing infinite loops, following L3 LAW ring-buffer logic).

Usage (library)
---------------
    from tool_registry import ToolRegistry
    from agent_planner import AgentPlanner, ThinkFn

    registry = ToolRegistry()
    # ... register tools ...

    def my_think(state) -> dict:
        # Decide: {"action": "add", "args": {"a": 1, "b": 2}}
        # or finish: {"action": "__finish__", "args": {"answer": "done"}}
        ...

    planner = AgentPlanner(registry, think_fn=my_think, max_steps=10)
    result = planner.run("What is 3 + 4?")
    print(result["answer"])

CLI
---
    python 09_workflow/agent_planner.py demo
"""

from __future__ import annotations

import json
import time
from typing import Any, Callable, Dict, List, Optional

ORIGIN_SIGNATURE = "MrLiouWord"
FINISH_ACTION = "__finish__"

# Type alias for the user-supplied reasoning function
ThinkFn = Callable[[Dict[str, Any]], Dict[str, Any]]


# ─── Step record ─────────────────────────────────────────────────────────────

def _make_step(
    step_num: int,
    step_type: str,
    content: Any,
    *,
    tool: Optional[str] = None,
    tool_result: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    return {
        "step": step_num,
        "type": step_type,            # "think" | "act" | "observe" | "finish"
        "content": content,
        "tool": tool,
        "tool_result": tool_result,
        "ts_ms": int(time.time() * 1000),
        "origin_signature": ORIGIN_SIGNATURE,
    }


# ─── AgentPlanner ─────────────────────────────────────────────────────────────

class AgentPlanner:
    """
    Minimal ReAct-style plan-act-observe loop.

    Parameters
    ----------
    tool_registry : ToolRegistry
        Provides ``call(name, kwargs)`` for tool invocation.
    think_fn : ThinkFn
        Pure function ``(state: dict) -> dict`` that receives the current
        agent state and returns a decision dict::

            {
              "thought": "<optional reasoning text>",
              "action":  "<tool_name or '__finish__'>",
              "args":    {<tool kwargs or final answer dict>}
            }

    max_steps : int
        Hard limit on total iterations (LAW-ring-buffer safety valve).
        Default = 20.
    """

    def __init__(
        self,
        tool_registry: Any,
        think_fn: ThinkFn,
        max_steps: int = 20,
    ) -> None:
        self._registry = tool_registry
        self._think = think_fn
        self._max_steps = max_steps

    def run(
        self,
        goal: str,
        initial_context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Execute the plan-act-observe loop for *goal*.

        Returns
        -------
        {
          "goal":         <str>,
          "answer":       <Any>,        # value from __finish__ args
          "steps":        [step, ...],
          "total_steps":  <int>,
          "finished":     True | False, # False = hit step limit
          "started_at_ms":<int>,
          "ended_at_ms":  <int>,
          "origin_signature": "MrLiouWord",
        }
        """
        started = int(time.time() * 1000)
        steps: List[Dict[str, Any]] = []
        observations: List[Dict[str, Any]] = []
        finished = False
        answer: Any = None

        state: Dict[str, Any] = {
            "goal": goal,
            "context": dict(initial_context or {}),
            "observations": observations,
            "step": 0,
        }

        for i in range(self._max_steps):
            state["step"] = i

            # ── THINK ────────────────────────────────────────────────────────
            decision = self._think(state)
            thought = decision.get("thought", "")
            action = decision.get("action", FINISH_ACTION)
            args = decision.get("args", {})

            steps.append(_make_step(i, "think", thought))

            # ── ACT ──────────────────────────────────────────────────────────
            if action == FINISH_ACTION:
                answer = args.get("answer")
                steps.append(_make_step(i, "finish", answer))
                finished = True
                break

            steps.append(_make_step(i, "act", action, tool=action))

            # ── OBSERVE ──────────────────────────────────────────────────────
            tool_result = self._registry.call(action, args)
            obs = {
                "step": i,
                "tool": action,
                "ok": tool_result.get("ok", False),
                "output": tool_result.get("output"),
                "error": tool_result.get("error"),
            }
            observations.append(obs)
            steps.append(
                _make_step(i, "observe", obs["output"], tool=action, tool_result=tool_result)
            )

        return {
            "goal": goal,
            "answer": answer,
            "steps": steps,
            "total_steps": len(steps),
            "finished": finished,
            "started_at_ms": started,
            "ended_at_ms": int(time.time() * 1000),
            "origin_signature": ORIGIN_SIGNATURE,
        }


# ─── CLI demo ─────────────────────────────────────────────────────────────────

def _demo() -> None:
    """
    Self-contained demo: agent adds two numbers using the built-in 'add' tool,
    then echoes the result.
    """
    import sys
    sys.path.insert(0, str(__file__).rsplit("/", 1)[0])
    from tool_registry import ToolRegistry

    registry = ToolRegistry()

    @registry.register(description="Add two numbers.", parameters={"a": float, "b": float})
    def add(a: float, b: float) -> float:
        return a + b

    @registry.register(description="Echo a message.", parameters={"message": str})
    def echo(message: str) -> str:
        return message

    # Simple hard-coded think function for the demo
    _plan = [
        {"thought": "I need to add 3 + 4.", "action": "add", "args": {"a": 3.0, "b": 4.0}},
        {"thought": "Got the sum; echo it.", "action": "echo", "args": {"message": "3+4=7"}},
        {"thought": "Done.", "action": FINISH_ACTION, "args": {"answer": "3 + 4 = 7"}},
    ]
    _idx = {"v": 0}

    def _think(_state: Dict[str, Any]) -> Dict[str, Any]:
        step = _idx["v"]
        _idx["v"] += 1
        return _plan[min(step, len(_plan) - 1)]

    planner = AgentPlanner(registry, think_fn=_think, max_steps=10)
    result = planner.run("What is 3 + 4?")
    print(json.dumps(result, ensure_ascii=False, indent=2, default=str))


import argparse as _argparse


def main() -> None:
    p = _argparse.ArgumentParser(description="AgentPlanner — ReAct agent loop demo")
    p.add_argument("cmd", choices=["demo"], help="Run the built-in demo")
    args = p.parse_args()
    if args.cmd == "demo":
        _demo()


if __name__ == "__main__":
    main()
