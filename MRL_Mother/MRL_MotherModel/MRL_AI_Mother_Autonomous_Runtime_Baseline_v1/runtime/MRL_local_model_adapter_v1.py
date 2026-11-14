#!/usr/bin/env python3
"""Local-only model adapter for the MRL AI mother runtime.

The adapter intentionally accepts loopback endpoints only.  It speaks the
Ollama and OpenAI-compatible llama.cpp protocols with Python's standard
library, so the runtime does not require a cloud SDK or cloud model API.
"""

from __future__ import annotations

import http.client
import json
import re
import socket
from threading import Timer
from time import monotonic
from dataclasses import dataclass
from typing import Any
from urllib.parse import urlparse

from . import ORIGIN_SIGNATURE


MAX_RESPONSE_BYTES = 8 * 1024 * 1024
LOOPBACK_AUTHORITY = re.compile(
    r"(?:127\.0\.0\.1|localhost|\[::1\])(?::[0-9]{1,5})?", re.IGNORECASE | re.ASCII,
)


class MRLModelGateError(RuntimeError):
    """A local model failure with a stable code and a safe message."""

    def __init__(self, message: str, *, code: str = "BACKEND_INVALID_RESPONSE") -> None:
        super().__init__(message)
        self.code = code


def require_loopback_endpoint(endpoint: str) -> str:
    """Return a normalized endpoint or reject non-loopback model traffic."""
    if not isinstance(endpoint, str) or any(ord(char) <= 32 or ord(char) == 127 for char in endpoint):
        raise MRLModelGateError("invalid local model endpoint", code="EGRESS_DENIED")
    try:
        parsed = urlparse(endpoint)
        port = parsed.port
    except ValueError:
        raise MRLModelGateError("invalid local model endpoint", code="EGRESS_DENIED") from None
    if parsed.scheme not in {"http", "https"}:
        raise MRLModelGateError("model endpoint must use http or https", code="EGRESS_DENIED")
    if (
        not LOOPBACK_AUTHORITY.fullmatch(parsed.netloc)
        or port == 0
        or any(char in endpoint for char in ("?", "#", "\\"))
    ):
        raise MRLModelGateError(
            "AUTONOMY_GATE_REJECTED: model endpoint must be loopback-local",
            code="EGRESS_DENIED",
        )
    return endpoint.rstrip("/")


def _remaining_timeout(timeout: float, deadline: float | None) -> float:
    if deadline is not None:
        timeout = min(timeout, deadline - monotonic())
    if timeout <= 0:
        raise MRLModelGateError("local model deadline has elapsed", code="BACKEND_TIMEOUT")
    return timeout


class _LocalConnection:
    """Pin accepted hostnames and apply a wall-clock deadline to a connected socket."""

    def __init__(self, host: str, port: int | None, timeout: float, deadline: float) -> None:
        super().__init__(host, port, timeout=timeout)
        self.deadline = deadline
        self.expired = False
        self.timer: Timer | None = None
        # HTTPResponse closes the connection for Connection: close. Retain a
        # separate descriptor for shutdown until the complete body is read.
        self.watch_socket: socket.socket | None = None
        self._create_connection = self._connect_loopback

    def _connect_loopback(self, address, timeout, source_address):
        host, port = address
        addresses = ("127.0.0.1", "::1") if host.lower() == "localhost" else (host,)
        for candidate in addresses:
            try:
                connected = socket.create_connection(
                    (candidate, port), _remaining_timeout(timeout, self.deadline), source_address,
                )
                break
            except ConnectionRefusedError:
                if candidate == addresses[-1]:
                    raise
        try:
            self.watch_socket = connected.dup()
            self.timer = Timer(_remaining_timeout(timeout, self.deadline), self._expire)
            self.timer.daemon = True
            self.timer.start()
        except (OSError, MRLModelGateError):
            connected.close()
            raise
        return connected

    def _expire(self) -> None:
        self.expired = True
        if self.watch_socket is not None:
            try:
                self.watch_socket.shutdown(socket.SHUT_RDWR)
            except OSError:
                pass

    def finish(self) -> None:
        if self.timer is not None:
            self.timer.cancel()
        if self.watch_socket is not None:
            self.watch_socket.close()
        self.close()


class _LoopbackHTTPConnection(_LocalConnection, http.client.HTTPConnection):
    pass


class _LoopbackHTTPSConnection(_LocalConnection, http.client.HTTPSConnection):
    pass


def _unique_json_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    value = dict(pairs)
    if len(value) != len(pairs):
        raise ValueError("duplicate keys in model response")
    return value


def _json_request(
    url: str, payload: dict[str, Any] | None, timeout: float, *, deadline: float | None = None,
) -> dict[str, Any]:
    require_loopback_endpoint(url)
    parsed = urlparse(url)
    timeout = _remaining_timeout(timeout, deadline)
    stop = monotonic() + timeout
    if deadline is not None:
        stop = min(stop, deadline)
    connection_type = _LoopbackHTTPSConnection if parsed.scheme == "https" else _LoopbackHTTPConnection
    connection = connection_type(parsed.hostname, parsed.port, timeout, stop)
    try:
        data = None if payload is None else json.dumps(payload).encode("utf-8")
        connection.request(
            "GET" if payload is None else "POST", parsed.path or "/", body=data,
            headers={"Accept": "application/json", "Content-Type": "application/json", "Connection": "close"},
        )
        with connection.getresponse() as response:
            if 300 <= response.status < 400:
                raise MRLModelGateError("local model redirect rejected", code="BACKEND_REDIRECT_REJECTED")
            if not 200 <= response.status < 300:
                raise MRLModelGateError("local model response status rejected", code="BACKEND_HTTP_ERROR")
            length = response.length
            if length is not None and length > MAX_RESPONSE_BYTES:
                raise MRLModelGateError("local model response exceeds the size limit")
            raw = response.read(MAX_RESPONSE_BYTES + 1)
            if connection.expired or monotonic() >= stop:
                raise MRLModelGateError("local model deadline has elapsed", code="BACKEND_TIMEOUT")
            if length is not None and len(raw) != length:
                raise MRLModelGateError("local model returned a truncated response")
    except (OSError, http.client.HTTPException) as error:
        if connection.expired or monotonic() >= stop or isinstance(error, TimeoutError):
            raise MRLModelGateError("local model deadline has elapsed", code="BACKEND_TIMEOUT") from None
        if isinstance(error, http.client.IncompleteRead):
            raise MRLModelGateError("local model returned a truncated response") from None
        raise MRLModelGateError("local model connection failed", code="BACKEND_UNAVAILABLE") from None
    finally:
        connection.finish()
    if len(raw) > MAX_RESPONSE_BYTES:
        raise MRLModelGateError("local model response exceeds the size limit")
    try:
        decoded = json.loads(raw.decode("utf-8"), object_pairs_hook=_unique_json_object)
    except (ValueError, RecursionError):
        raise MRLModelGateError("invalid JSON from local model") from None
    if not isinstance(decoded, dict) or "error" in decoded:
        raise MRLModelGateError("local model returned an invalid response envelope")
    if monotonic() >= stop:
        raise MRLModelGateError("local model deadline has elapsed", code="BACKEND_TIMEOUT")
    return decoded


def _token_count(value: Any) -> int | None:
    return value if type(value) is int and 0 <= value <= 2**53 - 1 else None


@dataclass(frozen=True)
class MRLLocalModelAdapter:
    """A strict local inference adapter for Ollama or llama.cpp."""

    backend: str
    endpoint: str
    model: str
    timeout_seconds: float = 120

    def __post_init__(self) -> None:
        if self.backend not in {"ollama", "llamacpp"}:
            raise MRLModelGateError("backend must be ollama or llamacpp", code="INVALID_CONFIGURATION")
        object.__setattr__(self, "endpoint", require_loopback_endpoint(self.endpoint))
        if not isinstance(self.model, str) or not self.model.strip():
            raise MRLModelGateError("model must be explicit", code="INVALID_CONFIGURATION")
        if self.backend == "ollama" and self._ollama_remote_model(self.model):
            raise MRLModelGateError("local model configuration selected a cloud alias", code="EGRESS_DENIED")

    @staticmethod
    def _ollama_remote_model(name: str) -> bool:
        return name.strip().lower().endswith(("-cloud", ":cloud"))

    def _inventory(self, *, deadline: float | None = None) -> tuple[set[str], list[str]]:
        ollama = self.backend == "ollama"
        path = "/api/tags" if ollama else "/v1/models"
        response = _json_request(f"{self.endpoint}{path}", None, 5, deadline=deadline)
        models = response.get("models" if ollama else "data")
        if not isinstance(models, list):
            raise MRLModelGateError("local model returned an invalid model inventory")
        available, denied = set(), set()
        for item in models:
            if not isinstance(item, dict):
                raise MRLModelGateError("local model returned an invalid inventory entry")
            names = [item[key] for key in (("name", "model") if ollama else ("id",)) if key in item]
            if not names or any(not isinstance(name, str) or not name.strip() for name in names):
                raise MRLModelGateError("local model returned an invalid model name")
            remote = any(item.get(field) for field in (
                "remote_host", "remote_model", "remoteHost", "remoteModel",
            ))
            if remote or (ollama and any(self._ollama_remote_model(name) for name in names)):
                denied.update(names)
            else:
                available.update(names)
        if self.model in denied:
            raise MRLModelGateError("configured model advertises a remote target", code="EGRESS_DENIED")
        return available - denied, sorted(response)

    def models(self, *, deadline: float | None = None) -> list[str]:
        """Return model names reported by the local endpoint."""
        available, _ = self._inventory(deadline=deadline)
        return sorted(available)

    def require_local_model(self, *, deadline: float | None = None) -> None:
        """Reject missing models and verify Ollama aliases before sending messages."""
        if self.model not in self.models(deadline=deadline):
            raise MRLModelGateError("configured local model is not available", code="MODEL_UNAVAILABLE")
        if self.backend == "ollama":
            details = _json_request(
                f"{self.endpoint}/api/show", {"model": self.model}, 5, deadline=deadline,
            )
            if any(details.get(field) for field in ("remote_host", "remote_model", "remoteHost", "remoteModel")):
                raise MRLModelGateError("configured model advertises a remote target", code="EGRESS_DENIED")
            if isinstance(details.get("capabilities"), list) and "cloud" in details["capabilities"]:
                raise MRLModelGateError("configured model advertises cloud inference", code="EGRESS_DENIED")
            info, model_info = details.get("details"), details.get("model_info")
            if not (
                isinstance(info, dict) and info.get("format") == "gguf"
                and isinstance(model_info, dict) and model_info
            ):
                raise MRLModelGateError("local model metadata is unverified", code="MODEL_LOCALITY_UNKNOWN")

    def health(self) -> dict[str, Any]:
        """Probe the local model server without contacting an external host."""
        result = {
            "backend": self.backend,
            "model": self.model,
            "endpoint": self.endpoint,
            "external_model_required": False,
            "origin_signature": ORIGIN_SIGNATURE,
        }
        try:
            available, response_keys = self._inventory()
            if self.model not in available:
                raise MRLModelGateError("configured local model is not available", code="MODEL_UNAVAILABLE")
            return {**result, "ready": True, "response_keys": response_keys}
        except MRLModelGateError as exc:
            return {**result, "ready": False, "error": f"{type(exc).__name__}: {exc}"}

    def complete(
        self, messages: list[dict[str, str]], *, report_missing_usage: bool = False,
        deadline: float | None = None,
    ) -> dict[str, Any]:
        """Generate using the existing protocols and normalize into an MRL envelope."""
        if not messages:
            raise MRLModelGateError("messages must not be empty", code="INVALID_REQUEST")
        ollama = self.backend == "ollama"
        path = "/api/chat" if ollama else "/v1/chat/completions"
        payload = {"model": self.model, "messages": messages, "stream": False}
        response = _json_request(
            f"{self.endpoint}{path}", payload, self.timeout_seconds, deadline=deadline,
        )
        if ollama:
            message = response.get("message")
            token_fields = response
            input_key, output_key = "prompt_eval_count", "eval_count"
        else:
            choices = response.get("choices")
            first = choices[0] if isinstance(choices, list) and choices else None
            message = first.get("message") if isinstance(first, dict) else None
            token_fields = response.get("usage")
            input_key, output_key = "prompt_tokens", "completion_tokens"
        text = message.get("content") if isinstance(message, dict) else None
        if not isinstance(text, str) or not text.strip():
            raise MRLModelGateError("local model returned missing or invalid text")
        tokens = token_fields if isinstance(token_fields, dict) else {}
        usage = {
            "input_tokens": _token_count(tokens.get(input_key)),
            "output_tokens": _token_count(tokens.get(output_key)),
        }
        if not report_missing_usage:
            usage = {name: count if count is not None else 0 for name, count in usage.items()}
        return {
            "text": text,
            "backend": self.backend,
            "model": self.model,
            "usage": usage,
            "external_model_required": False,
            "origin_signature": ORIGIN_SIGNATURE,
        }
