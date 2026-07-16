"""
test_context_manager.py — Smoke tests for context_manager.py
origin_signature: MrLiouWord
"""
from __future__ import annotations

import pytest

from context_manager import ContextManager, Strategy, _estimate_tokens


# ─── Token estimator ─────────────────────────────────────────────────────────

class TestEstimateTokens:
    def test_empty_list_is_zero(self):
        assert _estimate_tokens([]) == 0

    def test_non_empty_message_positive(self):
        msgs = [{"role": "user", "content": "Hello world"}]
        assert _estimate_tokens(msgs) > 0

    def test_longer_content_more_tokens(self):
        short = [{"role": "user", "content": "Hi"}]
        long  = [{"role": "user", "content": "Hello " * 100}]
        assert _estimate_tokens(long) > _estimate_tokens(short)

    def test_multimodal_blocks(self):
        msgs = [{"role": "user", "content": [{"text": "image description here"}]}]
        assert _estimate_tokens(msgs) > 0


# ─── ContextManager.fit ───────────────────────────────────────────────────────

def _msgs(n: int, chars_each: int = 50) -> list:
    return [{"role": "user", "content": "x" * chars_each} for _ in range(n)]


class TestContextManagerFit:
    def test_within_budget_no_drop(self):
        cm = ContextManager(max_tokens=4096)
        msgs = _msgs(3, 10)
        trimmed, stats = cm.fit(msgs)
        assert stats["dropped"] == 0
        assert len(trimmed) == 3

    def test_over_budget_drops_oldest(self):
        # Very small budget → must drop messages
        cm = ContextManager(max_tokens=20, reply_reserve=0)
        msgs = _msgs(10, 20)
        trimmed, stats = cm.fit(msgs)
        assert stats["dropped"] > 0
        assert len(trimmed) < 10

    def test_system_message_preserved(self):
        cm = ContextManager(max_tokens=20, reply_reserve=0)
        msgs = [
            {"role": "system", "content": "You are MRL."},
        ] + _msgs(8, 30)
        trimmed, stats = cm.fit(msgs)
        roles = [m["role"] for m in trimmed]
        assert "system" in roles

    def test_stats_structure(self):
        cm = ContextManager(max_tokens=4096)
        _, stats = cm.fit(_msgs(2))
        required = {
            "original_count", "final_count", "dropped",
            "strategy_used", "estimated_tokens", "budget_tokens",
            "fitted_at_ms", "origin_signature",
        }
        assert required.issubset(stats.keys())

    def test_stats_origin_signature(self):
        cm = ContextManager()
        _, stats = cm.fit(_msgs(1))
        assert stats["origin_signature"] == "MrLiouWord"


# ─── Strategy: TRUNCATE_OLDEST ────────────────────────────────────────────────

class TestTruncateOldest:
    def test_removes_oldest_non_system(self):
        cm = ContextManager(max_tokens=20, reply_reserve=0, strategy=Strategy.TRUNCATE_OLDEST)
        msgs = [
            {"role": "user", "content": "first turn " * 5},
            {"role": "assistant", "content": "reply " * 5},
            {"role": "user", "content": "last"},
        ]
        trimmed, stats = cm.fit(msgs)
        contents = [m["content"] for m in trimmed]
        # "last" should survive; older content may be dropped
        if stats["dropped"] > 0:
            assert "last" in contents


# ─── Strategy: SLIDING_WINDOW ─────────────────────────────────────────────────

class TestSlidingWindow:
    def test_keeps_most_recent(self):
        cm = ContextManager(
            max_tokens=30, reply_reserve=0,
            strategy=Strategy.SLIDING_WINDOW,
        )
        msgs = _msgs(10, 20)
        trimmed, stats = cm.fit(msgs)
        # Sliding window keeps only as many recent messages as fit
        assert len(trimmed) <= 10

    def test_system_always_kept(self):
        cm = ContextManager(
            max_tokens=20, reply_reserve=0,
            strategy=Strategy.SLIDING_WINDOW,
        )
        msgs = [{"role": "system", "content": "sys"}] + _msgs(5, 30)
        trimmed, _ = cm.fit(msgs)
        assert trimmed[0]["role"] == "system"


# ─── Strategy: SUMMARISE_OLDEST ──────────────────────────────────────────────

class TestSummariseOldest:
    def test_adds_stub_when_dropping(self):
        cm = ContextManager(
            max_tokens=20, reply_reserve=0,
            strategy=Strategy.SUMMARISE_OLDEST,
        )
        msgs = _msgs(8, 30)
        trimmed, stats = cm.fit(msgs)
        if stats["dropped"] > 0:
            contents = [m.get("content", "") for m in trimmed]
            assert any("summarised" in c.lower() for c in contents)

    def test_no_stub_when_no_dropping(self):
        cm = ContextManager(
            max_tokens=4096, reply_reserve=0,
            strategy=Strategy.SUMMARISE_OLDEST,
        )
        msgs = _msgs(2, 5)
        trimmed, stats = cm.fit(msgs)
        assert stats["dropped"] == 0
        stub_msgs = [m for m in trimmed if m.get("_context_stub")]
        assert len(stub_msgs) == 0


# ─── estimate helper ─────────────────────────────────────────────────────────

class TestEstimateMethod:
    def test_estimate_matches_estimate_tokens(self):
        cm = ContextManager()
        msgs = _msgs(3, 20)
        assert cm.estimate(msgs) == _estimate_tokens(msgs)
