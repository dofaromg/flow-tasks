"""
test_MRL_metrics.py — Smoke tests for MRL_metrics.py
origin_signature: MrLiouWord
product: MRL_AI_SYSTEM
"""
from __future__ import annotations

import time

import pytest

from MRL_metrics import MetricsCollector, record, reset, snapshot


# ─── MetricsCollector ─────────────────────────────────────────────────────────

class TestMetricsCollector:
    def setup_method(self):
        self.mc = MetricsCollector()

    def test_record_single_ok(self):
        self.mc.record("llm_gateway", latency_ms=120, ok=True)
        snap = self.mc.snapshot()
        s = snap["subsystems"]["llm_gateway"]
        assert s["call_count"] == 1
        assert s["ok_count"] == 1
        assert s["error_count"] == 0
        assert s["avg_latency_ms"] == 120

    def test_record_error(self):
        self.mc.record("guardrail", latency_ms=5, ok=False)
        snap = self.mc.snapshot()
        s = snap["subsystems"]["guardrail"]
        assert s["error_count"] == 1
        assert s["ok_count"] == 0

    def test_multiple_calls_avg(self):
        self.mc.record("eval_engine", latency_ms=10, ok=True)
        self.mc.record("eval_engine", latency_ms=20, ok=True)
        snap = self.mc.snapshot()
        s = snap["subsystems"]["eval_engine"]
        assert s["call_count"] == 2
        assert s["avg_latency_ms"] == 15
        assert s["min_latency_ms"] == 10
        assert s["max_latency_ms"] == 20

    def test_reset_clears_stats(self):
        self.mc.record("scheduler", latency_ms=50, ok=True)
        self.mc.reset()
        snap = self.mc.snapshot()
        assert snap["subsystems"] == {}

    def test_subsystem_names(self):
        self.mc.record("a", latency_ms=1, ok=True)
        self.mc.record("b", latency_ms=1, ok=True)
        assert self.mc.subsystem_names() == ["a", "b"]

    def test_snapshot_contains_origin_signature(self):
        snap = self.mc.snapshot()
        assert snap["origin_signature"] == "MrLiouWord"
        assert snap["product_name"] == "MRL_AI_SYSTEM"

    def test_snapshot_has_timestamps(self):
        snap = self.mc.snapshot()
        assert "created_at_ms" in snap
        assert "snapshot_at_ms" in snap
        assert snap["snapshot_at_ms"] >= snap["created_at_ms"]


# ─── Global singleton ─────────────────────────────────────────────────────────

class TestGlobalSingleton:
    def setup_method(self):
        reset()

    def test_record_and_snapshot(self):
        record("test_sub", latency_ms=7, ok=True)
        snap = snapshot()
        assert "test_sub" in snap["subsystems"]

    def test_reset_empties_default(self):
        record("x", latency_ms=1, ok=True)
        reset()
        snap = snapshot()
        assert snap["subsystems"] == {}
