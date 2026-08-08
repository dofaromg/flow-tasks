#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
llm_adapter.py — LLM Provider Gateway
origin_signature: MrLiouWord
layer: L7 LOOP
group: Y=3 FlowAgentRuntime

Industry capability: unified LLM provider abstraction supporting OpenAI,
                     Anthropic, and local model endpoints — distilled from
                     the three major mainstream AI systems.
MRL extension: every LLM call is wrapped in a trace-compatible LLMResponse
               record stamped with origin_signature, elapsed_ms, and model.

Architecture
------------
  LLMRequest  — input message list + generation config
  LLMResponse — output text + usage stats + trace record
  LLMAdapter  — abstract base class
    ├── OpenAIAdapter    — calls OpenAI Chat Completions API
    ├── AnthropicAdapter — calls Anthropic Messages API
    ├── LocalAdapter     — calls any OpenAI-compatible local endpoint
    └── MockAdapter      — deterministic mock (no network; for testing)
  LLMGateway  — routes requests to the registered adapter by model name

Usage (library)
---------------
    from llm_adapter import LLMGateway, LLMRequest, MockAdapter

    gw = LLMGateway()
    gw.register("mock", MockAdapter(reply="Hello from MRL!"))

    resp = gw.complete(LLMRequest(
        model="mock",
        messages=[{"role": "user", "content": "Hi"}],
    ))
    print(resp.text)     # Hello from MRL!
    print(resp.ok)       # True

CLI
---
    python 09_workflow/llm_adapter.py mock   --prompt "Hello"
    python 09_workflow/llm_adapter.py list
"""

from __future__ import annotations

import argparse
import json
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

ORIGIN_SIGNATURE = "MrLiouWord"


# ─── Data classes ─────────────────────────────────────────────────────────────

@dataclass
class LLMRequest:
    """
    A single LLM completion request.

    Fields
    ------
    model        : Model identifier (e.g. "gpt-4o", "claude-3-5-sonnet", "mock")
    messages     : List of {"role": ..., "content": ...} dicts
    max_tokens   : Maximum tokens to generate (default 1024)
    temperature  : Sampling temperature 0-2 (default 0.7)
    stream       : Whether to request streaming (adapter must support it)
    tools        : Optional tool/function calling spec (OpenAI format)
    extra        : Provider-specific extra kwargs
    """

    model: str
    messages: List[Dict[str, Any]]
    max_tokens: int = 1024
    temperature: float = 0.7
    stream: bool = False
    tools: Optional[List[Dict[str, Any]]] = None
    extra: Dict[str, Any] = field(default_factory=dict)


@dataclass
class LLMResponse:
    """
    A completed LLM response — trace-compatible record.

    Fields
    ------
    text          : Generated text content
    model         : Model that generated the response
    ok            : True if the call succeeded
    error         : Error message if not ok
    input_tokens  : Prompt token count (if reported)
    output_tokens : Generated token count (if reported)
    finish_reason : stop | length | tool_calls | error
    tool_calls    : Parsed tool call objects (if any)
    elapsed_ms    : Wall-clock latency
    called_at_ms  : Request timestamp
    raw           : Full raw provider response (for debugging)
    """

    text: str
    model: str
    ok: bool = True
    error: Optional[str] = None
    input_tokens: int = 0
    output_tokens: int = 0
    finish_reason: str = "stop"
    tool_calls: Optional[List[Dict[str, Any]]] = None
    elapsed_ms: int = 0
    called_at_ms: int = field(default_factory=lambda: int(time.time() * 1000))
    raw: Optional[Any] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "text": self.text,
            "model": self.model,
            "ok": self.ok,
            "error": self.error,
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "finish_reason": self.finish_reason,
            "tool_calls": self.tool_calls,
            "elapsed_ms": self.elapsed_ms,
            "called_at_ms": self.called_at_ms,
            "origin_signature": ORIGIN_SIGNATURE,
        }


# ─── Abstract base ────────────────────────────────────────────────────────────

class LLMAdapter(ABC):
    """Abstract base for all LLM provider adapters."""

    @abstractmethod
    def complete(self, request: LLMRequest) -> LLMResponse:
        """Send *request* to the provider and return an LLMResponse."""

    def name(self) -> str:
        return self.__class__.__name__


# ─── MockAdapter ─────────────────────────────────────────────────────────────

class MockAdapter(LLMAdapter):
    """
    Deterministic mock adapter — no network calls.

    Useful for unit testing and CI pipelines.  Returns a fixed reply or
    echoes the last user message.
    """

    def __init__(self, reply: Optional[str] = None, latency_ms: int = 0) -> None:
        self._reply = reply
        self._latency_ms = latency_ms

    def complete(self, request: LLMRequest) -> LLMResponse:
        t0 = time.time()
        if self._latency_ms:
            time.sleep(self._latency_ms / 1000)

        # Default reply: echo last user message
        user_msgs = [m for m in request.messages if m.get("role") == "user"]
        content = (
            self._reply
            or (f"[MockAdapter] Echo: {user_msgs[-1]['content']}" if user_msgs else "[MockAdapter] No user message")
        )

        return LLMResponse(
            text=content,
            model=request.model,
            ok=True,
            input_tokens=sum(len(m.get("content", "")) // 4 for m in request.messages),
            output_tokens=len(content) // 4,
            finish_reason="stop",
            elapsed_ms=int((time.time() - t0) * 1000),
            called_at_ms=int(t0 * 1000),
        )

    def name(self) -> str:
        return "MockAdapter"


# ─── OpenAIAdapter ────────────────────────────────────────────────────────────

class OpenAIAdapter(LLMAdapter):
    """
    Adapter for the OpenAI Chat Completions API.

    Requires the ``openai`` package (``pip install openai``).
    Set OPENAI_API_KEY in your environment before use.
    """

    def __init__(self, api_key: Optional[str] = None, base_url: Optional[str] = None) -> None:
        self._api_key = api_key
        self._base_url = base_url

    def _client(self) -> Any:
        try:
            import openai  # noqa: PLC0415
        except ImportError as exc:
            raise ImportError("openai package required: pip install openai") from exc
        import os
        key = self._api_key or os.environ.get("OPENAI_API_KEY", "")
        kwargs: Dict[str, Any] = {"api_key": key}
        if self._base_url:
            kwargs["base_url"] = self._base_url
        return openai.OpenAI(**kwargs)

    def complete(self, request: LLMRequest) -> LLMResponse:
        t0 = time.time()
        try:
            client = self._client()
            kwargs: Dict[str, Any] = {
                "model": request.model,
                "messages": request.messages,
                "max_tokens": request.max_tokens,
                "temperature": request.temperature,
                **request.extra,
            }
            if request.tools:
                kwargs["tools"] = request.tools
                kwargs["tool_choice"] = "auto"

            resp = client.chat.completions.create(**kwargs)
            choice = resp.choices[0]
            msg = choice.message

            tool_calls = None
            if getattr(msg, "tool_calls", None):
                tool_calls = [
                    {
                        "id": tc.id,
                        "type": tc.type,
                        "function": {
                            "name": tc.function.name,
                            "arguments": tc.function.arguments,
                        },
                    }
                    for tc in msg.tool_calls
                ]

            return LLMResponse(
                text=msg.content or "",
                model=resp.model,
                ok=True,
                input_tokens=resp.usage.prompt_tokens if resp.usage else 0,
                output_tokens=resp.usage.completion_tokens if resp.usage else 0,
                finish_reason=choice.finish_reason or "stop",
                tool_calls=tool_calls,
                elapsed_ms=int((time.time() - t0) * 1000),
                called_at_ms=int(t0 * 1000),
                raw=resp,
            )
        except Exception as exc:  # noqa: BLE001
            return LLMResponse(
                text="",
                model=request.model,
                ok=False,
                error=f"{type(exc).__name__}: {exc}",
                elapsed_ms=int((time.time() - t0) * 1000),
                called_at_ms=int(t0 * 1000),
            )

    def name(self) -> str:
        return "OpenAIAdapter"


# ─── AnthropicAdapter ────────────────────────────────────────────────────────

class AnthropicAdapter(LLMAdapter):
    """
    Adapter for the Anthropic Messages API (Claude models).

    Requires the ``anthropic`` package (``pip install anthropic``).
    Set ANTHROPIC_API_KEY in your environment before use.
    """

    def __init__(self, api_key: Optional[str] = None) -> None:
        self._api_key = api_key

    def _client(self) -> Any:
        try:
            import anthropic  # noqa: PLC0415
        except ImportError as exc:
            raise ImportError("anthropic package required: pip install anthropic") from exc
        import os
        key = self._api_key or os.environ.get("ANTHROPIC_API_KEY", "")
        return anthropic.Anthropic(api_key=key)

    def complete(self, request: LLMRequest) -> LLMResponse:
        t0 = time.time()
        try:
            client = self._client()
            # Anthropic separates system from user/assistant turns
            system = ""
            messages = []
            for m in request.messages:
                if m.get("role") == "system":
                    system = m.get("content", "")
                else:
                    messages.append({"role": m["role"], "content": m.get("content", "")})

            kwargs: Dict[str, Any] = {
                "model": request.model,
                "max_tokens": request.max_tokens,
                "messages": messages,
                **request.extra,
            }
            if system:
                kwargs["system"] = system
            if request.tools:
                kwargs["tools"] = request.tools

            resp = client.messages.create(**kwargs)
            text = "".join(
                block.text for block in resp.content if hasattr(block, "text")
            )

            return LLMResponse(
                text=text,
                model=resp.model,
                ok=True,
                input_tokens=resp.usage.input_tokens if resp.usage else 0,
                output_tokens=resp.usage.output_tokens if resp.usage else 0,
                finish_reason=resp.stop_reason or "stop",
                elapsed_ms=int((time.time() - t0) * 1000),
                called_at_ms=int(t0 * 1000),
                raw=resp,
            )
        except Exception as exc:  # noqa: BLE001
            return LLMResponse(
                text="",
                model=request.model,
                ok=False,
                error=f"{type(exc).__name__}: {exc}",
                elapsed_ms=int((time.time() - t0) * 1000),
                called_at_ms=int(t0 * 1000),
            )

    def name(self) -> str:
        return "AnthropicAdapter"


# ─── LocalAdapter ────────────────────────────────────────────────────────────

class LocalAdapter(LLMAdapter):
    """
    Adapter for any OpenAI-compatible local endpoint (e.g. Ollama, LM Studio,
    vLLM, llama.cpp server).

    Parameters
    ----------
    base_url : str
        e.g. "http://localhost:11434/v1" for Ollama
    api_key  : str
        Usually "ollama" or "local"; required by the openai SDK but not
        validated by local servers.
    """

    def __init__(
        self,
        base_url: str = "http://localhost:11434/v1",
        api_key: str = "local",
    ) -> None:
        self._openai_adapter = OpenAIAdapter(api_key=api_key, base_url=base_url)

    def complete(self, request: LLMRequest) -> LLMResponse:
        return self._openai_adapter.complete(request)

    def name(self) -> str:
        return f"LocalAdapter({self._openai_adapter._base_url})"


# ─── LLMGateway ──────────────────────────────────────────────────────────────

class LLMGateway:
    """
    Routes LLMRequests to the correct adapter based on model name prefix or
    an explicit registration.

    Registration
    ------------
        gw = LLMGateway()
        gw.register("mock",   MockAdapter())
        gw.register("gpt-4",  OpenAIAdapter())
        gw.register("claude", AnthropicAdapter())

    Auto-routing by prefix
    ----------------------
    If no exact match is found, the gateway checks:
      model starts with "gpt"     → OpenAIAdapter (if registered under "openai")
      model starts with "claude"  → AnthropicAdapter (if registered under "anthropic")
      model starts with "mock"    → MockAdapter
    """

    def __init__(self) -> None:
        self._adapters: Dict[str, LLMAdapter] = {}
        # Register a built-in mock adapter (testing only).
        # NOTE: Production routing must never silently fall back to this adapter.
        self._adapters["mock"] = MockAdapter()

    def register(self, name: str, adapter: LLMAdapter) -> "LLMGateway":
        self._adapters[name] = adapter
        return self

    def adapter_for(self, model: str) -> LLMAdapter:
        # Exact match
        if model in self._adapters:
            return self._adapters[model]
        # Prefix match
        if model.startswith("gpt") and "openai" in self._adapters:
            return self._adapters["openai"]
        if model.startswith("claude") and "anthropic" in self._adapters:
            return self._adapters["anthropic"]
        if model.startswith("mock"):
            return self._adapters["mock"]
        raise KeyError(
            f"No adapter registered for model '{model}'. "
            f"Registered: {list(self._adapters.keys())}"
        )

    def is_mock_model(self, model: str) -> bool:
        try:
            return isinstance(self.adapter_for(model), MockAdapter)
        except KeyError:
            return False

    def complete(self, request: LLMRequest) -> LLMResponse:
        """Route *request* to the appropriate adapter and return the response."""
        adapter = self.adapter_for(request.model)
        return adapter.complete(request)

    def list_adapters(self) -> List[str]:
        return sorted(self._adapters.keys())


# ─── CLI ─────────────────────────────────────────────────────────────────────

def _cmd_mock(args: argparse.Namespace) -> None:
    adapter = MockAdapter()
    req = LLMRequest(
        model="mock",
        messages=[{"role": "user", "content": args.prompt}],
    )
    resp = adapter.complete(req)
    print(json.dumps(resp.to_dict(), ensure_ascii=False, indent=2))


def _cmd_list(_args: argparse.Namespace) -> None:
    gw = LLMGateway()
    print("Registered adapters:")
    for name in gw.list_adapters():
        print(f"  {name}")


def _build_argparser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="LLMAdapter — LLM provider gateway")
    sub = p.add_subparsers(dest="cmd", required=True)

    m = sub.add_parser("mock", help="Run a mock completion")
    m.add_argument("--prompt", required=True, help="User prompt text")

    sub.add_parser("list", help="List registered adapters")

    return p


def main() -> None:
    parser = _build_argparser()
    args = parser.parse_args()
    dispatch = {"mock": _cmd_mock, "list": _cmd_list}
    dispatch[args.cmd](args)


if __name__ == "__main__":
    main()
