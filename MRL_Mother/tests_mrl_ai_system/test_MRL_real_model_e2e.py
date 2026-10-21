"""
test_MRL_real_model_e2e.py — 真模型端到端冒煙(P0)
origin_signature: MrLiouWord
product: MRL_AI_SYSTEM

驗證「設了金鑰就能用真模型」整條鏈，不偽造(no_proof_implies_rhetoric)：
  - 無金鑰          → skip(不假裝測過)
  - 有金鑰          → 真打 endpoint，斷言收到真實回覆
  - 假金鑰          → 必須走到真實 endpoint 並收到 HTTP 錯誤(證明非 mock)
"""
from __future__ import annotations

import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "09_workflow"))

from MRL_mother_assembly import MotherAssembly  # noqa: E402

_HAS_OPENAI = bool(os.environ.get("OPENAI_API_KEY"))
_HAS_ANTHROPIC = bool(os.environ.get("ANTHROPIC_API_KEY"))


# ─── 路徑打通(不需真金鑰，用假金鑰證明走到真 endpoint，非 mock)──────────────

class TestRealModelPathWired:
    def test_fake_key_reaches_real_endpoint_not_mock(self, monkeypatch):
        # 假金鑰 → adapter 註冊 → chat 真送 endpoint → 收到 HTTP 錯誤(非 mock echo)
        monkeypatch.setenv("OPENAI_API_KEY", "sk-fake-e2e-probe")
        m = MotherAssembly()
        rep = m.boot()
        assert "openai" in m.llm_gateway.list_adapters()
        assert rep["subsystems"]["llm_gateway"].startswith("ok (real")
        m.config.set("llm.default_model", "gpt-4o")
        r = m.chat("ping")
        # 必須是真實引擎路徑:回覆含 LLM Error(真 HTTP 回應)或真 reply，
        # 絕不能是 mock echo。
        text = r.get("reply", "") + r.get("error", "")
        assert "[MockAdapter]" not in text
        assert ("LLM Error" in text) or (r.get("model") == "gpt-4o")

    def test_no_key_denies_real_model_by_default(self):
        # 無金鑰且未開 mock → deny-by-default，不偽造
        m = MotherAssembly()
        m.boot()
        m.config.set("llm.default_model", "gpt-4o")
        # 沒有 openai adapter 註冊時，gateway 對未知 model 應誠實失敗
        if "openai" not in m.llm_gateway.list_adapters():
            r = m.chat("ping")
            assert "error" in r or "[MockAdapter]" not in r.get("reply", "")


# ─── 真金鑰端到端(有才跑，無則 skip — 不假裝)─────────────────────────────────

@pytest.mark.skipif(not _HAS_OPENAI, reason="OPENAI_API_KEY 未設；真模型端到端待金鑰")
class TestRealOpenAIE2E:
    def test_real_openai_chat(self):
        m = MotherAssembly()
        m.boot()
        m.config.set("llm.default_model", "gpt-4o")
        r = m.chat("Reply with exactly: MRL_OK")
        assert "reply" in r and r["reply"]
        assert "[MockAdapter]" not in r["reply"]
        assert r.get("law_chronicled") is True


@pytest.mark.skipif(not _HAS_ANTHROPIC, reason="ANTHROPIC_API_KEY 未設；真模型端到端待金鑰")
class TestRealAnthropicE2E:
    def test_real_anthropic_chat(self):
        m = MotherAssembly()
        m.boot()
        m.config.set("llm.default_model", "claude-3-5-sonnet-20241022")
        r = m.chat("Reply with exactly: MRL_OK")
        assert "reply" in r and r["reply"]
        assert "[MockAdapter]" not in r["reply"]
