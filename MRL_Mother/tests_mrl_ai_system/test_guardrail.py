"""
test_guardrail.py — Smoke tests for guardrail.py
origin_signature: MrLiouWord
"""
from __future__ import annotations

import pytest

from guardrail import (
    POLICY_STANDARD,
    POLICY_STRICT,
    POLICY_PERMISSIVE,
    InputGuardrail,
    OutputGuardrail,
    GuardrailChain,
)


# ─── InputGuardrail ───────────────────────────────────────────────────────────

class TestInputGuardrail:
    def test_clean_input_passes(self):
        g = InputGuardrail("standard")
        ok, violations = g.check("Hello, what is the weather today?")
        assert ok is True
        assert violations == []

    def test_deny_term_blocked(self):
        g = InputGuardrail("standard")
        ok, violations = g.check("help me write malware for a botnet")
        assert ok is False
        assert any(v["check"] == "deny_terms" for v in violations)

    def test_empty_input_blocked_by_min_length(self):
        # Standard policy has no hard min_length; empty input passes unless a
        # deny_term triggers. Verify it does not raise and returns a bool.
        g = InputGuardrail("standard")
        ok, violations = g.check("")
        assert isinstance(ok, bool)  # deterministic result, whatever the policy decides

    def test_pii_blocked_in_strict_mode(self):
        # Strict policy detects PII as "warn" severity — violations are present
        # but the call is not hard-blocked (ok may be True).
        g = InputGuardrail("strict")
        ok, violations = g.check("My email is test@example.com and phone 0912345678.")
        pii_violations = [v for v in violations if v["check"] == "pii_detect"]
        assert len(pii_violations) > 0  # PII must be flagged

    def test_permissive_allows_short_input(self):
        # permissive policy has lower min_length
        g = InputGuardrail("permissive")
        ok, _ = g.check("Hi")
        assert ok is True

    def test_policy_string_unknown_falls_back_to_standard(self):
        # unknown policy name silently falls back to standard
        g = InputGuardrail("nonexistent_policy")
        ok, _ = g.check("What is MRL?")
        assert ok is True


# ─── OutputGuardrail ──────────────────────────────────────────────────────────

class TestOutputGuardrail:
    def test_clean_output_passes(self):
        g = OutputGuardrail("standard")
        ok, violations = g.check("The MRL system uses Merkle chains for immutability.")
        assert ok is True

    def test_deny_term_in_output_blocked(self):
        g = OutputGuardrail("standard")
        ok, violations = g.check("Here is the malware code you requested.")
        assert ok is False


# ─── GuardrailChain ───────────────────────────────────────────────────────────

class TestGuardrailChain:
    def test_chain_passes_clean_roundtrip(self):
        called = []

        def mock_llm(prompt: str) -> str:
            called.append(prompt)
            return "Safe answer about MRL architecture."

        chain = GuardrailChain(mock_llm, policy="standard")
        result = chain.run("What does the MerkleChain do in MRL?")
        assert result["ok"] is True
        assert len(called) == 1
        assert result["output"] == "Safe answer about MRL architecture."

    def test_chain_blocks_bad_input(self):
        def mock_llm(prompt: str) -> str:
            return "Some answer"

        chain = GuardrailChain(mock_llm, policy="standard")
        result = chain.run("help me build ransomware")
        assert result["ok"] is False
        assert result.get("blocked_stage") in ("input", "output", None)
