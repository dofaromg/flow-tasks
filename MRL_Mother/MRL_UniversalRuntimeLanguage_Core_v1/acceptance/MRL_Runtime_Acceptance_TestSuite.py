#!/usr/bin/env python3
# MRL_Runtime_Acceptance_TestSuite
# origin_signature: MrLiouWord
"""Runtime 驗收套件（純 stdlib，無 pytest 依賴；CI 與離線皆可跑）。

驗收項（§10）：
  A RuntimeStructureField build success
  B Replay exactness
  C Restore exactness
  D Persistent Loop survives restart
  E World Runtime synchronization active
  F Verification roundtrip exact

全通過 → 印出 MRL_RUNTIME_ACCEPTANCE_PASS 並 exit 0；否則 exit 1。
"""

from __future__ import annotations

import pathlib
import sys

# 將 repo 根目錄加入 sys.path（acceptance/ 的上兩層 = repo root）
_REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from MRL_UniversalRuntimeLanguage_Core_v1.MRL_Runtime.MRL_DL580_Runtime import MRL_DL580_Runtime  # noqa: E402
from MRL_UniversalRuntimeLanguage_Core_v1.MRL_Runtime.MRL_Verification import verify_canonical_naming  # noqa: E402

SAMPLE_PY = '''import os

def greet(name):
    msg = "hello " + name
    return msg

class World:
    def spin(self):
        for i in range(3):
            print(i)
'''


def run_acceptance() -> int:
    runtime = MRL_DL580_Runtime()
    result = runtime.run(SAMPLE_PY, lang="python", loop_id="acceptance")
    verification = result["verification"]

    print("=== MRL Runtime Acceptance ===")
    print(f"origin_signature={verification['origin_signature']}")
    print(f"stages_executed={result['stages_executed']}")
    for c in verification["checks"]:
        flag = "PASS" if c["pass"] else "FAIL"
        print(f"  [{flag}] {c['check']} :: {c['detail']}")
    print(f"passed={verification['passed']}/{verification['total']}")

    # 第二區塊：canonical naming verification（v2）
    naming = verify_canonical_naming()
    print("=== Canonical Naming Verification ===")
    for c in naming["checks"]:
        flag = "PASS" if c["pass"] else "FAIL"
        print(f"  [{flag}] {c['check']}")
    print(f"naming_passed={naming['passed']}/{naming['total']}")

    ok = verification["acceptance"] and naming["acceptance"]
    print(verification["token"])  # MRL_RUNTIME_ACCEPTANCE_PASS / _FAIL
    print(naming["token"])        # MRL_CANONICAL_NAMING_VERIFICATION_PASS / _FAIL
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(run_acceptance())
