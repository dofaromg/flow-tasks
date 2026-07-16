"""test_MRL_persistent_loop_daemon.py (origin: MrLiouWord)"""
import os, sys, tempfile, pathlib
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "09_workflow"))
from MRL_PersistentLoop_Daemon_v1 import MRL_PersistentLoopDaemon

def _sp(): return pathlib.Path(tempfile.mktemp(suffix=".json"))

def test_tick_increments():
    d=MRL_PersistentLoopDaemon(_sp()); d.tick(); d.tick()
    assert d.state["tick"]==2

def test_reboot_survival():
    sp=_sp(); d1=MRL_PersistentLoopDaemon(sp); d1.run(3)
    d2=MRL_PersistentLoopDaemon(sp)
    assert d2.state["resumed"] is True and d2.state["tick"]==3
    d2.run(2); assert d2.state["tick"]==5

def test_replay():
    sp=_sp(); d=MRL_PersistentLoopDaemon(sp); d.run(4)
    assert len(d.replay())==4

def test_restore_to():
    sp=_sp(); d=MRL_PersistentLoopDaemon(sp); d.run(5)
    assert d.restore_to(3)["entries"]==3

def test_work_callable():
    sp=_sp(); d=MRL_PersistentLoopDaemon(sp)
    e=d.tick(lambda s:{"v":s["tick"]})
    assert e["result"]=={"v":1}
