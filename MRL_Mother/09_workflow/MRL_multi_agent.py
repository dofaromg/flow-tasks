#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MRL_multi_agent.py — Multi-Agent Orchestrator & Coordination Framework
origin_signature: MrLiouWord
layer: L7 LOOP
group: Y=3 MrLiouAIRuntime

Goal: product-level local multi-agent orchestration — zero external
      dependencies, pure Python stdlib only.

Concepts
--------
Agent
    A named participant with a system prompt, an optional tool registry,
    and an attached LLMGateway.  Agents produce responses given a message
    list (their "view" of the conversation so far).

HumanProxyAgent
    Special agent that blocks on stdin (or raises HumanInputRequired) when
    the conversation requires a human decision — enforcing the MRL
    REQUIRE_HUMAN policy.

GroupChat
    A shared message bus.  Manages speaker selection (round-robin or
    auto/LLM-driven) and the turn loop.

GroupChatManager
    Runs the GroupChat loop up to max_turns; emits a structured transcript.

Message format
--------------
    {
      "turn":             int,
      "from_agent":       str,
      "to_agent":         str | "all",
      "role":             "user" | "assistant" | "system",
      "content":          str,
      "ts_ms":            int,
      "origin_signature": "MrLiouWord",
    }

Usage (library)
---------------
    from llm_gateway import LLMGateway
    from multi_agent import Agent, HumanProxyAgent, GroupChat, GroupChatManager

    gw = LLMGateway()   # auto-detects local backend

    planner = Agent("Planner", gw,
                    system_prompt="You decompose tasks into steps.")
    executor = Agent("Executor", gw,
                     system_prompt="You execute one step at a time.")
    human   = HumanProxyAgent("Human")

    gc = GroupChat([planner, executor, human], max_turns=6)
    mgr = GroupChatManager(gc)

    transcript = mgr.run("Build a local file index of the repo.")
    for msg in transcript["messages"]:
        print(f"[{msg['from_agent']}] {msg['content'][:80]}")
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
    from MRL_multi_agent import MultiAgentSession, AgentRole

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
    python 09_workflow/MRL_multi_agent.py demo
    python 09_workflow/MRL_multi_agent.py run --goal "Summarise this repo" --agents Planner,Executor
    python 09_workflow/MRL_multi_agent.py roles
"""

from __future__ import annotations

import argparse
import json
import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional

from MRL_utils import ORIGIN_SIGNATURE
MULTI_AGENT_VERSION = "1.0"

# Type alias used by MultiAgentSession
AgentFn = Callable[["AgentContext"], str]

# ─── Exceptions ───────────────────────────────────────────────────────────────

class HumanInputRequired(Exception):
    """Raised when a HumanProxyAgent needs interactive input but none is available."""


# ─── Message helpers ──────────────────────────────────────────────────────────

def _make_msg(
    turn: int,
    from_agent: str,
    to_agent: str,
    role: str,
    content: str,
) -> Dict[str, Any]:
    return {
        "turn":             turn,
        "from_agent":       from_agent,
        "to_agent":         to_agent,
        "role":             role,
        "content":          content,
        "ts_ms":            int(time.time() * 1000),
        "origin_signature": ORIGIN_SIGNATURE,
    }


# ─── Agent ────────────────────────────────────────────────────────────────────

class Agent:
    """
    A named participant in a group chat backed by a local LLMGateway.

    Parameters
    ----------
    name : str
        Unique agent identifier within the group.
    gateway : any
        LLMGateway instance (or None → stub replies).
    system_prompt : str
        System-level instruction for this agent.
    max_tokens : int
        Per-reply token budget.
    temperature : float
    """

    def __init__(
        self,
        name: str,
        gateway: Any = None,
        *,
        system_prompt: str = "",
        max_tokens: int = 512,
        temperature: float = 0.7,
    ) -> None:
        self.name = name
        self._gateway = gateway
        self._system_prompt = system_prompt or f"You are {name}, a helpful AI agent."
        self._max_tokens = max_tokens
        self._temperature = temperature
        self.is_human = False

    def reply(
        self,
        history: List[Dict[str, Any]],
        *,
        sender: str = "user",
    ) -> str:
        """
        Produce a reply given the shared message history.

        The history is converted to an LLM-compatible message list:
        system prompt first, then the conversation chronologically.
        """
        messages: List[Dict[str, str]] = [
            {"role": "system", "content": self._system_prompt}
        ]
        for msg in history:
            # Map to standard roles understood by LLMs
            role = msg.get("role", "user")
            if role not in ("system", "user", "assistant"):
                role = "user"
            messages.append({"role": role, "content": msg["content"]})

        if self._gateway is not None:
            resp = self._gateway.chat(
                messages,
                max_tokens=self._max_tokens,
                temperature=self._temperature,
            )
            return resp.get("text", "")

        # No gateway — minimal stub
        last = history[-1]["content"][:80] if history else ""
        return f"[{self.name} stub] Received: {last!r}"

    def __repr__(self) -> str:
        return f"Agent(name={self.name!r})"


# ─── HumanProxyAgent ──────────────────────────────────────────────────────────

class HumanProxyAgent:
    """
    A human participant.  When interactive=True (default), blocks on stdin.
    When interactive=False, raises HumanInputRequired (useful in CI / tests).

    MRL policy: REQUIRE_HUMAN decisions must flow through this agent so they
    are visible in the transcript and can be traced to the Merkle chain.
    """

    def __init__(
        self,
        name: str = "Human",
        *,
        interactive: bool = True,
        auto_reply: Optional[str] = None,
    ) -> None:
        self.name = name
        self._interactive = interactive
        self._auto_reply = auto_reply
        self.is_human = True

    def reply(
        self,
        history: List[Dict[str, Any]],
        *,
        sender: str = "user",
    ) -> str:
        if self._auto_reply is not None:
            return self._auto_reply

        if not self._interactive:
            last = history[-1]["content"][:120] if history else ""
            raise HumanInputRequired(
                f"Human input required — last message: {last!r}"
            )

        # Interactive: prompt on stdin
        last_content = history[-1]["content"] if history else ""
        print(f"\n[{sender} → {self.name}] {last_content}")
        try:
            response = input(f"[{self.name}] Your reply: ").strip()
        except EOFError:
            response = "[Human: no input available]"
        return response

    def __repr__(self) -> str:
        return f"HumanProxyAgent(name={self.name!r})"


# ─── GroupChat ────────────────────────────────────────────────────────────────

SpeakerFn = Callable[[List[Dict[str, Any]], List[Any]], Any]


def _round_robin(
    history: List[Dict[str, Any]],
    agents: List[Any],
    *,
    include_human: bool = False,
) -> Any:
    """Default speaker selector: cycle through agents.

    When *include_human* is False (default), HumanProxyAgents are skipped.
    When *include_human* is True all agents — including human proxies — are
    included in the rotation so that REQUIRE_HUMAN flows can be scheduled.
    """
    pool = agents if include_human else [a for a in agents if not getattr(a, "is_human", False)]
    if not pool:
        pool = agents  # fallback: never return nothing
    last_speaker = history[-1].get("from_agent", "") if history else ""
    idx = next(
        (i for i, a in enumerate(pool) if a.name == last_speaker),
        -1,
    )
    return pool[(idx + 1) % len(pool)]


class GroupChat:
    """
    Shared message bus for a multi-agent conversation.

    Parameters
    ----------
    agents : list
        Mix of Agent and HumanProxyAgent instances.
    max_turns : int
        Hard upper bound on the total number of turns.
    speaker_fn : callable | None
        ``(history, agents) -> agent`` — custom speaker selection.
        Default = round-robin (respects *include_human_proxy*).
    include_human_proxy : bool
        When True, HumanProxyAgent instances are included in the default
        round-robin rotation so that REQUIRE_HUMAN flows can be scheduled.
        Has no effect when a custom *speaker_fn* is provided.
    """

    def __init__(
        self,
        agents: List[Any],
        max_turns: int = 10,
        speaker_fn: Optional[SpeakerFn] = None,
        include_human_proxy: bool = False,
    ) -> None:
        if not agents:
            raise ValueError("GroupChat: agents list must not be empty")
        self.agents = agents
        self.max_turns = max_turns
        self.include_human_proxy = include_human_proxy
        if speaker_fn is not None:
            self._speaker_fn = speaker_fn
        else:
            _include = include_human_proxy
            self._speaker_fn = lambda h, a: _round_robin(h, a, include_human=_include)
        self._messages: List[Dict[str, Any]] = []
        self._turn = 0
        self._agent_map: Dict[str, Any] = {a.name: a for a in agents}

    def agent(self, name: str) -> Any:
        return self._agent_map.get(name)

    def messages(self) -> List[Dict[str, Any]]:
        return list(self._messages)

    def inject(self, from_agent: str, content: str, role: str = "user") -> None:
        """Inject an initial message into the chat (e.g., the task description)."""
        msg = _make_msg(self._turn, from_agent, "all", role, content)
        self._messages.append(msg)

    def next_speaker(self) -> Any:
        return self._speaker_fn(self._messages, self.agents)

    def step(self) -> Optional[Dict[str, Any]]:
        """Execute one turn.  Returns the new message or None if max_turns reached."""
        if self._turn >= self.max_turns:
            return None

        speaker = self.next_speaker()
        prev_speaker = (
            self._messages[-1].get("from_agent", "") if self._messages else ""
        )

        try:
            content = speaker.reply(self._messages, sender=prev_speaker)
        except HumanInputRequired:
            raise
        except Exception as exc:
            content = f"[{speaker.name} error: {exc}]"

        role = "user" if getattr(speaker, "is_human", False) else "assistant"
        msg = _make_msg(self._turn, speaker.name, "all", role, content)
        self._messages.append(msg)
        self._turn += 1
        return msg


# ─── GroupChatManager ─────────────────────────────────────────────────────────

class GroupChatManager:
    """
    Runs a GroupChat for up to max_turns, collecting the transcript.

    Parameters
    ----------
    group_chat : GroupChat
    terminate_fn : callable | None
        ``(messages) -> bool`` — return True to stop early.
        Default = stop when the last message contains "TERMINATE".
    """

    def __init__(
        self,
        group_chat: GroupChat,
        terminate_fn: Optional[Callable[[List[Dict[str, Any]]], bool]] = None,
    ) -> None:
        self._gc = group_chat
        self._terminate_fn = terminate_fn or self._default_terminate

    @staticmethod
    def _default_terminate(messages: List[Dict[str, Any]]) -> bool:
        if not messages:
            return False
        last = messages[-1].get("content", "")
        return "TERMINATE" in last.upper()

    def run(
        self,
        task: str,
        *,
        initiator: str = "Human",
    ) -> Dict[str, Any]:
        """
        Run the group chat for *task*.

        Returns
        -------
        {
          "task":             str,
          "total_turns":      int,
          "terminated_early": bool,
          "messages":         [msg, ...],
          "started_at_ms":    int,
          "ended_at_ms":      int,
          "origin_signature": "MrLiouWord",
        }
        """
        started = int(time.time() * 1000)

        # Seed the conversation with the task
        self._gc.inject(initiator, task, role="user")

        terminated_early = False

        for _ in range(self._gc.max_turns):
            msg = self._gc.step()
            if msg is None:
                break
            if self._terminate_fn(self._gc.messages()):
                terminated_early = True
                break

        return {
            "task":             task,
            "total_turns":      self._gc._turn,
            "terminated_early": terminated_early,
            "messages":         self._gc.messages(),
            "started_at_ms":    started,
            "ended_at_ms":      int(time.time() * 1000),
            "origin_signature": ORIGIN_SIGNATURE,
        }


# ─── CLI demo ─────────────────────────────────────────────────────────────────

def _demo() -> None:
    """Two-agent stub demo (no LLM required)."""

    planner = Agent(
        "Planner",
        gateway=None,
        system_prompt="You break tasks into numbered steps.",
    )
    executor = Agent(
        "Executor",
        gateway=None,
        system_prompt="You confirm steps are done and report results.",
    )
    human = HumanProxyAgent("Human", interactive=False, auto_reply="Looks good. TERMINATE")

    gc = GroupChat([planner, executor, human], max_turns=6)
    mgr = GroupChatManager(gc)

    transcript = mgr.run("Index all Python files in the repository.")

    print(json.dumps(transcript, ensure_ascii=False, indent=2, default=str))


def _cmd_group_chat_demo(_args: argparse.Namespace) -> None:
    """Demo using the Group Chat API (Agent/HumanProxyAgent/GroupChat)."""
    _demo()


def _cmd_run(args: argparse.Namespace) -> None:
    """Run a group chat with named stub agents from the CLI."""
    names = [n.strip() for n in (args.agents or "Planner,Executor").split(",")]
    agents = [Agent(n, gateway=None) for n in names]
    agents.append(HumanProxyAgent("Human", interactive=False, auto_reply="TERMINATE"))

    gc = GroupChat(agents, max_turns=args.max_turns)
    mgr = GroupChatManager(gc)
    result = mgr.run(args.goal)
    print(json.dumps(result, ensure_ascii=False, indent=2, default=str))


# ─── AgentRole / AgentMessage / AgentContext / MultiAgentSession ─────────────
# Legacy sequential-API (compatible with MotherAssembly.run_multi_agent)

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
    p = argparse.ArgumentParser(
        description="MRL_multi_agent — multi-agent orchestration (group-chat + sequential)"
    )
    sub = p.add_subparsers(dest="cmd", required=True)

    sub.add_parser("demo",       help="Run a sequential demo using AgentRole/MultiAgentSession")
    sub.add_parser("group-chat", help="Run the built-in two-agent group-chat demo")
    sub.add_parser("roles",      help="List built-in agent role templates")

    r = sub.add_parser("run", help="Run a group chat with named stub agents")
    r.add_argument("--goal",      required=True, help="Task description")
    r.add_argument("--agents",    default="Planner,Executor",
                   help="Comma-separated agent names (all stub)")
    r.add_argument("--max-turns", type=int, default=6, dest="max_turns")

    return p


def main() -> None:
    parser = _build_argparser()
    args = parser.parse_args()
    dispatch = {
        "demo":       _cmd_demo,
        "group-chat": _cmd_group_chat_demo,
        "run":        _cmd_run,
        "roles":      _cmd_roles,
    }
    dispatch[args.cmd](args)


if __name__ == "__main__":
    main()
