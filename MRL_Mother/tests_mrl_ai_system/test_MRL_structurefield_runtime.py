"""test_MRL_structurefield_runtime.py — Replay/Restore/World (origin: MrLiouWord)"""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "09_workflow"))
from MRL_StructureField_Runtime_v1 import (MRL_ReplayStructureField,
    MRL_RestoreStructureField, MRL_WorldStructureField)

def _reducer(s, ev):
    s[ev["payload"]["k"]] = ev["payload"]["v"]; return s

def test_replay_deterministic():
    r = MRL_ReplayStructureField(); r.record("add",{"k":"a","v":1}); r.record("add",{"k":"b","v":2})
    out = r.replay(_reducer)
    assert out["state"] == {"a":1,"b":2} and out["replayed_events"]==2

def test_replay_same_events_same_result():
    r1=MRL_ReplayStructureField(); r1.record("add",{"k":"x","v":9})
    r2=MRL_ReplayStructureField(); r2.record("add",{"k":"x","v":9})
    assert r1.replay(_reducer)["state"]==r2.replay(_reducer)["state"]

def test_restore_latest_and_specific():
    rs=MRL_RestoreStructureField(); rs.snapshot({"x":1}); rs.snapshot({"x":2})
    assert rs.restore()["state"]=={"x":2} and rs.restore(0)["state"]=={"x":1}

def test_restore_hash_verified():
    rs=MRL_RestoreStructureField(); rs.snapshot({"a":1})
    assert rs.restore()["hash_verified"] is True

def test_restore_no_snapshot_errors():
    assert MRL_RestoreStructureField().restore()["restored"] is False

def test_world_register_and_sync():
    w=MRL_WorldStructureField(); w.register("w0",{"v":42}); r=w.sync("w0","w1")
    assert r["synced"] and "w1" in w.list_worlds()
    assert w.worlds["w1"]["state"]=={"v":42}

def test_world_sync_missing_source():
    assert MRL_WorldStructureField().sync("none","x")["synced"] is False
