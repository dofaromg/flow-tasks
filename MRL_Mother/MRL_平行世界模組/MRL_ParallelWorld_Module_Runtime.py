#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MRL_ParallelWorld_Module_Runtime.py — MRL 平行世界模組實作入口
origin_signature: MrLiouWord

使用 canonical 多世界同步器建立可執行入口。
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Dict

ORIGIN_SIGNATURE = "MrLiouWord"

_THIS_DIR = Path(__file__).resolve().parent
_MOTHER_DIR = _THIS_DIR.parent
_WORKFLOW_DIR = _MOTHER_DIR / "09_workflow"

if str(_WORKFLOW_DIR) not in sys.path:
    sys.path.insert(0, str(_WORKFLOW_DIR))

from MRL_WorldSync_MultiWorld_v1 import MRL_WorldSyncMultiWorld  # type: ignore  # noqa: E402


class MRL_ParallelWorldRuntime:
    """平行世界模組入口。"""

    def __init__(self) -> None:
        self.origin_signature = ORIGIN_SIGNATURE
        self.sync_engine = MRL_WorldSyncMultiWorld()

    def converge_demo(self) -> Dict[str, Any]:
        self.sync_engine.set("world_A", "law", "源頭主權", version=1)
        self.sync_engine.set("world_B", "law", "源頭主權", version=3)
        self.sync_engine.set("world_C", "law", "舊版", version=2)
        self.sync_engine.set("world_A", "mode", "權位區分", version=1)
        before = self.sync_engine.consistency()
        sync = self.sync_engine.sync()
        after = self.sync_engine.consistency()
        return {
            "origin_signature": self.origin_signature,
            "before": before,
            "sync": sync,
            "after": after,
            "worlds": sorted(self.sync_engine.worlds.keys()),
        }


def main() -> int:
    runtime = MRL_ParallelWorldRuntime()
    report = runtime.converge_demo()
    print("MRL_PARALLEL_WORLD_RUNTIME_OK")
    print(report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
