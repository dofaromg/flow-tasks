"""test_MRL_pingresonance_map.py (origin: MrLiouWord)"""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "09_workflow"))
from MRL_PingResonance_Map_v1 import MRL_PingResonanceMap
def _m():
    m = MRL_PingResonanceMap()
    m.add_resonance("EchoBody", "futuremind", 0.8)
    m.add_resonance("EchoBody", "guardian", 0.9)
    m.add_resonance("EchoBody", "wild", 0.6)
    return m
def test_add_resonance_symmetric():
    m = _m()
    assert m.weights[("EchoBody", "guardian")] == 0.9
    assert m.weights[("guardian", "EchoBody")] == 0.9  # 共振對稱
def test_ping_ranks_by_weight():
    m = _m(); r = m.ping("EchoBody")
    nodes = [x["node"] for x in r["resonance"]]
    assert nodes[0] == "EchoBody"          # source 最強
    assert nodes[1] == "guardian"          # 0.9 最高權重
    assert r["next_persona"] == "guardian"
def test_ping_unknown_node():
    m = _m(); assert "error" in m.ping("nope")
def test_map_summary():
    m = _m(); s = m.map_summary()
    assert s["nodes"] == 4 and s["edges"] == 3
    assert s["origin_signature"] == "MrLiouWord"
