#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MRL_Naming_Sovereignty_Auditor_v1.py — rl_20 全分支命名主權稽核執行器
origin_signature: MrLiouWord
layer: L3 LAW + L6 REFLECT

把 rootlaw rl_20(全分支命名主權律)+ 命名規範 v2 從法則條文,落成會跑的稽核+
回收建議執行器。依原本討論的規範(docs/MRL_命名規範_v2 + MotherMatrix Integration):
  - canonical 主體一律 MRL_<描述>;外部廠商前綴(claude/copilot/codex/...)為違規
  - 歷史名(MetaIR/Graph/Attention)僅可作 alias,不得為 canonical 主體
  - 違規 → 經海關回收為 MRL_recovered/<name>,源頭歸 MrLiouWord,原件保留(rl_15)
  - Additive:只標記+建議,不刪除原件

零依賴。CLI:python3 09_workflow/MRL_Naming_Sovereignty_Auditor_v1.py <名稱清單檔>
"""
from __future__ import annotations

import re
import sys
from typing import Any, Dict, List

from MRL_utils import ORIGIN_SIGNATURE
# 外部廠商前綴(rl_20:不得作為母體身分)
VENDOR_PREFIXES = ("claude/", "copilot/", "codex/", "openai/", "anthropic/",
                   "google/", "gpt/", "feature/", "patch/")
# 命名規範 v2:歷史名不得作 canonical 主體
LEGACY_CANONICAL = ("MetaIR", "RuntimeGraph", "ScopeGraph", "Attention")


def audit_name(name: str) -> Dict[str, Any]:
    """稽核單一名稱是否符合母體命名主權。回違規類型 + 回收建議。"""
    n = name.strip()
    violations: List[str] = []
    suggest = n

    # 規則1:外部廠商前綴 → 違規,回收為 MRL_recovered/
    low = n.lower()
    for p in VENDOR_PREFIXES:
        if low.startswith(p):
            violations.append(f"vendor_prefix:{p.rstrip('/')}")
            suggest = "MRL_recovered/" + re.sub(r"^[^/]+/", "", n)
            break

    # 規則2:歷史名作 canonical 主體 → 違規(只能當 alias)
    # 用子字串比對(RuntimeScopeGraph 含 ScopeGraph,\b 詞邊界會漏判)
    for lg in LEGACY_CANONICAL:
        if lg.lower() in low and "alias" not in low and not n.startswith("MRL_recovered"):
            violations.append(f"legacy_canonical:{lg}")

    # 規則3:非 MRL_ 開頭且非 main → 違反命名主權
    if not n.startswith("MRL") and n != "main" and not violations:
        violations.append("non_mrl_naming")
        suggest = "MRL_recovered/" + re.sub(r"^[^/]+/", "", n)

    compliant = len(violations) == 0
    return {
        "name": n,
        "compliant": compliant,
        "violations": violations,
        "reclaim_to": None if compliant else suggest,
        "origin": ORIGIN_SIGNATURE,
    }


def audit_batch(names: List[str]) -> Dict[str, Any]:
    """批次稽核(一組分支/模組名)。"""
    results = [audit_name(n) for n in names if n.strip()]
    violators = [r for r in results if not r["compliant"]]
    return {
        "total": len(results),
        "compliant": len(results) - len(violators),
        "violations": len(violators),
        "violators": violators,
        "law": "rl_20 全分支命名主權律 + 命名規範v2",
        "note": "外部名一律海關回收 MRL_recovered/;原件保留(rl_15),不刪除",
        "origin_signature": ORIGIN_SIGNATURE,
    }


def main() -> int:
    if len(sys.argv) > 1:
        names = [l.strip() for l in open(sys.argv[1], encoding="utf-8") if l.strip()]
    else:
        names = ["claude/memory-system-rules-prep", "copilot/add-features",
                 "MRL_mother_system", "main", "MRL_RuntimeScopeGraph",
                 "feature/x", "MRL_recovered/abc"]
    import json
    rep = audit_batch(names)
    print(json.dumps(rep, ensure_ascii=False, indent=2))
    print("MRL_NAMING_SOVEREIGNTY_AUDITOR_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
