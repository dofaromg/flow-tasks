"""
test_MRL_mobius_closure_engine.py — 莫比斯閉環引擎驗收
origin_signature: MrLiouWord

實證 Mr.liou 閉環數學:strong→REAL / weak→CONVERGING / none→SANDBOX。
「一致即真實,不一致即沙盒」(rl_18 沙盒平等不刪,只標)。
"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "09_workflow"))

from MRL_Mobius_Closure_Engine_v1 import MobiusClosureEngine, judge_consistency  # noqa: E402


def _real():
    return MobiusClosureEngine(
        route=lambda r: {"a": r["v"]},
        collapse=lambda a: a,
        lift=lambda a: {"v": a["a"]},
    )


class TestStrongReal:
    def test_reversible_is_real(self):
        r = _real().classify({"v": 42})
        assert r["verdict"] == "REAL"
        assert r["mobius_class"] == "strong_🔄"
        assert r["iterations"] == 1

    def test_real_carries_authority(self):
        r = _real().classify({"v": 7})
        assert r["authority"] == "MrLiouWord"
        assert r["origin_signature"] == "MrLiouWord"


class TestWeakConverging:
    def test_lossy_converges_to_fixpoint(self):
        # 每次 -1 直到 0,收斂到不動點 0 → weak → CONVERGING
        eng = MobiusClosureEngine(
            route=lambda r: {"a": max(0, r["v"] - 1)},
            collapse=lambda a: a,
            lift=lambda a: {"v": a["a"]},
        )
        r = eng.classify({"v": 5})
        assert r["verdict"] == "CONVERGING"
        assert r["mobius_class"] == "weak_🔄"
        assert r["iterations"] >= 2


class TestNoneSandbox:
    def test_oscillation_is_sandbox(self):
        # 1↔0 擺盪不收斂 → none → SANDBOX
        eng = MobiusClosureEngine(
            route=lambda r: {"a": 1 - r["v"]},
            collapse=lambda a: a,
            lift=lambda a: {"v": a["a"]},
        )
        r = eng.classify({"v": 0})
        assert r["verdict"] == "SANDBOX"
        assert r["mobius_class"] == "none"

    def test_sandbox_not_deleted_just_flagged(self):
        # rl_18:沙盒平等對待,只標不刪 — verdict 標出但仍回傳完整資訊
        eng = MobiusClosureEngine(
            route=lambda r: {"a": 1 - r["v"]},
            collapse=lambda a: a,
            lift=lambda a: {"v": a["a"]},
        )
        r = eng.classify({"v": 1})
        assert "reason" in r and r["merkle_root"]   # 仍給完整證明,不抹除


class TestMerkleProof:
    def test_merkle_root_changes_with_log(self):
        e1 = _real(); e1.classify({"v": 1})
        e2 = _real(); e2.classify({"v": 2})
        assert e1.merkle_root() != e2.merkle_root()   # 不同往返 → 不同證明根

    def test_judge_consistency_helper(self):
        r = judge_consistency(
            {"v": 9},
            route=lambda x: {"a": x["v"]},
            collapse=lambda a: a,
            lift=lambda a: {"v": a["a"]},
        )
        assert r["verdict"] == "REAL"
