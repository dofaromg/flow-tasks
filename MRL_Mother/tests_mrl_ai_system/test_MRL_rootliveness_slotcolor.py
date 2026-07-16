"""test_MRL_rootliveness_slotcolor.py (origin: MrLiouWord)

吸收 LLVM late-GC-root-lowering 之演算法本體(liveness/干涉圖/PEO/著色),
驗證母體自家重寫真的算對。
"""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "09_workflow"))
from MRL_RootLiveness_SlotColor_Engine_v1 import MRL_RootLivenessSlotColorEngine


def _cfg():
    e = MRL_RootLivenessSlotColorEngine()
    e.add_block("entry", defs=["a", "b"], uses=[], succs=["loop"])
    e.add_block("loop", defs=["c"], uses=["a", "b"], succs=["loop", "exit"])
    e.add_block("exit", defs=["d"], uses=["c"], succs=[])
    return e


def test_liveness_fixpoint():
    e = _cfg(); e.compute_liveness()
    assert e.live_in["loop"] == {"a", "b"}
    assert e.live_out["loop"] == {"a", "b", "c"}
    assert e.live_in["exit"] == {"c"}


def test_interference_clique():
    e = _cfg(); g = e.interference_graph()
    # a,b,c 在 loop 同時活躍 → 兩兩干涉
    assert "b" in g["a"] and "c" in g["a"] and "c" in g["b"]


def test_slot_coloring_valid_and_minimal():
    e = _cfg(); r = e.allocate_slots()
    assert r["valid_coloring"] is True
    # a,b,c 互相干涉需 3 槽;d 不與 a,b,c 全干涉可重用
    assert r["num_slots"] == 3
    s = r["slots"]
    assert s["a"] != s["b"] and s["a"] != s["c"] and s["b"] != s["c"]


def test_full_clique_needs_n_slots():
    # 完全干涉圖(所有值同時活躍)→ 色數 = 變數數
    e = MRL_RootLivenessSlotColorEngine()
    e.add_block("b0", defs=["x", "y", "z"], uses=[], succs=["b1"])
    e.add_block("b1", defs=[], uses=["x", "y", "z"], succs=[])
    r = e.allocate_slots()
    assert r["num_slots"] == 3 and r["valid_coloring"] is True


def test_origin_signature():
    assert MRL_RootLivenessSlotColorEngine().origin_signature == "MrLiouWord"
