"""test_MRL_durablereplay_instrumentation.py (origin: MrLiouWord)

補完 ReplayRestore 常駐結構:持久落盤 + 跨重啟精確重播。
"""
import os, sys, tempfile, pathlib
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "09_workflow"))
from MRL_DurableReplay_Instrumentation_v1 import MRL_DurableReplayInstrumentation


def _log():
    return pathlib.Path(tempfile.mktemp(suffix=".jsonl"))


def test_record_is_durable_appendonly():
    p = _log()
    inst = MRL_DurableReplayInstrumentation(p)
    inst.record("n0", "observe"); inst.record("n1", "resolve")
    # 落盤可由新實例讀回(跨重啟)
    assert len(MRL_DurableReplayInstrumentation(p).load_events()) == 2


def test_exact_replay_across_restart():
    p = _log()
    inst = MRL_DurableReplayInstrumentation(p)
    for i in range(6):
        inst.record(f"n{i}", "observe" if i % 2 == 0 else "resolve")
    pre = inst.state_hash()
    # 模擬重啟:新實例指同一持久日誌 → 精確重播一致
    rep = MRL_DurableReplayInstrumentation(p).exact_replay(expected_hash=pre)
    assert rep["exact"] is True and rep["events"] == 6


def test_rollback_from_durable_log():
    p = _log()
    inst = MRL_DurableReplayInstrumentation(p)
    for i in range(5):
        inst.record(f"n{i}")
    rb = inst.rollback(2)
    assert rb["rolled_back_to"] == 2 and rb["state"]["node_count"] == 3


def test_origin_signature():
    assert MRL_DurableReplayInstrumentation(_log()).origin_signature == "MrLiouWord"
