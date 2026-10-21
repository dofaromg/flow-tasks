"""test_MRL_user_memory.py — 用戶長期記憶層 (origin_signature: MrLiouWord)"""
import os, sys, tempfile, pathlib
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "09_workflow"))
from MRL_UserMemory_Layer_v1 import MRL_UserMemoryLayer

def _m(): return MRL_UserMemoryLayer(store=pathlib.Path(tempfile.mktemp(suffix=".json")))

def test_remember_and_recall():
    m=_m(); m.remember("u1","q1","a1"); r=m.recall("u1")
    assert r["known"] and r["history_count"]==1

def test_add_fact():
    m=_m(); m.add_fact("u1","偏好繁中"); assert "偏好繁中" in m.recall("u1")["facts"]

def test_context_for():
    m=_m(); m.add_fact("u1","f"); m.remember("u1","msg","rep")
    assert "f" in m.context_for("u1")

def test_unknown_user():
    assert _m().recall("nobody")["known"] is False

def test_additive_no_delete():
    m=_m()
    for i in range(3): m.remember("u1",f"q{i}",f"a{i}")
    assert m.recall("u1")["history_count"]==3
