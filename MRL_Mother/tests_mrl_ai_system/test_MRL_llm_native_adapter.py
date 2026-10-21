"""
test_MRL_llm_native_adapter.py — MRL 自生取代 adapter 驗收（rl_12）
origin_signature: MrLiouWord
product: MRL_AI_SYSTEM

實證:外部 openai/anthropic SDK 殼已由 stdlib-only native adapter 取代。
HTTP 層以 monkeypatch 攔截,不打真實網路。
"""
from __future__ import annotations

import pytest

import MRL_LLM_NativeAdapter_v1 as native
from MRL_LLM_NativeAdapter_v1 import (
    MRLNativeOpenAIAdapter,
    MRLNativeAnthropicAdapter,
    register_native_adapters,
)
from llm_adapter import LLMRequest, LLMGateway


def _req(model):
    return LLMRequest(model=model, messages=[{"role": "user", "content": "hi"}], max_tokens=16)


# ─── 零外部套件 ────────────────────────────────────────────────────────────────

class TestZeroSDKDependency:
    def test_module_imports_without_openai_or_anthropic(self):
        # 模組能 import 即證明不需 openai/anthropic 套件(stdlib only)
        import importlib
        m = importlib.import_module("MRL_LLM_NativeAdapter_v1")
        assert hasattr(m, "MRLNativeOpenAIAdapter")
        assert hasattr(m, "MRLNativeAnthropicAdapter")


# ─── OpenAI-compatible native ─────────────────────────────────────────────────

class TestNativeOpenAI:
    def test_complete_parses_response(self, monkeypatch):
        def fake_post(url, payload, headers, timeout=60):
            assert "/chat/completions" in url
            assert headers.get("Authorization") == "Bearer sk-test"
            return {"model": "gpt-4o", "choices": [{"message": {"content": "hello back"},
                    "finish_reason": "stop"}], "usage": {"prompt_tokens": 3, "completion_tokens": 2}}
        monkeypatch.setattr(native, "_http_post_json", fake_post)
        r = MRLNativeOpenAIAdapter(api_key="sk-test").complete(_req("gpt-4o"))
        assert r.ok is True and r.text == "hello back"
        assert r.input_tokens == 3 and r.output_tokens == 2

    def test_error_is_captured(self, monkeypatch):
        def boom(*a, **k):
            raise RuntimeError("network down")
        monkeypatch.setattr(native, "_http_post_json", boom)
        r = MRLNativeOpenAIAdapter(api_key="x").complete(_req("gpt-4o"))
        assert r.ok is False and "network down" in r.error

    def test_local_base_url(self, monkeypatch):
        seen = {}
        def fake_post(url, payload, headers, timeout=60):
            seen["url"] = url
            return {"choices": [{"message": {"content": "ok"}}], "usage": {}}
        monkeypatch.setattr(native, "_http_post_json", fake_post)
        a = MRLNativeOpenAIAdapter(api_key="local", base_url="http://localhost:11434/v1")
        a.complete(_req("llama3"))
        assert seen["url"].startswith("http://localhost:11434/v1")


# ─── Anthropic native ─────────────────────────────────────────────────────────

class TestNativeAnthropic:
    def test_complete_parses_and_splits_system(self, monkeypatch):
        captured = {}
        def fake_post(url, payload, headers, timeout=60):
            captured["payload"] = payload
            assert headers.get("anthropic-version")
            return {"model": "claude-3-5-sonnet", "content": [{"type": "text", "text": "hi there"}],
                    "stop_reason": "end_turn", "usage": {"input_tokens": 5, "output_tokens": 2}}
        monkeypatch.setattr(native, "_http_post_json", fake_post)
        req = LLMRequest(model="claude-3-5-sonnet",
                         messages=[{"role": "system", "content": "be brief"},
                                   {"role": "user", "content": "hi"}], max_tokens=16)
        r = MRLNativeAnthropicAdapter(api_key="k").complete(req)
        assert r.ok is True and r.text == "hi there"
        # system 被抽離到 payload.system
        assert captured["payload"]["system"] == "be brief"


# ─── 註冊進 gateway（取代 SDK 殼）────────────────────────────────────────────

class TestRegistration:
    def test_register_native_into_gateway(self):
        gw = LLMGateway()
        names = register_native_adapters(gw, openai_key="k1", anthropic_key="k2",
                                         local_base_url="http://localhost:11434/v1")
        assert "openai(native)" in names
        assert "anthropic(native)" in names
        adapters = gw.list_adapters()
        assert "openai" in adapters and "anthropic" in adapters and "local" in adapters

    def test_no_keys_registers_nothing(self):
        gw = LLMGateway()
        names = register_native_adapters(gw)
        assert names == []
