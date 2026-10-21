#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MRL_WorldModule_Runtime.py — MRL 世界模組實作入口
origin_signature: MrLiouWord

提供可執行世界場 runtime：
- 世界生成 / context 寫入 / 雙世界同步
- 與 canonical `MRL_WorldRuntime` 對齊
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


class MRL_WorldModuleRuntime:
    """世界模組主入口（可直接由外部呼叫）。"""

    def __init__(self) -> None:
        self.origin_signature = ORIGIN_SIGNATURE
        self.runtime = MRL_WorldRuntime()

    def boot_minimal_world(self) -> Dict[str, Any]:
        world_structurefield = {
            "runtime_001": "world_main",
            "runtime_002": "world_mirror",
        }
        self.runtime.spawn_world("MRL_World_Main", world_structurefield)
        self.runtime.spawn_world("MRL_World_Mirror", world_structurefield)

        self.runtime.set_context("MRL_World_Main", "mode", "perception")
        self.runtime.set_context("MRL_World_Mirror", "law", "怎麼過去，就怎麼回來")
        sync_result = self.runtime.synchronize("MRL_World_Main", "MRL_World_Mirror")

        report = self.runtime.report()
        report["origin_signature"] = self.origin_signature
        report["sync_result"] = sync_result
        return report


def main() -> int:
    runtime = MRL_WorldModuleRuntime()
    report = runtime.boot_minimal_world()
    print("MRL_WORLD_MODULE_RUNTIME_OK")
    print(report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
