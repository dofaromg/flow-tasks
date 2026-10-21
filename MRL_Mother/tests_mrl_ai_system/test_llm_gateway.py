"""
test_llm_gateway.py — Smoke tests for llm_gateway.py (local backend gateway)
origin_signature: MrLiouWord
"""
from __future__ import annotations

import urllib.error

import pytest

from llm_gateway import LLMGateway, _with_retry, _stub_reply


# ─── Stub backend ─────────────────────────────────────────────────────────────

class TestStubBackend:
    """LLMGateway always falls back to stub when no local server is available."""

    def setup_method(self):
        # Force stub backend so tests never need a running server
        self.gw = LLMGateway(backend="stub")

    def test_backend_is_stub(self):
        assert self.gw.backend == "stub"

    def test_model_is_stub_model(self):
        assert self.gw.model == "stub-model"

    def test_chat_returns_ok(self):
        resp = self.gw.chat([{"role": "user", "content": "Hello"}])
        assert resp["ok"] is True
        assert isinstance(resp["text"], str)
        assert len(resp["text"]) > 0

    def test_complete_returns_ok(self):
        resp = self.gw.complete("What is 2+2?")
        assert resp["ok"] is True

    def test_list_models_returns_stub_model(self):
        models = self.gw.list_models()
        assert "stub-model" in models

    def test_response_contains_origin_signature(self):
        resp = self.gw.complete("ping")
        assert resp["origin_signature"] == "MrLiouWord"

    def test_response_contains_backend_field(self):
        resp = self.gw.complete("ping")
        assert resp["backend"] == "stub"

    def test_response_contains_elapsed_ms(self):
        resp = self.gw.complete("ping")
        assert "elapsed_ms" in resp
        assert resp["elapsed_ms"] >= 0

    def test_status_returns_dict(self):
        s = self.gw.status()
        assert s["backend"] == "stub"
        assert s["is_stub"] is True
        assert "available_models" in s
        assert s["origin_signature"] == "MrLiouWord"


# ─── Stream (stub) ────────────────────────────────────────────────────────────

class TestStreamStub:
    def test_stream_yields_text(self):
        gw = LLMGateway(backend="stub")
        chunks = list(gw.stream_chat([{"role": "user", "content": "hi"}]))
        assert len(chunks) >= 1
        assert all(isinstance(c, str) for c in chunks)


# ─── _stub_reply ──────────────────────────────────────────────────────────────

class TestStubReply:
    def test_returns_string(self):
        text = _stub_reply("Hello")
        assert isinstance(text, str)
        assert len(text) > 0

    def test_cycles_through_responses(self):
        replies = {_stub_reply(f"prompt {i}") for i in range(10)}
        # Multiple distinct replies (cycles through the list)
        assert len(replies) > 1


# ─── _with_retry ──────────────────────────────────────────────────────────────

class TestWithRetry:
    def test_succeeds_on_first_attempt(self):
        calls = []

        def fn():
            calls.append(1)
            return "ok"

        result = _with_retry(fn, max_retries=3)
        assert result == "ok"
        assert len(calls) == 1

    def test_retries_on_url_error(self):
        calls = []

        def fn():
            calls.append(1)
            if len(calls) < 3:
                raise urllib.error.URLError("connection refused")
            return "recovered"

        result = _with_retry(fn, max_retries=3)
        assert result == "recovered"
        assert len(calls) == 3

    def test_raises_after_max_retries(self):
        def fn():
            raise urllib.error.URLError("always fails")

        with pytest.raises(urllib.error.URLError):
            _with_retry(fn, max_retries=2)

    def test_does_not_retry_non_url_errors(self):
        calls = []

        def fn():
            calls.append(1)
            raise ValueError("not a network error")

        with pytest.raises(ValueError):
            _with_retry(fn, max_retries=3)
        assert len(calls) == 1
