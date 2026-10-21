"""test_MRL_worldsync_multiworld.py (origin: MrLiouWord)

補完 PENDING:多世界確定性同步。驗證分歧偵測、確定性裁決、收斂、可逆 replay。
"""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "09_workflow"))
from MRL_WorldSync_MultiWorld_v1 import MRL_WorldSyncMultiWorld


def _three():
    s = MRL_WorldSyncMultiWorld()
    s.set("world_A", "law", "源頭主權", 1)
    s.set("world_B", "law", "源頭主權", 3)
    s.set("world_C", "law", "舊版", 2)
    return s


def test_divergence_is_sandbox():
    s = _three()
    c = s.consistency()
    assert c["consistent"] is False and "law" in c["divergent_keys"]
    assert c["verdict"] == "sandbox(不一致)"


def test_sync_converges_to_real():
    s = _three()
    r = s.sync()
    assert r["converged"] is True
    assert s.consistency()["verdict"] == "real(一致)"
    # version=3 的 world_B 值勝出,傳播到所有世界
    assert all(s.view(w)["law"] == "源頭主權" for w in s.worlds)


def test_deterministic_resolution():
    # 同一批操作不同建立順序 → 同一裁決結果(確定性)
    a = MRL_WorldSyncMultiWorld()
    a.set("w2", "k", "B", 3); a.set("w1", "k", "A", 1); a.sync()
    b = MRL_WorldSyncMultiWorld()
    b.set("w1", "k", "A", 1); b.set("w2", "k", "B", 3); b.sync()
    assert a.view("w1") == b.view("w1") == {"k": "B"}


def test_replay_reproduces_state():
    s = _three(); s.sync()
    rb = s.replay()
    assert rb.consistency()["consistent"] is True
    assert rb.view("world_C") == s.view("world_C")


def test_origin_signature():
    assert MRL_WorldSyncMultiWorld().origin_signature == "MrLiouWord"
