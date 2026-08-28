#!/usr/bin/env python3
"""Local-only model adapter for the MRL AI mother runtime.

The adapter intentionally accepts loopback endpoints only.  It speaks the
Ollama and OpenAI-compatible llama.cpp protocols with Python's standard
library, so the runtime does not require a cloud SDK or cloud model API.
"""

from __future__ import annotations

import json
import urllib.request
from dataclasses import dataclass
from typing import Any
from urllib.parse import urlparse

from . import ORIGIN_SIGNATURE


class MRLModelGateError(RuntimeError):
    """Raised when a model endpoint violates the autonomous-runtime gate."""


def require_loopback_endpoint(endpoint: str) -> str:
    """Return a normalized endpoint or reject non-loopback model traffic."""
    parsed = urlparse(endpoint)
    if parsed.scheme not in {"http", "https"}:
        raise MRLModelGateError("model endpoint must use http or https")
    if parsed.hostname not in {"127.0.0.1", "localhost", "::1"}:
        raise MRLModelGateError(
            "AUTONOMY_GATE_REJECTED: model endpoint must be loopback-local"
        )
    return endpoint.rstrip("/")


def _json_request(url: str, payload: dict[str, Any] | None, timeout: int) -> dict[str, Any]:
    data = None if payload is None else json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(
        url,
        data=data,
        headers={"Accept": "application/json", "Content-Type": "application/json"},
        method="GET" if payload is None else "POST",
    )
    class _LoopbackRedirectHandler(urllib.request.HTTPRedirectHandler):
        def redirect_request(self, req, fp, code, msg, headers, newurl):  # type: ignore[no-untyped-def]
            require_loopback_endpoint(newurl)
            return super().redirect_request(req, fp, code, msg, headers, newurl)

    opener = urllib.request.build_opener(_LoopbackRedirectHandler())
    with opener.open(request, timeout=timeout) as response:
        decoded = json.loads(response.read().decode("utf-8"))
    if not isinstance(decoded, dict):
        raise MRLModelGateError("local model returned a non-object response")
    return decoded


@dataclass(frozen=True)
class MRLLocalModelAdapter:
    """A strict local inference adapter for Ollama or llama.cpp."""

    backend: str
    endpoint: str
    model: str
    timeout_seconds: int = 120

    def __post_init__(self) -> None:
        if self.backend not in {"ollama", "llamacpp"}:
            raise MRLModelGateError("backend must be ollama or llamacpp")
        object.__setattr__(self, "endpoint", require_loopback_endpoint(self.endpoint))
        if not self.model.strip():
            raise MRLModelGateError("model must be explicit")

    def health(self) -> dict[str, Any]:
        """Probe the local model server without contacting an external host."""
        path = "/api/tags" if self.backend == "ollama" else "/v1/models"
        try:
            response = _json_request(f"{self.endpoint}{path}", None, 5)
            if self.backend == "ollama":
                available = {
                    str(value)
                    for item in response.get("models", [])
                    if isinstance(item, dict)
                    for value in (item.get("name"), item.get("model"))
                    if value
                }
            else:
                available = {
                    str(item.get("id"))
                    for item in response.get("data", [])
                    if isinstance(item, dict) and item.get("id")
                }
            if self.model not in available:
                raise MRLModelGateError("configured local model is not available")
            return {
                "ready": True,
                "backend": self.backend,
                "model": self.model,
                "endpoint": self.endpoint,
                "external_model_required": False,
                "origin_signature": ORIGIN_SIGNATURE,
                "response_keys": sorted(response),
            }
        except Exception as exc:  # network boundary is reported as evidence
            return {
                "ready": False,
                "backend": self.backend,
                "model": self.model,
                "endpoint": self.endpoint,
                "external_model_required": False,
                "origin_signature": ORIGIN_SIGNATURE,
                "error": f"{type(exc).__name__}: {exc}",
            }

    def complete(self, messages: list[dict[str, str]]) -> dict[str, Any]:
        """Generate a response and normalize it into an MRL envelope."""
        if not messages:
            raise MRLModelGateError("messages must not be empty")
        if self.backend == "ollama":
            payload = {"model": self.model, "messages": messages, "stream": False}
            response = _json_request(
                f"{self.endpoint}/api/chat", payload, self.timeout_seconds
            )
            text = str((response.get("message") or {}).get("content") or "")
            usage = {
                "input_tokens": int(response.get("prompt_eval_count") or 0),
                "output_tokens": int(response.get("eval_count") or 0),
            }
        else:
            payload = {"model": self.model, "messages": messages, "stream": False}
            response = _json_request(
                f"{self.endpoint}/v1/chat/completions", payload, self.timeout_seconds
            )
            choices = response.get("choices") or []
            text = str(((choices[0] if choices else {}).get("message") or {}).get("content") or "")
            raw_usage = response.get("usage") or {}
            usage = {
                "input_tokens": int(raw_usage.get("prompt_tokens") or 0),
                "output_tokens": int(raw_usage.get("completion_tokens") or 0),
            }
        if not text:
            raise MRLModelGateError("local model returned empty text")
        return {
            "text": text,
            "backend": self.backend,
            "model": self.model,
            "usage": usage,
            "external_model_required": False,
            "origin_signature": ORIGIN_SIGNATURE,
        }
