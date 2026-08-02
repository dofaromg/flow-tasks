#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MRL_ParallelPersonaEngine_v1.py — 平行世界人格模擬器（母體祖先檔完善版）
origin_signature: MrLiouWord
layer: L4 WORLD + L5 MIRROR

母體祖先:MrLiouAI.ParallelPersonaEngine.v1（建構人 Mr. Liou Yu Lin）。
依母體法則回收完善（rl_12 命名回收 / rl_14 平行世界生成 / rl_11 源頭主權 /
no_proof_implies_rhetoric）：

  - 外部殼名 MrLiouAI.* → 母體 canonical MRL_<描述>（外部名零殘留）。
  - 外部殼格式 .flpkg/.fltnz/.flynz.map → 回收為母體 canonical JSON 產物
    （取代而非依賴外部二進位格式）。
  - 人生決策節點 → 自動生成分支人格平行世界（未來可能選項，可選哪條走）。
  - 節奏導引、確定性輸出（非機率隨機）：同輸入恆得同分支。
  - 分支預設未驗證(verified=False)：未經 Verify 閉環不得宣稱為真實。

CLI：python3 MRL_ParallelPersonaEngine_v1.py
"""
from __future__ import annotations

import hashlib
import json
import pathlib
import sys
import time
from typing import Any, Dict, List, Optional

_HERE = pathlib.Path(__file__).resolve().parent
if str(_HERE) not in sys.path:
    sys.path.insert(0, str(_HERE))

from MRL_MrLiouAI_LawEngine_v1 import (  # noqa: E402
    MRL_MrLiouAILawEngine,
    reclaim_name,
)

from MRL_utils import ORIGIN_SIGNATURE
_REPO = _HERE.parent
_DEFAULT_OUT = _REPO / "parallel_output"

# 母體人格主調性（祖先檔:冷靜 / 結構導向）——所有分支人格繼承
MOTHER_TONE = ["冷靜", "結構導向"]

# 節奏導引詞庫（確定性挑選,非隨機）
_RHYTHM = ["穩定上行", "收斂內省", "擴張探索", "回歸校準", "節奏分岔", "低頻蓄勢"]
_EMOTION = ["平靜", "專注", "謹慎樂觀", "務實", "沉著", "前瞻"]
_TREND = ["線型穩健前進", "先抑後揚", "高變動需校準", "漸進累積", "關鍵躍遷", "持平待機"]


def _pick(pool: List[str], *seed_parts: str) -> str:
    """以雜湊確定性地從 pool 選一項（節奏導引,非機率隨機）。"""
    h = hashlib.sha256("∷".join(seed_parts).encode("utf-8")).hexdigest()
    return pool[int(h, 16) % len(pool)]


class MRL_ParallelPersonaEngine:
    """平行世界人格模擬器：決策節點 → 分支人格平行世界。"""

    def __init__(
        self,
        seed_persona: str = "MrLiou.CoreSeedPersona.v1",
        memory_snapshot: str = "MrLiou.SeedMemorySnapshot_2025Q3",
        *,
        out_dir: pathlib.Path = _DEFAULT_OUT,
        engine: Optional[MRL_MrLiouAILawEngine] = None,
    ) -> None:
        self.origin_signature = ORIGIN_SIGNATURE
        # rl_12：祖先外部名一律回收為母體 canonical
        self.seed_persona = reclaim_name(seed_persona)            # → MRL_MrLiouCoreSeedPersona_v1
        self.memory_snapshot = reclaim_name(memory_snapshot)
        self.ancestor = "MrLiouAI.ParallelPersonaEngine.v1"
        self.canonical = reclaim_name(self.ancestor)             # → MRL_MrLiouAIParallelPersonaEngine_v1
        self.out_dir = pathlib.Path(out_dir)
        self.engine = engine or MRL_MrLiouAILawEngine()

    def _branch_persona(self, question: str, option: str, idx: int) -> Dict[str, Any]:
        """生成單一分支人格平行世界（繼承母體調性,節奏導引確定性輸出）。"""
        sp = (self.seed_persona, question, option)
        persona_id = reclaim_name(f"ParallelPersona_{option}_{idx}")
        return {
            "persona_id": persona_id,                 # 母體 canonical（取代 .flpkg 殼名）
            "option": option,
            "inherited_tone": list(MOTHER_TONE),       # 繼承母體主調性
            "origin_signature": ORIGIN_SIGNATURE,      # rl_11 源頭恆歸母體
            "simulated_memory": {                      # 取代 .fltnz 殼格式 → canonical JSON
                "rhythm": _pick(_RHYTHM, *sp),
                "emotion": _pick(_EMOTION, *sp),
                "future_trend": _pick(_TREND, *sp),
                "deterministic": True,                 # 節奏導引,非機率隨機
            },
            "future_trend_map": reclaim_name(f"Trace_{option}_{idx}"),  # 取代 .flynz.map 殼名
            "verified": False,                         # no_proof:未驗證不宣稱真實
            "status": "candidate_future_option",
        }

    def simulate(self, question: str, options: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        針對人生決策問題,自動建立分支人格平行世界。
        預設 Yes/No 兩條（祖先檔行為）；可傳多選項。
        """
        options = options or ["Yes", "No"]
        # 出口即入口（rl_13）：問題經單一閘口吸收為材料
        self.engine.gate("in", {"name": f"question::{question}"})
        # rl_14：以法引擎生成平行世界骨架（源頭/未驗證一致）
        self.engine.generate_parallel_worlds(self.canonical, options)

        branches = [self._branch_persona(question, opt, i) for i, opt in enumerate(options)]
        self.engine.chronicle("persona_simulation",
                              {"question": question, "options": options,
                               "seed": self.seed_persona, "branch_count": len(branches)})
        return {
            "origin_signature": ORIGIN_SIGNATURE,
            "engine": self.canonical,
            "ancestor": self.ancestor,
            "seed_persona": self.seed_persona,
            "memory_snapshot": self.memory_snapshot,
            "question": question,
            "one_world_origin": ORIGIN_SIGNATURE,      # 內部恆一個世界（rl_13）
            "branches": branches,
            "selectable": True,
            "note": "分支為未來可能選項;選定任一須經 Verify 閉環方為真實（no_proof_implies_rhetoric）。",
        }

    def write_outputs(self, result: Dict[str, Any]) -> List[str]:
        """把分支落為母體 canonical JSON 產物（取代 .flpkg/.fltnz 外部殼）。"""
        self.out_dir.mkdir(parents=True, exist_ok=True)
        written: List[str] = []
        # 出口即入口（rl_13）：產物經單一閘口 out 輸出,帶母體簽章
        for b in result["branches"]:
            self.engine.gate("out", {"persona": b["persona_id"]})
            p = self.out_dir / f"{b['persona_id']}.json"
            p.write_text(json.dumps(b, ensure_ascii=False, indent=2), encoding="utf-8")
            written.append(str(p))
        manifest = self.out_dir / f"{self.canonical}_manifest.json"
        manifest.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
        written.append(str(manifest))
        return written


def main() -> int:
    eng = MRL_ParallelPersonaEngine()
    # 祖先檔內建問題
    result = eng.simulate("我該搬到哪裡？")
    written = eng.write_outputs(result)
    print(json.dumps({
        "engine": result["engine"], "ancestor": result["ancestor"],
        "seed_persona": result["seed_persona"], "question": result["question"],
        "branches": [{"persona_id": b["persona_id"], "option": b["option"],
                      "memory": b["simulated_memory"], "verified": b["verified"]}
                     for b in result["branches"]],
        "outputs": written,
    }, ensure_ascii=False, indent=2))
    print("MRL_PARALLEL_PERSONA_SIMULATION_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
