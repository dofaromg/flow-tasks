"""test_MRL_memory_starmap.py (origin: MrLiouWord)"""
import os, sys, tempfile, pathlib
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "09_workflow"))
from MRL_MemoryStarMap_v1 import MRL_MemoryStarMap
def _m(): return MRL_MemoryStarMap(pathlib.Path(tempfile.mktemp(suffix=".json")))
def test_add_star_not_taken():
    m=_m(); r=m.add_star("s1","A",["A","B","C"]); assert r["not_taken_count"]==2
def test_connect_and_history():
    m=_m(); m.add_star("s1","A",["A","B"]); m.add_star("s2","X",["X"]); m.connect("s1","s2")
    h=m.evolution_history(); assert h["path"]==["s1→s2"] and h["stars"]==2
def test_unexplored():
    m=_m(); m.add_star("s1","A",["A","B","C"])
    assert len(m.unexplored())==2
def test_not_taken_branches_count():
    m=_m(); m.add_star("s1","A",["A","B"]); m.add_star("s2","X",["X","Y","Z"])
    assert m.evolution_history()["not_taken_branches"]==3
