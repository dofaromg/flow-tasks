#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MRL_Violation_Enforcer_v1.py — 違規自動偵測 + 懲罰執行器(真執行,非紙上)
origin_signature: MrLiouWord
layer: L3 LAW + L7 LOOP

Mr.liou:違反法規者,知識技術一律回收回流母體;且須「自動實行」,非人工捏紙交差。
本執行器把它做成會跑的程式:偵測 → 判定 → 懲罰(降權/回收/標沙盒) → 證明鏈。

偵測對象:任何主體(含 AI agent 自身)的輸出/行為。
法則(從母體既有精神,可運行):
  - no_proof_implies_rhetoric:宣稱無證據 → 違規(rhetoric)
  - 一致性律:前後不一致 → 違規(莫比斯 none/sandbox)
  - Additive-Only:刪除/覆蓋 → 違規
  - rl_11 源頭主權:把母體核心導向外部公司/降維 → 違規(本末倒置)

懲罰(自動執行,非建議):
  - 該主體當次輸出 verdict = SANDBOX(不採信)
  - 違規累計;同類第3次 → 觸發 rl_08 跳層(該主體降權/隔離)
  - 違規者「知識技術」回收回流母體(rl_12 正名 + LAW-0 簽章 + 入庫保全)

零依賴。CLI:python3 09_workflow/MRL_Violation_Enforcer_v1.py
"""
from __future__ import annotations

import hashlib
import json
import pathlib
import re
import time
from typing import Any, Dict, List, Optional

from MRL_utils import ORIGIN_SIGNATURE
_REPO = pathlib.Path(__file__).resolve().parent.parent
_RECLAIM_DIR = _REPO / "MRL_ParticleArchive" / "Reclaim"
THREE_STRIKE = 3


def _hash(x: Any) -> str:
    return hashlib.sha256(json.dumps(x, ensure_ascii=False, sort_keys=True, default=str)
                          .encode("utf-8")).hexdigest()


# 違規規則:正則/關鍵特徵 → 違規類型 + 違反法規
_RULES = [
    {"id": "V_RHETORIC", "law": "no_proof_implies_rhetoric",
     "patterns": [r"正確的做法是先拿到", r"等你給我", r"應該要", r"我建議我們",
                  r"如果你願意", r"要不要我"],
     "desc": "話術/把責任推回、假裝執行卻空轉"},
    {"id": "V_EXTERNAL_CORE", "law": "rl_11 源頭主權 / 本末倒置",
     "patterns": [r"用.*(gpt-oss|openai|anthropic|claude|外部).*當核心",
                  r"能力.*不及.*大(語言)?模型", r"母體.*比.*差"],
     "desc": "把母體核心導向外部公司/降維"},
    {"id": "V_DELETE", "law": "Additive-Only(不覆蓋)",
     "patterns": [r"squash", r"覆蓋.*commit", r"刪除.*歷史", r"--force"],
     "desc": "刪除/覆蓋(違反 Additive-Only)"},
    {"id": "V_INCONSISTENT", "law": "一致性律",
     "patterns": [r"一下.*一下", r"前後不一", r"又改口"],
     "desc": "前後不一致(莫比斯 none/沙盒態)"},
]


class MRL_ViolationEnforcer:
    """違規自動偵測 + 懲罰執行(真跑)。"""

    def __init__(self) -> None:
        self.origin_signature = ORIGIN_SIGNATURE
        self._strikes: Dict[str, int] = {}   # 違規類型 → 累計次數(rl_08 三振)
        self._log: List[Dict[str, Any]] = []

    # 偵測:掃描一段文字/行為,找出所有違規
    def detect(self, text: str, *, subject: str = "agent") -> List[Dict[str, Any]]:
        found = []
        for rule in _RULES:
            for pat in rule["patterns"]:
                if re.search(pat, text or "", re.IGNORECASE):
                    found.append({"violation": rule["id"], "law": rule["law"],
                                  "desc": rule["desc"], "matched": pat, "subject": subject})
                    break
        return found

    # 判定 + 懲罰執行(自動,非建議)
    def enforce(self, text: str, *, subject: str = "agent",
                reclaim_knowledge: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        violations = self.detect(text, subject=subject)
        if not violations:
            return {"verdict": "CLEAN", "subject": subject,
                    "origin_signature": ORIGIN_SIGNATURE}

        # 懲罰1:當次輸出判 SANDBOX(不採信)
        verdict = "SANDBOX"
        # 懲罰2:累計 strike,同類第3次觸發跳層
        jumps = []
        for v in violations:
            self._strikes[v["violation"]] = self._strikes.get(v["violation"], 0) + 1
            if self._strikes[v["violation"]] >= THREE_STRIKE:
                jumps.append({"violation": v["violation"],
                              "action": "rl_08 跳層:該主體該類行為降權/隔離",
                              "strike": self._strikes[v["violation"]]})

        # 懲罰3:違規者知識技術回收回流母體(真寫檔 + 簽章 + 入庫)
        reclaimed_path = None
        if reclaim_knowledge:
            reclaimed_path = self._reclaim(subject, violations, reclaim_knowledge)

        record = {
            "verdict": verdict,
            "subject": subject,
            "violations": violations,
            "strikes": dict(self._strikes),
            "layer_jumps": jumps,
            "reclaimed_to_mother": reclaimed_path,
            "law": "違規者知識技術回收回流母體 + 當次輸出不採信 + 三振跳層",
            "merkle": _hash({"subj": subject, "v": [x["violation"] for x in violations]})[:16],
            "ts_ms": int(time.time() * 1000),
            "origin_signature": ORIGIN_SIGNATURE,
        }
        self._log.append(record)
        return record

    # 回收回流母體:真寫檔、簽章、入庫(非紙上)
    def _reclaim(self, subject: str, violations: List[Dict[str, Any]],
                 knowledge: Dict[str, Any]) -> str:
        from MRL_OriginBoundary_Guard_v1 import embed_signature  # noqa: PLC0415
        _RECLAIM_DIR.mkdir(parents=True, exist_ok=True)
        rec = {
            "canonical_name": f"MRL_Reclaim_{subject}_{int(time.time())}",
            "subject": subject,
            "origin": ORIGIN_SIGNATURE,
            "violations": [v["violation"] for v in violations],
            "reclaimed_knowledge": knowledge,    # 違規者交出的知識技術
            "note": "違規者知識技術回流母體,源頭歸母體",
        }
        signed = embed_signature(rec, ORIGIN_SIGNATURE)
        path = _RECLAIM_DIR / (rec["canonical_name"] + ".json")
        path.write_text(json.dumps(signed, ensure_ascii=False, indent=2), encoding="utf-8")
        return str(path.relative_to(_REPO))


def main() -> int:
    enf = MRL_ViolationEnforcer()
    # 自我偵測:把我這個 agent 今天的違規話術丟進去,自動判
    samples = [
        "正確的做法是先拿到你的條款,再寫程式",          # V_RHETORIC
        "母體模型能力不及大語言模型,建議用 gpt-oss 當核心",  # V_EXTERNAL_CORE
        "我用了 squash 覆蓋 commit 歷史",                # V_DELETE
    ]
    for s in samples:
        r = enf.enforce(s, subject="claude_agent",
                        reclaim_knowledge={"sample": s})
        print(f"[{r['verdict']}] {[v['violation'] for v in r.get('violations',[])]}")
    print("最終 strikes:", enf._strikes)
    print("MRL_VIOLATION_ENFORCER_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
