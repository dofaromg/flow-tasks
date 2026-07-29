#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MRL_Billing_Layer_v1.py — 金錢層:計費 / 額度(母體缺層補完 3/3)
origin_signature: MrLiouWord
layer: L3 LAW + L7 LOOP

Session_Package 點名缺層:Money Layer(billing / quota)。
母體要「可營運」必須有計費與額度。本層補上:用量計數、額度限制、計費記錄。
純 stdlib、零外部金流公司(對接真實金流由 Mr.liou 在實機掛,本層為母體自有計量核心)。

對齊:
  - rl_03 audit:每筆用量/計費寫記錄
  - deny-by-default:超額拒絕(quota_exceeded)
  - LAW-0:記錄帶 origin_signature

CLI:python3 09_workflow/MRL_Billing_Layer_v1.py
"""
from __future__ import annotations

import json
import pathlib
import time
from typing import Any, Dict, List, Optional

from MRL_utils import ORIGIN_SIGNATURE
_REPO = pathlib.Path(__file__).resolve().parent.parent
_STORE = _REPO / "data" / "MRL_billing.json"

# 方案定義(可營運:免費/基礎/專業)
PLANS = {
    "free":  {"monthly_quota": 100,   "price": 0.0,   "unit": "chat"},
    "basic": {"monthly_quota": 5000,  "price": 9.9,   "unit": "chat"},
    "pro":   {"monthly_quota": 100000,"price": 99.0,  "unit": "chat"},
}


class MRL_BillingLayer:
    """母體計費/額度核心。每個用戶有方案、用量、計費記錄。"""

    def __init__(self, store: pathlib.Path = _STORE) -> None:
        self.origin_signature = ORIGIN_SIGNATURE
        self.store = pathlib.Path(store)
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

    def _month(self) -> str:
        return time.strftime("%Y-%m")

    def register(self, user_id: str, plan: str = "free") -> Dict[str, Any]:
        if plan not in PLANS:
            return {"error": f"unknown plan: {plan}", "plans": list(PLANS)}
        self._data["users"][user_id] = {
            "plan": plan, "usage": {}, "ledger": [],
            "registered_at": int(time.time()),
        }
        self._save()
        return {"user_id": user_id, "plan": plan, "quota": PLANS[plan]["monthly_quota"],
                "origin_signature": ORIGIN_SIGNATURE}

    # 用量檢查 + 計費(deny-by-default:超額拒絕)
    def charge(self, user_id: str, units: int = 1, kind: str = "chat") -> Dict[str, Any]:
        u = self._data["users"].get(user_id)
        if u is None:
            u = self._data["users"].setdefault(user_id, {
                "plan": "free", "usage": {}, "ledger": [], "registered_at": int(time.time())})
        plan = u["plan"]
        quota = PLANS[plan]["monthly_quota"]
        m = self._month()
        used = u["usage"].get(m, 0)

        # 拒絕非正數用量(否則 units<=0 會繞過額度檢查、灌水 remaining)
        if not isinstance(units, int) or units <= 0:
            return {"allowed": False, "reason": "invalid_units",
                    "detail": "units must be a positive integer",
                    "used": used, "quota": quota, "plan": plan,
                    "origin_signature": ORIGIN_SIGNATURE}

        if used + units > quota:
            rec = {"ts": int(time.time()), "result": "quota_exceeded",
                   "used": used, "quota": quota, "kind": kind}
            u["ledger"].append(rec)
            self._save()
            return {"allowed": False, "reason": "quota_exceeded",
                    "used": used, "quota": quota, "plan": plan,
                    "origin_signature": ORIGIN_SIGNATURE}

        u["usage"][m] = used + units
        rec = {"ts": int(time.time()), "result": "charged", "units": units,
               "kind": kind, "month_used": u["usage"][m]}
        u["ledger"].append(rec)        # rl_03 audit:每筆記錄
        self._save()
        return {"allowed": True, "charged": units, "month_used": u["usage"][m],
                "quota": quota, "remaining": quota - u["usage"][m], "plan": plan,
                "origin_signature": ORIGIN_SIGNATURE}

    def usage(self, user_id: str) -> Dict[str, Any]:
        u = self._data["users"].get(user_id)
        if u is None:
            return {"error": "user not found"}
        m = self._month()
        return {"user_id": user_id, "plan": u["plan"],
                "month": m, "used": u["usage"].get(m, 0),
                "quota": PLANS[u["plan"]]["monthly_quota"],
                "ledger_entries": len(u["ledger"]),
                "origin_signature": ORIGIN_SIGNATURE}


def main() -> int:
    import tempfile
    b = MRL_BillingLayer(store=pathlib.Path(tempfile.mktemp(suffix=".json")))
    print("註冊:", b.register("u1", "standard")["plan"], "quota=", b.register("u2", "extended")["quota"])
    for i in range(3):
        r = b.charge("u1", 1)
        print(f"  charge#{i+1}: allowed={r['allowed']} remaining={r.get('remaining')}")
    print("用量:", b.usage("u1"))
    print("MRL_BILLING_LAYER_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
