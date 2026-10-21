#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
mother_assembly.py — MotherAssembly: Unified System Entry Point
origin_signature: MrLiouWord
layer: L7 LOOP
group: Y=1 MotherCore

The MotherAssembly is the crown of the MRL AI System.

    MotherBody = MaxBoundary + MinPacket + ReversibleChain

It combines every industry-standard module (new) with every MRL-specific
core module (existing) into a single, operable assembly that is:

  - fully reversible          (fltnz_parser + memory_chain)
  - self-indexing             (mrl_librarian + vector_store)
  - agent-capable             (tool_registry + agent_planner)
  - prompt-managed            (prompt_template)
  - evaluable                 (eval_engine)
  - extensible                (plugin_manager)
  - world-aware               (world_module)

The combination (組合) is the system's biggest feature.  Every action taken
through the MotherAssembly is:
  1. Signed with origin_signature="MrLiouWord"
  2. Sealed in the MerkleChain (canonical immutable record)
  3. Scored by the EvalPipeline
  4. Stored as a trajectory step in the WorldModule
  5. Searchable via the VectorStore (RAG-ready)

Architecture diagram
--------------------

  ┌─────────────────────────────────────────────────────────┐
  │                    MotherAssembly                        │
  │                                                          │
  │  ┌──────────────┐  ┌──────────────┐  ┌───────────────┐  │
  │  │ ToolRegistry │  │PromptTemplate│  │  EvalPipeline │  │
  │  └──────┬───────┘  └──────┬───────┘  └──────┬────────┘  │
  │         │                 │                  │            │
  │  ┌──────▼─────────────────▼──────────────────▼────────┐  │
  │  │                  AgentPlanner (ReAct)               │  │
  │  └──────────────────────────┬──────────────────────────┘  │
  │                             │                              │
  │  ┌──────────────────────────▼──────────────────────────┐  │
  │  │          MRL Core Assembly (existing)               │  │
  │  │  MerkleChain · WorldModule · FLTNZParser ·          │  │
  │  │  MRL_Librarian · VectorStore · PluginManager        │  │
  │  └─────────────────────────────────────────────────────┘  │
  └─────────────────────────────────────────────────────────┘

Usage (library)
---------------
    from mother_assembly import MotherAssembly

    ma = MotherAssembly()
    ma.boot()

    # Run an agent task
    result = ma.run_agent("Summarise the repo structure")
    print(result["answer"])

    # Evaluate an output
    score = ma.evaluate("The MRL system uses Merkle chains.", keywords=["MRL", "Merkle"])
    print(score["composite"])

    # Render a prompt
    prompt = ma.render_prompt("system_intro", {"name": "FlowAgent"})

    # Seal a text into the reversible chain + merkle log
    trace = ma.seal_text("Hello world", label="test")

CLI
---
    python 09_workflow/mother_assembly.py boot
    python 09_workflow/mother_assembly.py status
    python 09_workflow/mother_assembly.py run   --goal "What is 3 + 4?"
    python 09_workflow/mother_assembly.py eval  --output "Hello MRL" --keywords "MRL"
    python 09_workflow/mother_assembly.py seal  --text "Hello world" --label test
"""

from __future__ import annotations

import argparse
import json
import pathlib
import sys
import time
from typing import Any, Dict, List, Optional

ORIGIN_SIGNATURE = "MrLiouWord"
ASSEMBLY_VERSION = "2.0"

_REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent

# ── Module path resolution ────────────────────────────────────────────────────
# The numeric-prefixed directories are not packages; add them to sys.path.

def _ensure_paths() -> None:
    for sub in [
        _REPO_ROOT / "09_workflow",
        _REPO_ROOT / "03_memory" / "merkle",
        _REPO_ROOT / "03_memory" / "vector",
        _REPO_ROOT / "05_persona",
    ]:
        p = str(sub)
        if p not in sys.path:
            sys.path.insert(0, p)

_ensure_paths()

# ── Lazy imports (graceful degradation if a module is unavailable) ────────────

def _try_import(module: str, attr: str) -> Any:
    try:
        import importlib
        mod = importlib.import_module(module)
        return getattr(mod, attr)
    except Exception:  # noqa: BLE001
        return None


# ─── MotherAssembly ───────────────────────────────────────────────────────────

class MotherAssembly:
    """
    Unified system entry point that wires all MRL modules together.

    Attributes
    ----------
    tool_registry       : ToolRegistry
    template_registry   : TemplateRegistry
    eval_pipeline       : EvalPipeline
    plugin_manager      : PluginManager
    vector_store        : VectorStore
    world               : WorldModule
    chain               : MerkleChain  (canonical immutable record)
    conversation_manager: ConversationManager
    llm_gateway         : LLMGateway
    context_manager     : ContextManager
    scheduler           : TaskScheduler
    config              : ConfigManager
    """

    def __init__(self) -> None:
        self._booted = False
        self.tool_registry: Any = None
        self.template_registry: Any = None
        self.eval_pipeline: Any = None
        self.plugin_manager: Any = None
        self.vector_store: Any = None
        self.world: Any = None
        self.chain: Any = None
        # New modules (v2.0)
        self.conversation_manager: Any = None
        self.llm_gateway: Any = None
        self.context_manager: Any = None
        self.scheduler: Any = None
        self.config: Any = None
        self._boot_log: List[Dict[str, Any]] = []

    # ── Boot ──────────────────────────────────────────────────────────────────

    def boot(self) -> Dict[str, Any]:
        """
        Initialise all subsystems in dependency order.

        Returns a boot report with status for each subsystem.
        """
        if self._booted:
            return {"already_booted": True}

        report: Dict[str, Any] = {
            "assembly_version": ASSEMBLY_VERSION,
            "origin_signature": ORIGIN_SIGNATURE,
            "booted_at_ms": int(time.time() * 1000),
            "subsystems": {},
        }

        # 1 ── MerkleChain (canonical record)
        report["subsystems"]["merkle_chain"] = self._boot_merkle()

        # 2 ── WorldModule (world state + trajectory)
        report["subsystems"]["world_module"] = self._boot_world()

        # 3 ── VectorStore (RAG)
        report["subsystems"]["vector_store"] = self._boot_vector()

        # 4 ── ToolRegistry
        report["subsystems"]["tool_registry"] = self._boot_tools()

        # 5 ── PromptTemplate registry
        report["subsystems"]["prompt_template"] = self._boot_templates()

        # 6 ── EvalPipeline
        report["subsystems"]["eval_engine"] = self._boot_eval()

        # 7 ── PluginManager
        report["subsystems"]["plugin_manager"] = self._boot_plugins()

        # 8 ── ConfigManager (v2.0)
        report["subsystems"]["config_manager"] = self._boot_config()

        # 9 ── ConversationManager (v2.0)
        report["subsystems"]["conversation_manager"] = self._boot_conversation()

        # 10 ── LLMGateway (v2.0)
        report["subsystems"]["llm_gateway"] = self._boot_llm_gateway()

        # 11 ── ContextManager (v2.0)
        report["subsystems"]["context_manager"] = self._boot_context_manager()

        # 12 ── TaskScheduler (v2.0)
        report["subsystems"]["scheduler"] = self._boot_scheduler()

        self._booted = True
        self._seal_event("boot", report)
        return report

    # ── Private boot helpers ──────────────────────────────────────────────────

    def _boot_merkle(self) -> str:
        MerkleChain = _try_import("memory_chain", "MerkleChain")
        if MerkleChain is None:
            return "unavailable"
        try:
            data_dir = _REPO_ROOT / "03_memory" / "_data" / "memory_chain"
            self.chain = MerkleChain(data_dir)
            return "ok"
        except Exception as exc:  # noqa: BLE001
            return f"error: {exc}"

    def _boot_world(self) -> str:
        WorldModule = _try_import("world_module", "WorldModule")
        if WorldModule is None:
            return "unavailable"
        try:
            self.world = WorldModule()
            self.world.set_state("assembly_version", ASSEMBLY_VERSION)
            return "ok"
        except Exception as exc:  # noqa: BLE001
            return f"error: {exc}"

    def _boot_vector(self) -> str:
        VectorStore = _try_import("vector_store", "VectorStore")
        if VectorStore is None:
            return "unavailable"
        try:
            self.vector_store = VectorStore()
            return "ok"
        except Exception as exc:  # noqa: BLE001
            return f"error: {exc}"

    def _boot_tools(self) -> str:
        ToolRegistry = _try_import("tool_registry", "ToolRegistry")
        if ToolRegistry is None:
            return "unavailable"
        try:
            self.tool_registry = ToolRegistry()
            self._register_builtin_tools()
            return "ok"
        except Exception as exc:  # noqa: BLE001
            return f"error: {exc}"

    def _boot_templates(self) -> str:
        TemplateRegistry = _try_import("prompt_template", "TemplateRegistry")
        if TemplateRegistry is None:
            return "unavailable"
        try:
            self.template_registry = TemplateRegistry()
            self._register_builtin_templates()
            return "ok"
        except Exception as exc:  # noqa: BLE001
            return f"error: {exc}"

    def _boot_eval(self) -> str:
        default_pipeline = _try_import("eval_engine", "default_pipeline")
        if default_pipeline is None:
            return "unavailable"
        try:
            self.eval_pipeline = default_pipeline()
            return "ok"
        except Exception as exc:  # noqa: BLE001
            return f"error: {exc}"

    def _boot_plugins(self) -> str:
        PluginManager = _try_import("plugin_manager", "PluginManager")
        if PluginManager is None:
            return "unavailable"
        try:
            self.plugin_manager = PluginManager(
                plugin_dir=_REPO_ROOT / "09_workflow" / "plugins",
                registry=self.tool_registry,
            )
            found = self.plugin_manager.discover()
            self.plugin_manager.activate_all()
            return f"ok ({len(found)} plugin(s) discovered)"
        except Exception as exc:  # noqa: BLE001
            return f"error: {exc}"

    def _boot_config(self) -> str:
        ConfigManager = _try_import("config_manager", "ConfigManager")
        if ConfigManager is None:
            return "unavailable"
        try:
            self.config = ConfigManager()
            return "ok"
        except Exception as exc:  # noqa: BLE001
            return f"error: {exc}"

    def _boot_conversation(self) -> str:
        ConversationManager = _try_import("conversation_manager", "ConversationManager")
        if ConversationManager is None:
            return "unavailable"
        try:
            self.conversation_manager = ConversationManager()
            return "ok"
        except Exception as exc:  # noqa: BLE001
            return f"error: {exc}"

    def _boot_llm_gateway(self) -> str:
        LLMGateway = _try_import("llm_adapter", "LLMGateway")
        LocalAdapter = _try_import("llm_adapter", "LocalAdapter")
        OpenAIAdapter = _try_import("llm_adapter", "OpenAIAdapter")
        AnthropicAdapter = _try_import("llm_adapter", "AnthropicAdapter")
        if LLMGateway is None:
            return "unavailable"
        try:
            self.llm_gateway = LLMGateway()
            errors = []
            # 各 adapter 獨立註冊：單一失敗不阻斷其他 adapter（review PR#77）
            if LocalAdapter is not None:
                try:
                    local_base_url = "http://localhost:11434/v1"
                    if self.config:
                        local_base_url = str(self.config.get("llm.local_base_url", local_base_url))
                    self.llm_gateway.register("local", LocalAdapter(base_url=local_base_url))
                except Exception as exc:  # noqa: BLE001
                    errors.append(f"local: {exc}")
            if OpenAIAdapter is not None and self.config:
                try:
                    openai_key = str(self.config.get("llm.openai_api_key", "")).strip()
                    if openai_key:
                        self.llm_gateway.register("openai", OpenAIAdapter(api_key=openai_key))
                except Exception as exc:  # noqa: BLE001
                    errors.append(f"openai: {exc}")
            if AnthropicAdapter is not None and self.config:
                try:
                    anthropic_key = str(self.config.get("llm.anthropic_api_key", "")).strip()
                    if anthropic_key:
                        self.llm_gateway.register("anthropic", AnthropicAdapter(api_key=anthropic_key))
                except Exception as exc:  # noqa: BLE001
                    errors.append(f"anthropic: {exc}")
            return "ok" if not errors else f"partial: {'; '.join(errors)}"
        except Exception as exc:  # noqa: BLE001
            return f"error: {exc}"

    def _boot_context_manager(self) -> str:
        ContextManager = _try_import("context_manager", "ContextManager")
        if ContextManager is None:
            return "unavailable"
        try:
            max_tokens = 4096
            if self.config:
                max_tokens = int(self.config.get("context.max_tokens", 4096))
            self.context_manager = ContextManager(max_tokens=max_tokens)
            return "ok"
        except Exception as exc:  # noqa: BLE001
            return f"error: {exc}"

    def _boot_scheduler(self) -> str:
        TaskScheduler = _try_import("scheduler", "TaskScheduler")
        if TaskScheduler is None:
            return "unavailable"
        try:
            workers = 2
            if self.config:
                workers = int(self.config.get("scheduler.workers", 2))
            self.scheduler = TaskScheduler(workers=workers)
            self.scheduler.start()
            return f"ok ({workers} worker(s))"
        except Exception as exc:  # noqa: BLE001
            return f"error: {exc}"

    # ── Built-in tools ────────────────────────────────────────────────────────

    def _register_builtin_tools(self) -> None:
        if self.tool_registry is None:
            return

        @self.tool_registry.register(
            description="Return current UTC timestamp in milliseconds."
        )
        def now_ms() -> int:
            return int(time.time() * 1000)

        @self.tool_registry.register(
            description="Echo a message.",
            parameters={"message": str},
        )
        def echo(message: str) -> str:
            return message

        @self.tool_registry.register(
            description="Add two numbers.",
            parameters={"a": float, "b": float},
        )
        def add(a: float, b: float) -> float:
            return a + b

        @self.tool_registry.register(
            description="Subtract b from a.",
            parameters={"a": float, "b": float},
        )
        def subtract(a: float, b: float) -> float:
            return a - b

        @self.tool_registry.register(
            description="Multiply two numbers.",
            parameters={"a": float, "b": float},
        )
        def multiply(a: float, b: float) -> float:
            return a * b

        @self.tool_registry.register(
            description="Divide a by b.",
            parameters={"a": float, "b": float},
        )
        def divide(a: float, b: float) -> float:
            if b == 0:
                raise ValueError("Cannot divide by zero")
            return a / b

        @self.tool_registry.register(
            description="Retrieve world state snapshot.",
        )
        def world_snapshot() -> Dict[str, Any]:
            if self.world:
                return self.world.snapshot()
            return {}

        @self.tool_registry.register(
            description="Query the vector store for nearest neighbours.",
            parameters={"query_csv": str, "top_k": int},
        )
        def vector_query(query_csv: str, top_k: int = 3) -> List[Any]:
            if self.vector_store is None:
                return []
            vec = [float(x) for x in query_csv.split(",")]
            hits = self.vector_store.query(vec, top_k=top_k)
            return [{"id": h[0], "score": h[1], "meta": h[2]} for h in hits]

        @self.tool_registry.register(
            description="Get basic text statistics.",
            parameters={"text": str},
        )
        def text_stats(text: str) -> Dict[str, int]:
            words = [w for w in text.strip().split() if w]
            return {
                "chars": len(text),
                "words": len(words),
                "lines": text.count("\n") + (1 if text.strip() else 0),
            }

    # ── Built-in templates ────────────────────────────────────────────────────

    def _register_builtin_templates(self) -> None:
        if self.template_registry is None:
            return
        self.template_registry.add(
            "system_intro",
            "You are {name}, a {role} in the MRL AI System. "
            "Your origin signature is MrLiouWord. "
            "Always act in accordance with the Mother Core Assembly laws.",
            "Standard system introduction prompt",
        )
        self.template_registry.add(
            "task_prompt",
            "Goal: {goal}\n\nContext:\n{context}\n\nPlease proceed step by step.",
            "Standard task prompt with goal and context",
        )
        self.template_registry.add(
            "eval_summary",
            "Output evaluation for '{label}':\n"
            "  composite score: {composite}\n"
            "  passed: {passed}\n"
            "  individual scores: {scores}",
            "Evaluation result summary template",
        )

    # ── Public API ────────────────────────────────────────────────────────────

    def run_agent(
        self,
        goal: str,
        think_fn: Optional[Any] = None,
        max_steps: int = 20,
    ) -> Dict[str, Any]:
        """
        Run an agent loop for *goal*.

        If *think_fn* is not provided, a simple default think function is used
        that immediately finishes with a fixed answer (useful for testing).
        """
        AgentPlanner = _try_import("agent_planner", "AgentPlanner")
        FINISH_ACTION = _try_import("agent_planner", "FINISH_ACTION") or "__finish__"

        if AgentPlanner is None or self.tool_registry is None:
            return {"error": "AgentPlanner or ToolRegistry unavailable", "goal": goal}

        if think_fn is None:
            def think_fn(_state: Dict[str, Any]) -> Dict[str, Any]:
                return {
                    "thought": f"Completing goal: {goal}",
                    "action": FINISH_ACTION,
                    "args": {"answer": f"[MotherAssembly] Goal noted: {goal}"},
                }

        planner = AgentPlanner(self.tool_registry, think_fn=think_fn, max_steps=max_steps)
        result = planner.run(goal)
        self._seal_event("run_agent", {"goal": goal, "finished": result.get("finished")})
        return result

    def evaluate(
        self,
        output: str,
        keywords: Optional[List[str]] = None,
        reference: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Score *output* with the EvalPipeline."""
        if self.eval_pipeline is None:
            return {"error": "EvalPipeline unavailable"}
        ref = dict(reference or {})
        if keywords:
            ref.setdefault("keywords", keywords)
        result = self.eval_pipeline.run(output, ref)
        self._seal_event("evaluate", {"composite": result["composite"]})
        return result

    def render_prompt(
        self,
        template_id: str,
        variables: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Render a named prompt template."""
        if self.template_registry is None:
            return f"[PromptTemplate unavailable] id={template_id}"
        return self.template_registry.render(template_id, variables or {})

    def seal_text(self, text: str, label: str = "unnamed") -> Dict[str, Any]:
        """
        Encode *text* through the full reversible chain and commit to MerkleChain.
        Returns the trace record.
        """
        text_to_trace = _try_import("fltnz_parser", "text_to_trace")
        if text_to_trace is None:
            return {"error": "fltnz_parser unavailable"}
        trace = text_to_trace(text, label=label)
        self._seal_event("seal_text", {"label": label})
        return trace

    def chat(
        self,
        message: str,
        *,
        session_id: Optional[str] = None,
        model: Optional[str] = None,
        system_prompt: Optional[str] = None,
        max_tokens: int = 1024,
        temperature: float = 0.7,
    ) -> Dict[str, Any]:
        """
        Send a chat message and return the assistant reply.

        Creates a new session automatically if *session_id* is not provided.
        Applies context window management before calling the LLM.

        Returns
        -------
        {
          "session_id": ...,
          "reply":      ...,
          "model":      ...,
          "origin_signature": "MrLiouWord",
        }
        """
        if self.conversation_manager is None:
            return {"error": "ConversationManager unavailable"}

        # Resolve model — deny-by-default（rootlaw rl_00）：不隱式退回 mock
        resolved_model = str(model or (
            self.config.get("llm.default_model", "") if self.config else ""
        )).strip()
        if not resolved_model:
            return {"error": "'model' is required unless llm.default_model is configured"}
        allow_mock = False
        if self.config:
            allow_mock = str(self.config.get("llm.allow_mock", False)).strip().lower() in ("1", "true", "yes", "on")
        if resolved_model.startswith("mock") and not allow_mock:
            return {"error": "MockAdapter is test-only. Set llm.allow_mock=true to enable."}

        # Get or create session
        if session_id is None:
            sp = system_prompt or (
                self.config.get("conversation.default_system_prompt", "") if self.config else ""
            )
            session_id = self.conversation_manager.new_session(system_prompt=sp)
        else:
            if self.conversation_manager.get_session(session_id) is None:
                return {"error": f"Session not found: {session_id}"}

        # Record user message
        self.conversation_manager.add_message(session_id, "user", message)

        # Get history and trim context
        history = self.conversation_manager.get_history(session_id)
        if self.context_manager is not None:
            history, _ = self.context_manager.fit(history)

        # Build LLM-compatible message list
        llm_messages = [
            {"role": m["role"], "content": m["content"]}
            for m in history
        ]

        # LLM call — deny-by-default（rootlaw rl_00）：gateway 不可用或呼叫失敗時
        # 以 top-level error 誠實回報，不以 Mock 偽造回覆（fail closed）。
        if self.llm_gateway is None:
            return {
                "error": "LLM gateway unavailable (not booted)",
                "session_id": session_id,
                "model": resolved_model,
                "origin_signature": ORIGIN_SIGNATURE,
            }
        LLMRequest = _try_import("llm_adapter", "LLMRequest")
        if LLMRequest is None:
            return {
                "error": "llm_adapter module unavailable",
                "session_id": session_id,
                "model": resolved_model,
                "origin_signature": ORIGIN_SIGNATURE,
            }
        req = LLMRequest(
            model=resolved_model,
            messages=llm_messages,
            max_tokens=max_tokens,
            temperature=temperature,
        )
        try:
            resp = self.llm_gateway.complete(req)
        except Exception as exc:  # noqa: BLE001 — 例如未註冊模型的 KeyError
            return {
                "error": f"LLM error: {exc}",
                "session_id": session_id,
                "model": resolved_model,
                "origin_signature": ORIGIN_SIGNATURE,
            }
        if not resp.ok:
            return {
                "error": f"LLM error: {resp.error}",
                "session_id": session_id,
                "model": resolved_model,
                "origin_signature": ORIGIN_SIGNATURE,
            }
        reply_text = resp.text

        # Record assistant reply
        self.conversation_manager.add_message(session_id, "assistant", reply_text)
        self._seal_event("chat", {"session_id": session_id, "model": resolved_model})

        return {
            "session_id": session_id,
            "reply": reply_text,
            "model": resolved_model,
            "origin_signature": ORIGIN_SIGNATURE,
        }

    def submit_task(
        self,
        fn: Any,
        *,
        name: str = "task",
        priority: int = 5,
    ) -> Optional[str]:
        """Submit a background task to the TaskScheduler. Returns task_id or None."""
        if self.scheduler is None:
            return None
        return self.scheduler.submit(fn, name=name, priority=priority)

    def run_multi_agent(
        self,
        goal: str,
        roles: Optional[List[Any]] = None,
        mode: str = "sequential",
        rounds: int = 3,
    ) -> Dict[str, Any]:
        """
        Run a multi-agent session for *goal*.

        Parameters
        ----------
        goal  : top-level objective
        roles : list of AgentRole objects (default: planner + researcher + writer)
        mode  : "sequential" | "round_robin"
        rounds: number of rounds (round_robin mode only)
        """
        MultiAgentSession = _try_import("multi_agent", "MultiAgentSession")
        AgentRole = _try_import("multi_agent", "AgentRole")

        if MultiAgentSession is None or AgentRole is None:
            return {"error": "multi_agent module unavailable"}

        sess = MultiAgentSession(goal=goal)

        if roles is None:
            roles = [
                AgentRole("planner",    "Decompose the goal into concrete sub-tasks."),
                AgentRole("researcher", "Research each sub-task and gather information."),
                AgentRole("writer",     "Synthesise the research into a clear answer."),
            ]

        for role in roles:
            sess.add_role(role)

        if mode == "round_robin":
            results = sess.run_round_robin(rounds=rounds)
        else:
            results = sess.run_sequential()

        self._seal_event("multi_agent", {"goal": goal, "mode": mode, "agents": len(roles)})
        return {
            "goal": goal,
            "mode": mode,
            "results": results,
            "summary": sess.summary(),
            "origin_signature": ORIGIN_SIGNATURE,
        }

    def status(self) -> Dict[str, Any]:
        """Return a health-check snapshot of all subsystems."""
        return {
            "assembly_version": ASSEMBLY_VERSION,
            "origin_signature": ORIGIN_SIGNATURE,
            "booted": self._booted,
            "subsystems": {
                "merkle_chain":         self.chain is not None,
                "world_module":         self.world is not None,
                "vector_store":         self.vector_store is not None,
                "tool_registry":        self.tool_registry is not None,
                "template_registry":    self.template_registry is not None,
                "eval_pipeline":        self.eval_pipeline is not None,
                "plugin_manager":       self.plugin_manager is not None,
                # v2.0
                "config_manager":       self.config is not None,
                "conversation_manager": self.conversation_manager is not None,
                "llm_gateway":          self.llm_gateway is not None,
                "context_manager":      self.context_manager is not None,
                "scheduler":            self.scheduler is not None,
            },
            "checked_at_ms": int(time.time() * 1000),
        }

    # ── Internal ──────────────────────────────────────────────────────────────

    def _seal_event(self, event_type: str, detail: Any = None) -> None:
        """Commit a canonical event to the MerkleChain (if available)."""
        if self.chain is None:
            return
        try:
            self.chain.commit(
                payload={
                    "event_type": event_type,
                    "detail": detail,
                    "origin_signature": ORIGIN_SIGNATURE,
                    "ts_ms": int(time.time() * 1000),
                },
                layer="L7",
                tags=["mother_assembly", event_type],
                meta={"source": "mother_assembly"},
            )
        except Exception:  # noqa: BLE001
            pass  # Chain failure must never crash the assembly


# ─── CLI ─────────────────────────────────────────────────────────────────────

def _cmd_boot(_args: argparse.Namespace) -> None:
    ma = MotherAssembly()
    report = ma.boot()
    print(json.dumps(report, ensure_ascii=False, indent=2, default=str))


def _cmd_status(_args: argparse.Namespace) -> None:
    ma = MotherAssembly()
    ma.boot()
    snap = ma.status()
    ok_count = sum(1 for v in snap["subsystems"].values() if v)
    total = len(snap["subsystems"])
    print(f"MotherAssembly v{snap['assembly_version']}  [{ok_count}/{total} subsystems online]")
    for name, online in snap["subsystems"].items():
        icon = "✅" if online else "❌"
        print(f"  {icon}  {name}")


def _cmd_run(args: argparse.Namespace) -> None:
    ma = MotherAssembly()
    ma.boot()
    result = ma.run_agent(args.goal)
    print(json.dumps(result, ensure_ascii=False, indent=2, default=str))


def _cmd_eval(args: argparse.Namespace) -> None:
    ma = MotherAssembly()
    ma.boot()
    keywords = [k.strip() for k in args.keywords.split(",")] if args.keywords else []
    result = ma.evaluate(args.output, keywords=keywords)
    print(json.dumps(result, ensure_ascii=False, indent=2))


def _cmd_seal(args: argparse.Namespace) -> None:
    ma = MotherAssembly()
    ma.boot()
    trace = ma.seal_text(args.text, label=args.label or "cli")
    print(json.dumps(trace, ensure_ascii=False, indent=2, default=str))


def _cmd_chat(args: argparse.Namespace) -> None:
    ma = MotherAssembly()
    ma.boot()
    result = ma.chat(
        args.message,
        session_id=args.sid or None,
        model=args.model or None,
    )
    print(json.dumps(result, ensure_ascii=False, indent=2, default=str))


def _cmd_multi_agent(args: argparse.Namespace) -> None:
    ma = MotherAssembly()
    ma.boot()
    result = ma.run_multi_agent(args.goal, mode=args.mode)
    print(json.dumps(result, ensure_ascii=False, indent=2, default=str))


def _build_argparser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="MotherAssembly — unified MRL AI System entry point"
    )
    sub = p.add_subparsers(dest="cmd", required=True)

    sub.add_parser("boot",   help="Boot all subsystems and print report")
    sub.add_parser("status", help="Print subsystem health status")

    r = sub.add_parser("run", help="Run an agent task")
    r.add_argument("--goal", required=True, help="Goal string for the agent")

    e = sub.add_parser("eval", help="Evaluate an output string")
    e.add_argument("--output", required=True)
    e.add_argument("--keywords", default="", help="Comma-separated keywords")

    s = sub.add_parser("seal", help="Seal text through the reversible chain")
    s.add_argument("--text", required=True)
    s.add_argument("--label", default="cli")

    ch = sub.add_parser("chat", help="Send a chat message (multi-turn)")
    ch.add_argument("--message", required=True)
    ch.add_argument("--sid",    default="", help="Session ID (creates new if omitted)")
    ch.add_argument("--model",  default="", help="LLM model name")

    ma_cmd = sub.add_parser("multi-agent", help="Run a multi-agent task")
    ma_cmd.add_argument("--goal", required=True)
    ma_cmd.add_argument("--mode", default="sequential", choices=["sequential", "round_robin"])

    return p


def main() -> None:
    parser = _build_argparser()
    args = parser.parse_args()
    dispatch = {
        "boot":        _cmd_boot,
        "status":      _cmd_status,
        "run":         _cmd_run,
        "eval":        _cmd_eval,
        "seal":        _cmd_seal,
        "chat":        _cmd_chat,
        "multi-agent": _cmd_multi_agent,
    }
    dispatch[args.cmd](args)


if __name__ == "__main__":
    main()
