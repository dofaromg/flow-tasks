#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
llm_gateway.py — Local LLM Gateway (zero external dependencies)
origin_signature: MrLiouWord
layer: L7 LOOP
group: Y=3 MrLiouAIRuntime

Goal: product-level local-only LLM access.  No cloud APIs, no third-party
      packages.  Every call is self-contained and fully auditable.

Supported backends (all local / self-hosted):
  - ollama   : Ollama server running at localhost (default http://127.0.0.1:11434)
  - llamacpp : llama-cpp-python HTTP server (OpenAI-compatible, local)
  - stub     : deterministic offline stub — always available, no server needed

Backend selection is automatic:
  1. Try "ollama"   (health-check /api/tags)
  2. Try "llamacpp" (health-check /v1/models)
  3. Fall back to   "stub"

All responses are normalised to the same envelope so callers are backend-agnostic.

Response envelope
-----------------
    {
      "ok":               bool,
      "text":             str,          # generated text
      "model":            str,
      "backend":          str,          # "ollama" | "llamacpp" | "stub"
      "prompt_tokens":    int,
      "completion_tokens":int,
      "elapsed_ms":       int,
      "called_at_ms":     int,
      "origin_signature": "MrLiouWord",
      "error":            str | None,
    }

Usage (library)
---------------
    from llm_gateway import LLMGateway

    gw = LLMGateway()          # auto-detects backend
    resp = gw.chat([
        {"role": "system",    "content": "You are a helpful assistant."},
        {"role": "user",      "content": "What is 3 + 4?"},
    ])
    print(resp["text"])

    # Force a specific model / backend
    gw2 = LLMGateway(backend="ollama", model="llama3")
    resp2 = gw2.complete("The capital of France is")

CLI
---
    python 09_workflow/llm_gateway.py status
    python 09_workflow/llm_gateway.py chat   --msg "Hello"
    python 09_workflow/llm_gateway.py complete --prompt "Once upon a time"
    python 09_workflow/llm_gateway.py list-models
"""

from __future__ import annotations

import argparse
import json
import time
import urllib.error
import urllib.request
from typing import Any, Callable, Dict, Iterator, List, Optional, TypeVar

_T = TypeVar("_T")

ORIGIN_SIGNATURE = "MrLiouWord"
GATEWAY_VERSION = "1.0"

# ── Default endpoints ─────────────────────────────────────────────────────────

_OLLAMA_BASE    = "http://127.0.0.1:11434"
_LLAMACPP_BASE  = "http://127.0.0.1:8080"
_DEFAULT_TIMEOUT = 60  # seconds

# ── Stub responses (offline fallback) ─────────────────────────────────────────

_STUB_RESPONSES = [
    "MRL stub: I have received your message and am processing it locally.",
    "MRL stub: The answer depends on context — please provide more detail.",
    "MRL stub: Local inference is not yet connected; running in stub mode.",
    "MRL stub: All systems nominal. Awaiting local model connection.",
]
_stub_idx = {"v": 0}


def _stub_reply(prompt: str) -> str:
    i = _stub_idx["v"] % len(_STUB_RESPONSES)
    _stub_idx["v"] += 1
    # Echo back the first 60 chars of prompt so callers can verify routing
    snippet = prompt[:60].replace("\n", " ")
    return f"{_STUB_RESPONSES[i]} [echo: {snippet!r}]"


# ── HTTP helper ───────────────────────────────────────────────────────────────

def _http_post(url: str, payload: Dict[str, Any], timeout: int = _DEFAULT_TIMEOUT) -> Dict[str, Any]:
    data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json", "Accept": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _http_get(url: str, timeout: int = 5) -> Dict[str, Any]:
    req = urllib.request.Request(url, headers={"Accept": "application/json"}, method="GET")
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


# ── Retry / backoff ───────────────────────────────────────────────────────────

_RETRY_DELAYS = (0.5, 1.0, 2.0)  # wait times between attempts in seconds


def _with_retry(fn: Callable[..., _T], *args: Any, max_retries: int = 3, **kwargs: Any) -> _T:
    """
    Invoke *fn* with exponential backoff on transient network errors.

    Only ``urllib.error.URLError`` (connection refused, timeout, DNS failure)
    triggers a retry.  Any other exception is propagated immediately.

    Parameters
    ----------
    fn          : Callable to invoke.
    *args       : Positional arguments forwarded to *fn*.
    max_retries : Total number of attempts (default 3).
    **kwargs    : Keyword arguments forwarded to *fn*.
    """
    if max_retries < 1:
        raise ValueError("_with_retry: max_retries must be >= 1")
    last_exc: Optional[Exception] = None
    for attempt in range(max_retries):
        try:
            return fn(*args, **kwargs)
        except urllib.error.URLError as exc:
            last_exc = exc
            if attempt < max_retries - 1:
                delay = _RETRY_DELAYS[min(attempt, len(_RETRY_DELAYS) - 1)]
                time.sleep(delay)
    raise last_exc  # type: ignore[misc]


# ── Health checks ─────────────────────────────────────────────────────────────

def _ollama_healthy(base: str) -> bool:
    try:
        _http_get(f"{base}/api/tags", timeout=3)
        return True
    except Exception:
        return False


def _llamacpp_healthy(base: str) -> bool:
    try:
        _http_get(f"{base}/v1/models", timeout=3)
        return True
    except Exception:
        return False


# ── Model listing ─────────────────────────────────────────────────────────────

def _ollama_models(base: str) -> List[str]:
    try:
        data = _http_get(f"{base}/api/tags")
        return [m["name"] for m in data.get("models", [])]
    except Exception:
        return []


def _llamacpp_models(base: str) -> List[str]:
    try:
        data = _http_get(f"{base}/v1/models")
        return [m["id"] for m in data.get("data", [])]
    except Exception:
        return []


# ── Response builder ──────────────────────────────────────────────────────────

def _make_response(
    ok: bool,
    text: str,
    model: str,
    backend: str,
    prompt_tokens: int = 0,
    completion_tokens: int = 0,
    elapsed_ms: int = 0,
    called_at_ms: int = 0,
    error: Optional[str] = None,
) -> Dict[str, Any]:
    return {
        "ok": ok,
        "text": text,
        "model": model,
        "backend": backend,
        "prompt_tokens": prompt_tokens,
        "completion_tokens": completion_tokens,
        "elapsed_ms": elapsed_ms,
        "called_at_ms": called_at_ms or int(time.time() * 1000),
        "origin_signature": ORIGIN_SIGNATURE,
        "error": error,
    }


# ─── LLMGateway ───────────────────────────────────────────────────────────────

class LLMGateway:
    """
    Local-only LLM gateway with automatic backend detection.

    Parameters
    ----------
    backend : str | None
        Force a backend: "ollama", "llamacpp", or "stub".
        If None (default), auto-detect in priority order.
    model : str | None
        Model name passed to the backend.  If None, the backend's default
        is used (first available model, or "llama3" for Ollama).
    ollama_base : str
        Base URL of the Ollama server.
    llamacpp_base : str
        Base URL of the llama-cpp-python HTTP server.
    timeout : int
        HTTP timeout in seconds.
    """

    def __init__(
        self,
        backend: Optional[str] = None,
        model: Optional[str] = None,
        ollama_base: str = _OLLAMA_BASE,
        llamacpp_base: str = _LLAMACPP_BASE,
        timeout: int = _DEFAULT_TIMEOUT,
    ) -> None:
        self._ollama_base = ollama_base
        self._llamacpp_base = llamacpp_base
        self._timeout = timeout
        self._backend = backend or self._detect_backend()
        self._model = model or self._default_model()

    # ── Backend detection ─────────────────────────────────────────────────────

    def _detect_backend(self) -> str:
        if _ollama_healthy(self._ollama_base):
            return "ollama"
        if _llamacpp_healthy(self._llamacpp_base):
            return "llamacpp"
        return "stub"

    def _default_model(self) -> str:
        if self._backend == "ollama":
            models = _ollama_models(self._ollama_base)
            return models[0] if models else "llama3"
        if self._backend == "llamacpp":
            models = _llamacpp_models(self._llamacpp_base)
            return models[0] if models else "local-model"
        return "stub-model"

    # ── Public API ────────────────────────────────────────────────────────────

    @property
    def backend(self) -> str:
        return self._backend

    @property
    def model(self) -> str:
        return self._model

    def list_models(self) -> List[str]:
        """Return available local models."""
        if self._backend == "ollama":
            return _ollama_models(self._ollama_base)
        if self._backend == "llamacpp":
            return _llamacpp_models(self._llamacpp_base)
        return ["stub-model"]

    def status(self) -> Dict[str, Any]:
        """
        Return a health-check dict describing the active backend.

        Returns
        -------
        {
          "backend":          str,   # "ollama" | "llamacpp" | "stub"
          "model":            str,
          "is_stub":          bool,  # True when running offline stub
          "available_models": list,
          "origin_signature": "MrLiouWord",
        }
        """
        return {
            "backend":          self._backend,
            "model":            self._model,
            "is_stub":          self._backend == "stub",
            "available_models": self.list_models(),
            "origin_signature": ORIGIN_SIGNATURE,
        }

    def complete(
        self,
        prompt: str,
        *,
        max_tokens: int = 512,
        temperature: float = 0.7,
        stop: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Text-completion call.  Internally converts to a single-user chat message.
        """
        return self.chat(
            [{"role": "user", "content": prompt}],
            max_tokens=max_tokens,
            temperature=temperature,
            stop=stop,
        )

    def chat(
        self,
        messages: List[Dict[str, str]],
        *,
        max_tokens: int = 512,
        temperature: float = 0.7,
        stop: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Chat-completion call.

        Parameters
        ----------
        messages : list of {"role": "system"|"user"|"assistant", "content": str}
        """
        called_at = int(time.time() * 1000)
        t0 = time.time()

        if self._backend == "ollama":
            result = self._ollama_chat(messages, max_tokens, temperature, stop)
        elif self._backend == "llamacpp":
            result = self._llamacpp_chat(messages, max_tokens, temperature, stop)
        else:
            result = self._stub_chat(messages)

        result["elapsed_ms"] = int((time.time() - t0) * 1000)
        result["called_at_ms"] = called_at
        return result

    def stream_chat(
        self,
        messages: List[Dict[str, str]],
        *,
        max_tokens: int = 512,
        temperature: float = 0.7,
    ) -> Iterator[str]:
        """
        Streaming chat: yields text chunks as they arrive.
        Falls back to a single yield for stub/llamacpp.
        """
        if self._backend == "ollama":
            yield from self._ollama_stream(messages, max_tokens, temperature)
        else:
            resp = self.chat(messages, max_tokens=max_tokens, temperature=temperature)
            yield resp["text"]

    # ── Backend implementations ───────────────────────────────────────────────

    def _ollama_chat(
        self,
        messages: List[Dict[str, str]],
        max_tokens: int,
        temperature: float,
        stop: Optional[List[str]],
    ) -> Dict[str, Any]:
        try:
            payload: Dict[str, Any] = {
                "model": self._model,
                "messages": messages,
                "stream": False,
                "options": {
                    "num_predict": max_tokens,
                    "temperature": temperature,
                },
            }
            if stop:
                payload["options"]["stop"] = stop

            data = _with_retry(
                _http_post,
                f"{self._ollama_base}/api/chat",
                payload,
                timeout=self._timeout,
            )
            text = (data.get("message") or {}).get("content", "")
            p_tok = data.get("prompt_eval_count", 0)
            c_tok = data.get("eval_count", 0)
            return _make_response(True, text, self._model, "ollama", p_tok, c_tok)
        except Exception as exc:
            return _make_response(False, "", self._model, "ollama", error=str(exc))

    def _ollama_stream(
        self,
        messages: List[Dict[str, str]],
        max_tokens: int,
        temperature: float,
    ) -> Iterator[str]:
        payload: Dict[str, Any] = {
            "model": self._model,
            "messages": messages,
            "stream": True,
            "options": {"num_predict": max_tokens, "temperature": temperature},
        }
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        req = urllib.request.Request(
            f"{self._ollama_base}/api/chat",
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=self._timeout) as resp:
                for raw_line in resp:
                    line = raw_line.decode("utf-8").strip()
                    if not line:
                        continue
                    try:
                        obj = json.loads(line)
                        chunk = (obj.get("message") or {}).get("content", "")
                        if chunk:
                            yield chunk
                        if obj.get("done"):
                            break
                    except json.JSONDecodeError:
                        continue
        except Exception as exc:
            yield f"[stream error: {exc}]"

    def _llamacpp_chat(
        self,
        messages: List[Dict[str, str]],
        max_tokens: int,
        temperature: float,
        stop: Optional[List[str]],
    ) -> Dict[str, Any]:
        """OpenAI-compatible /v1/chat/completions endpoint."""
        try:
            payload: Dict[str, Any] = {
                "model": self._model,
                "messages": messages,
                "max_tokens": max_tokens,
                "temperature": temperature,
            }
            if stop:
                payload["stop"] = stop

            data = _with_retry(
                _http_post,
                f"{self._llamacpp_base}/v1/chat/completions",
                payload,
                timeout=self._timeout,
            )
            choices = data.get("choices", [])
            text = (choices[0].get("message") or {}).get("content", "") if choices else ""
            usage = data.get("usage", {})
            return _make_response(
                True, text, self._model, "llamacpp",
                usage.get("prompt_tokens", 0),
                usage.get("completion_tokens", 0),
            )
        except Exception as exc:
            return _make_response(False, "", self._model, "llamacpp", error=str(exc))

    def _stub_chat(self, messages: List[Dict[str, str]]) -> Dict[str, Any]:
        last_user = next(
            (m["content"] for m in reversed(messages) if m.get("role") == "user"),
            "",
        )
        text = _stub_reply(last_user)
        return _make_response(True, text, "stub-model", "stub", len(last_user), len(text))


# ─── CLI ─────────────────────────────────────────────────────────────────────

def _cmd_status(_args: argparse.Namespace) -> None:
    gw = LLMGateway()
    print(f"backend : {gw.backend}")
    print(f"model   : {gw.model}")
    models = gw.list_models()
    print(f"models  : {models or ['(none)']}")


def _cmd_chat(args: argparse.Namespace) -> None:
    gw = LLMGateway(
        backend=args.backend or None,
        model=args.model or None,
    )
    messages = [{"role": "user", "content": args.msg}]
    if args.system:
        messages.insert(0, {"role": "system", "content": args.system})
    resp = gw.chat(messages, max_tokens=args.max_tokens, temperature=args.temperature)
    print(json.dumps(resp, ensure_ascii=False, indent=2))


def _cmd_complete(args: argparse.Namespace) -> None:
    gw = LLMGateway(backend=args.backend or None, model=args.model or None)
    resp = gw.complete(args.prompt, max_tokens=args.max_tokens, temperature=args.temperature)
    print(json.dumps(resp, ensure_ascii=False, indent=2))


def _cmd_list_models(_args: argparse.Namespace) -> None:
    gw = LLMGateway()
    models = gw.list_models()
    print(f"Backend: {gw.backend}")
    for m in models:
        print(f"  {m}")


def _build_argparser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="LLMGateway — local-only LLM connector")
    p.add_argument("--backend", default="", help="Force backend: ollama | llamacpp | stub")
    p.add_argument("--model",   default="", help="Model name")
    sub = p.add_subparsers(dest="cmd", required=True)

    sub.add_parser("status", help="Show active backend and available models")
    sub.add_parser("list-models", help="List available local models")

    ch = sub.add_parser("chat", help="Send a chat message")
    ch.add_argument("--msg",         required=True, help="User message text")
    ch.add_argument("--system",      default="",    help="Optional system prompt")
    ch.add_argument("--max-tokens",  type=int,      default=512, dest="max_tokens")
    ch.add_argument("--temperature", type=float,    default=0.7)

    co = sub.add_parser("complete", help="Text completion")
    co.add_argument("--prompt",      required=True)
    co.add_argument("--max-tokens",  type=int,   default=512, dest="max_tokens")
    co.add_argument("--temperature", type=float, default=0.7)

    return p


def main() -> None:
    parser = _build_argparser()
    args = parser.parse_args()
    dispatch = {
        "status":      _cmd_status,
        "list-models": _cmd_list_models,
        "chat":        _cmd_chat,
        "complete":    _cmd_complete,
    }
    dispatch[args.cmd](args)


if __name__ == "__main__":
    main()
