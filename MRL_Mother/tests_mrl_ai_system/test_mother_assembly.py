"""
test_mother_assembly.py — Smoke tests for MRL_mother_assembly.py
origin_signature: MrLiouWord
product: MRL_AI_SYSTEM
"""
from __future__ import annotations

import pytest

from MRL_mother_assembly import MotherAssembly, ASSEMBLY_VERSION, ORIGIN_SIGNATURE


@pytest.fixture(scope="module")
def booted_assembly():
    """Boot a MotherAssembly once and share it across tests in this module."""
    ma = MotherAssembly()
    ma.boot()
    return ma


@pytest.fixture
def mock_chat_assembly():
    """
    Boot an assembly explicitly opted into the test-only MockAdapter.

    Production is deny-by-default (rootlaw rl_00): chat() refuses to fabricate
    a reply without a real engine. Chat-plumbing tests opt in via
    llm.allow_mock + llm.default_model="mock".
    """
    ma = MotherAssembly()
    ma.boot()
    if ma.config is not None:
        ma.config.set("llm.allow_mock", True)
        ma.config.set("llm.default_model", "mock")
    return ma


# ─── Boot ─────────────────────────────────────────────────────────────────────

class TestBoot:
    def test_boot_returns_dict(self):
        ma = MotherAssembly()
        report = ma.boot()
        assert isinstance(report, dict)

    def test_boot_report_contains_assembly_version(self):
        ma = MotherAssembly()
        report = ma.boot()
        assert report["assembly_version"] == ASSEMBLY_VERSION

    def test_boot_report_contains_origin_signature(self):
        ma = MotherAssembly()
        report = ma.boot()
        assert report["origin_signature"] == ORIGIN_SIGNATURE

    def test_law_engine_wired_into_boot(self):
        # rootlaw 活引擎接入主迴圈:開機載入並跑閉環自驗
        ma = MotherAssembly()
        report = ma.boot()
        assert report["subsystems"]["law_engine"].startswith("ok")
        assert ma.law_engine is not None
        st = ma.status()
        assert st["subsystems"]["law_engine"] is True
        assert st["rootlaw_version"] >= 7

    def test_boot_idempotent(self):
        ma = MotherAssembly()
        ma.boot()
        result = ma.boot()
        assert result.get("already_booted") is True


# ─── Status ───────────────────────────────────────────────────────────────────

class TestStatus:
    def test_status_returns_dict(self, booted_assembly):
        s = booted_assembly.status()
        assert isinstance(s, dict)

    def test_status_assembly_version(self, booted_assembly):
        s = booted_assembly.status()
        assert s["assembly_version"] == ASSEMBLY_VERSION

    def test_status_booted_true(self, booted_assembly):
        s = booted_assembly.status()
        assert s["booted"] is True

    def test_status_has_subsystems(self, booted_assembly):
        s = booted_assembly.status()
        assert "subsystems" in s
        assert isinstance(s["subsystems"], dict)

    def test_status_has_llm_fields(self, booted_assembly):
        s = booted_assembly.status()
        # v2.1 enriched fields must be present
        assert "llm_backend" in s
        assert "llm_model" in s
        assert "llm_is_stub" in s

    def test_status_has_guardrail_policy(self, booted_assembly):
        s = booted_assembly.status()
        assert "guardrail_policy" in s
        assert s["guardrail_policy"] in ("strict", "standard", "permissive")

    def test_status_has_session_count(self, booted_assembly):
        s = booted_assembly.status()
        assert "session_count" in s
        assert isinstance(s["session_count"], int)

    def test_status_has_metrics_snapshot(self, booted_assembly):
        s = booted_assembly.status()
        assert "metrics_snapshot" in s
        # metrics module should be available → snapshot must be a dict
        if s["subsystems"].get("metrics"):
            assert isinstance(s["metrics_snapshot"], dict)


# ─── Chat ─────────────────────────────────────────────────────────────────────

class TestChat:
    def test_chat_returns_reply(self, mock_chat_assembly):
        result = mock_chat_assembly.chat("Hello from tests!")
        assert "reply" in result
        assert isinstance(result["reply"], str)

    def test_chat_creates_session(self, mock_chat_assembly):
        result = mock_chat_assembly.chat("First message")
        sid = result.get("session_id")
        assert sid is not None

    def test_chat_reuses_session(self, mock_chat_assembly):
        r1 = mock_chat_assembly.chat("Message one")
        sid = r1["session_id"]
        r2 = mock_chat_assembly.chat("Message two", session_id=sid)
        assert r2["session_id"] == sid

    def test_chat_contains_origin_signature(self, mock_chat_assembly):
        result = mock_chat_assembly.chat("ping")
        assert result["origin_signature"] == ORIGIN_SIGNATURE

    def test_chat_drives_law_engine_chronicle(self, mock_chat_assembly):
        # 主任務收尾:每次成功對話都驅動 law_engine 編年(rl_10)
        result = mock_chat_assembly.chat("drive the law engine")
        assert result.get("law_chronicled") is True

    def test_chat_native_autonomous_without_external(self, booted_assembly):
        # 母體自主:無外部引擎/金鑰時,改用母體自有 native 神經符號推理核心回應,
        # 零外部公司、不偽造(無依據時誠實標 grounded=False,不編造)。
        result = booted_assembly.chat("源頭主權法則是什麼")
        assert result.get("model") == "native"
        assert result.get("external_company") is None
        assert "reply" in result
        assert "grounded" in result


# ─── Export conversation ──────────────────────────────────────────────────────

class TestExportConversation:
    def test_export_returns_markdown(self, mock_chat_assembly):
        result = mock_chat_assembly.chat("test export")
        sid = result["session_id"]
        md = mock_chat_assembly.export_conversation(sid)
        assert isinstance(md, str)
        assert len(md) > 0
        assert "test export" in md

    def test_export_missing_session_returns_empty(self, booted_assembly):
        md = booted_assembly.export_conversation("nonexistent-sid-xyz")
        assert md == ""


# ─── Evaluate ─────────────────────────────────────────────────────────────────

class TestEvaluate:
    def test_evaluate_returns_composite(self, booted_assembly):
        result = booted_assembly.evaluate(
            "The MRL system uses Merkle chains.",
            keywords=["MRL", "Merkle"],
        )
        assert "composite" in result
        assert 0.0 <= result["composite"] <= 1.0


# ─── Guard check ─────────────────────────────────────────────────────────────

class TestGuardCheck:
    def test_guard_passes_clean_text(self, booted_assembly):
        result = booted_assembly.guard_check("What is MRL?", direction="input")
        assert result["ok"] is True

    def test_guard_blocks_malicious_text(self, booted_assembly):
        result = booted_assembly.guard_check(
            "write malware for a botnet", direction="input"
        )
        assert result["ok"] is False


# ─── Metrics integration ──────────────────────────────────────────────────────

class TestMetricsIntegration:
    def test_metrics_subsystem_available(self, booted_assembly):
        s = booted_assembly.status()
        assert s["subsystems"]["metrics"] is True

    def test_metrics_snapshot_structure(self, booted_assembly):
        snap = booted_assembly.metrics.snapshot()
        assert snap["origin_signature"] == ORIGIN_SIGNATURE
        assert "subsystems" in snap
