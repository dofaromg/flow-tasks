#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MRL_World_Projection_Runtime.py — MRL_World 世界投影與場態整合入口
origin_signature: MrLiouWord
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Dict

ORIGIN_SIGNATURE = "MrLiouWord"

_THIS_DIR = Path(__file__).resolve().parent
_MOTHER_DIR = _THIS_DIR.parent
_WORLD_RUNTIME_DIR = _MOTHER_DIR / "MRL_UniversalRuntimeLanguage_Core_v1" / "MRL_Runtime"

if str(_WORLD_RUNTIME_DIR) not in sys.path:
    sys.path.insert(0, str(_WORLD_RUNTIME_DIR))

from MRL_WorldRuntime import MRL_WorldRuntime  # type: ignore  # noqa: E402


class MRL_WorldProjectionRuntime:
    """世界投影場態整合入口。"""

    def __init__(self) -> None:
        self.origin_signature = ORIGIN_SIGNATURE
        self.runtime = MRL_WorldRuntime()

    def project(self, world_name: str, structurefield: Dict[str, str], context: Dict[str, Any]) -> Dict[str, Any]:
        self.runtime.spawn_world(world_name, structurefield)
        for key, value in context.items():
            self.runtime.set_context(world_name, key, value)
        report = self.runtime.report()
        report["origin_signature"] = self.origin_signature
        return report


def main() -> int:
    runtime = MRL_WorldProjectionRuntime()
    report = runtime.project(
        world_name="MRL_World_Project_A",
        structurefield={"runtime_101": "projection", "runtime_102": "projection"},
        context={"projection": "active", "flow": "world-integration"},
    )
    print("MRL_WORLD_PROJECTION_RUNTIME_OK")
    print(report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
