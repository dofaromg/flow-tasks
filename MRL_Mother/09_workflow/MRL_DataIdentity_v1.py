#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MRL_DataIdentity_v1.py — 數據即身分(母體運行只需數據)
origin_signature: MrLiouWord
layer: L0 ROOT (身分) + L3 LAW

Mr.liou 模式(極簡):email 或 手機 即可登入。
母體運行只有數據 —— 姓名/地址/電話/email/手機,三者即成立身分。
無密碼、無外部 OAuth 強依賴:身分由「數據粒子」構成(對齊 rl_15 粒子 / LAW-0 簽章)。

成立規則(three-of-data):
  - 主鍵至少一:email 或 phone(可登入錨點)
  - 任一資料粒子滿 3 個(name/address/phone/email/mobile)→ 身分成立(established)
  - 身分本體即數據,經 LAW-0 母體簽章,溯源歸母體(rl_11)。
"""
from __future__ import annotations

import os
import re
import sys
from typing import Any, Dict, List, Optional

_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)

from MRL_OriginBoundary_Guard_v1 import embed_signature, verify_signature  # noqa: E402

from MRL_utils import ORIGIN_SIGNATURE
_DATA_FIELDS = ("name", "address", "phone", "email", "mobile")
_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
_PHONE_RE = re.compile(r"^\+?[0-9][0-9\-\s]{5,}$")


def _valid(field: str, value: str) -> bool:
    v = (value or "").strip()
    if not v:
        return False
    if field == "email":
        return bool(_EMAIL_RE.match(v))
    if field in ("phone", "mobile"):
        return bool(_PHONE_RE.match(v))
    return len(v) >= 1


class MRL_DataIdentity:
    """數據即身分。三個資料粒子 + 一個可登入錨點(email/phone)即成立。"""

    MIN_DATA_POINTS = 3

    def build(self, data: Dict[str, str]) -> Dict[str, Any]:
        """以數據構成身分;回傳已簽章的身分粒子或未成立原因。"""
        present = {f: data[f].strip() for f in _DATA_FIELDS
                   if f in data and _valid(f, data.get(f, ""))}
        anchor = present.get("email") or present.get("phone") or present.get("mobile")
        established = bool(anchor) and len(present) >= self.MIN_DATA_POINTS

        identity = {
            "persona_kind": "data_identity",
            "anchor": anchor,                          # email/手機 登入錨點
            "data_points": present,                    # 數據粒子(只有數據)
            "data_count": len(present),
            "established": established,
            "origin": ORIGIN_SIGNATURE,                # rl_11 溯源歸母體
        }
        if not established:
            identity["reason"] = (
                "need login anchor (email/phone) + >=3 data points; "
                f"have anchor={bool(anchor)}, count={len(present)}"
            )
            return identity
        return embed_signature(identity, ORIGIN_SIGNATURE)  # LAW-0 簽章

    def login(self, anchor: str) -> Dict[str, Any]:
        """email 或 手機 即可登入(錨點驗證)。"""
        a = (anchor or "").strip()
        ok = bool(_EMAIL_RE.match(a) or _PHONE_RE.match(a))
        return {"login": ok, "anchor": a, "origin_signature": ORIGIN_SIGNATURE,
                "reason": "ok" if ok else "anchor must be a valid email or phone"}

    def verify(self, identity: Dict[str, Any]) -> bool:
        """驗證身分粒子的母體簽章。"""
        return identity.get("established", False) and verify_signature(identity)


def main() -> int:
    import json
    di = MRL_DataIdentity()
    # 範例:姓名 + email + 手機 = 三數據 → 成立
    ident = di.build({"name": "Mr.liou", "email": "z814241@gmail.com",
                      "mobile": "+886912345678"})
    print(json.dumps({"established": ident["established"],
                      "anchor": ident["anchor"], "count": ident["data_count"],
                      "verified": di.verify(ident)}, ensure_ascii=False, indent=2))
    print("login by email:", di.login("z814241@gmail.com")["login"])
    print("MRL_DATA_IDENTITY_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
