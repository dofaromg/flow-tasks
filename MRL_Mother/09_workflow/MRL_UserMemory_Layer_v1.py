#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MRL_UserMemory_Layer_v1.py — 用戶層:長期記憶(母體缺層補完 2/3)
origin_signature: MrLiouWord
layer: L6 REFLECT

Session_Package 點名缺層:User Layer(long-term memory)。
跨 session 記住每個用戶的對話/偏好/事實。純 stdlib、零外部、可持久(JSON)。
接進 chat:每次對話前注入用戶長期記憶,對話後存回。

對齊:rl_03 audit(每筆記憶有時間戳)/ LAW-0(origin_signature)/ rl_15(不刪,additive)
CLI:python3 09_workflow/MRL_UserMemory_Layer_v1.py
"""
from __future__ import annotations

import json
import pathlib
import time
from typing import Any, Dict, List, Optional

from MRL_utils import ORIGIN_SIGNATURE
_REPO = pathlib.Path(__file__).resolve().parent.parent
_STORE = _REPO / "data" / "MRL_user_memory.json"


class MRL_UserMemoryLayer:
    """用戶跨 session 長期記憶。每用戶:facts(事實)+ history(對話摘要)。"""

    def __init__(self, store: pathlib.Path = _STORE, max_history: int = 50) -> None:
        self.origin_signature = ORIGIN_SIGNATURE
        self.store = pathlib.Path(store)
        self.max_history = max_history
        self._data: Dict[str, Any] = self._load()

    def _load(self) -> Dict[str, Any]:
        if self.store.exists():
            try:
                return json.loads(self.store.read_text(encoding="utf-8"))
            except Exception:  # noqa: BLE001
                pass
        return {"users": {}, "origin_signature": ORIGIN_SIGNATURE}

    def _save(self) -> None:
        self.store.parent.mkdir(parents=True, exist_ok=True)
        self.store.write_text(json.dumps(self._data, ensure_ascii=False, indent=2),
                              encoding="utf-8")

    def _u(self, uid: str) -> Dict[str, Any]:
        return self._data["users"].setdefault(uid, {"facts": [], "history": []})

    # 記一筆對話(additive,不刪舊;超過上限只截顯示不刪存)
    def remember(self, user_id: str, message: str, reply: str) -> Dict[str, Any]:
        u = self._u(user_id)
        u["history"].append({"ts": int(time.time()), "msg": message[:200],
                             "reply": str(reply)[:200]})
        self._save()
        return {"remembered": True, "user_id": user_id,
                "history_count": len(u["history"]), "origin_signature": ORIGIN_SIGNATURE}

    # 記一筆事實/偏好
    def add_fact(self, user_id: str, fact: str) -> Dict[str, Any]:
        u = self._u(user_id)
        if fact not in u["facts"]:
            u["facts"].append(fact)
            self._save()
        return {"user_id": user_id, "facts": u["facts"], "origin_signature": ORIGIN_SIGNATURE}

    # 取回用戶長期記憶(注入 chat 上下文用)
    def recall(self, user_id: str, recent: int = 5) -> Dict[str, Any]:
        u = self._data["users"].get(user_id)
        if u is None:
            return {"user_id": user_id, "facts": [], "recent_history": [], "known": False}
        return {"user_id": user_id, "facts": u["facts"],
                "recent_history": u["history"][-recent:],
                "history_count": len(u["history"]), "known": True,
                "origin_signature": ORIGIN_SIGNATURE}

    # 組成可注入對話的記憶上下文字串
    def context_for(self, user_id: str) -> str:
        r = self.recall(user_id)
        if not r["known"]:
            return ""
        parts = []
        if r["facts"]:
            parts.append("已知事實:" + "；".join(r["facts"]))
        if r["recent_history"]:
            parts.append("近期對話:" + "；".join(h["msg"] for h in r["recent_history"]))
        return " | ".join(parts)


def main() -> int:
    import tempfile
    m = MRL_UserMemoryLayer(store=pathlib.Path(tempfile.mktemp(suffix=".json")))
    m.add_fact("u1", "偏好繁體中文")
    m.remember("u1", "源頭主權是什麼", "[母體回應]rl_11...")
    m.remember("u1", "莫比斯環", "[母體回應]rl_18...")
    r = m.recall("u1")
    print("facts:", r["facts"], "| history:", r["history_count"])
    print("context:", m.context_for("u1")[:120])
    print("MRL_USER_MEMORY_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
