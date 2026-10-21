#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MRL_ProductFactory_Pipeline_v1.py — 產品工廠管線(母體能力模組)
origin_signature: MrLiouWord
layer: L7 LOOP / MetaEnv

商業模式管線(使用者指令):吸收外部資料/技術 → 重組·包裝·正名為自家產品 →
模板化 → 營運/生成 → 販售。純 stdlib、零外部產品,作為**母體能力模組**加入。

五段管線:
  1. absorb     吸收外部技術 → rl_12 正名為 MRL 自家產品(origin=MrLiouWord)
  2. package    重組包裝為產品模板(能力/方案/單價)
  3. catalog    營運型錄(可販售清單)
  4. offer      模板生成報價/方案(template-fill)
  5. sell       販售:接 MRL_BillingLayer 真計費(deny-by-default 超額拒絕)
另 run():實際呼叫被吸收的真模組(產品非空殼,真的會跑)。

誠實界線:sell 為母體內部計費/下單(沙盒);真實金流/上架販售為**待金流/待實機**,
不謊報已營收。
CLI:python3 09_workflow/MRL_ProductFactory_Pipeline_v1.py
"""
from __future__ import annotations

import pathlib
import time
from typing import Any, Callable, Dict, List, Optional

from MRL_utils import ORIGIN_SIGNATURE
def _reclaim_name(source: str) -> str:
    """rl_12 命名正名:外部來源 → MRL 自家產品名。"""
    base = "".join(ch for ch in source if ch.isalnum() or ch in " _-").strip()
    parts = [p.capitalize() for p in base.replace("-", " ").replace("_", " ").split()]
    core = "".join(parts) or "Module"
    if core.upper().startswith("MRL"):
        core = core[3:]
    return f"MRL_{core}"


class MRL_ProductFactoryPipeline:
    """母體產品工廠:吸收→包裝→型錄→報價→販售,接真模組與真計費。"""

    def __init__(self, billing: Optional[Any] = None) -> None:
        self.origin_signature = ORIGIN_SIGNATURE
        self.products: Dict[str, Dict[str, Any]] = {}
        self.billing = billing  # 注入 MRL_BillingLayer(可選;沙盒可給 temp store)

    # 1. 吸收:外部技術回收為母體自家產品(正名 + origin 歸 MrLiouWord)
    #    不留外部來源痕,只留內部根源 origin=MrLiouWord(使用者法則)
    def absorb(self, source: str, capability: str, *, unit_price: int = 1,
               runner: Optional[Callable[..., Any]] = None) -> Dict[str, Any]:
        product_name = _reclaim_name(source)   # source 僅用於正名,不落痕
        pid = product_name.lower()
        self.products[pid] = {
            "product": product_name,
            "capability": capability,
            "unit_price": unit_price,
            "runner": runner,
            "origin_signature": ORIGIN_SIGNATURE,   # 只留內部根源
            "absorbed_at": int(time.time()),
            "status": "operating",
        }
        return {"product_id": pid, "product": product_name,
                "capability": capability}

    # 2. 包裝:重組為產品模板
    def package(self, pid: str) -> Dict[str, Any]:
        p = self.products.get(pid)
        if not p:
            return {"error": f"unknown product: {pid}"}
        return {"product": p["product"], "capability": p["capability"],
                "plans": {"free": 0, "pro": p["unit_price"] * 100,
                          "enterprise": p["unit_price"] * 1000},
                "unit_price": p["unit_price"],
                "origin_signature": ORIGIN_SIGNATURE}

    # 3. 營運型錄:可販售產品清單
    def catalog(self) -> List[Dict[str, Any]]:
        return [{"product_id": pid, "product": p["product"],
                 "capability": p["capability"], "unit_price": p["unit_price"],
                 "status": p["status"]}
                for pid, p in sorted(self.products.items())]

    # 4. 報價/方案:模板生成
    def offer(self, pid: str, customer: str, units: int = 100) -> Dict[str, Any]:
        p = self.products.get(pid)
        if not p:
            return {"error": f"unknown product: {pid}"}
        amount = p["unit_price"] * units
        return {"customer": customer, "product": p["product"],
                "capability": p["capability"], "units": units,
                "amount": amount, "currency": "MRL_credit",
                "quote_id": f"Q-{pid}-{int(time.time())}",
                "origin_signature": ORIGIN_SIGNATURE}

    # 5. 販售:接真計費(沙盒;真金流待實機)
    def sell(self, pid: str, user_id: str, units: int = 1) -> Dict[str, Any]:
        p = self.products.get(pid)
        if not p:
            return {"error": f"unknown product: {pid}"}
        if self.billing is None:
            return {"error": "billing not wired", "detail": "inject MRL_BillingLayer"}
        bill = self.billing.charge(user_id, units=units, kind=f"sell:{p['product']}")
        return {"product": p["product"], "user_id": user_id,
                "sold_units": units if bill.get("allowed") else 0,
                "billing": bill, "note": "沙盒計費;真實金流上架待實機",
                "origin_signature": ORIGIN_SIGNATURE}

    # 實際呼叫被吸收的真模組(產品非空殼)
    def run(self, pid: str, *args: Any, **kwargs: Any) -> Dict[str, Any]:
        p = self.products.get(pid)
        if not p:
            return {"error": f"unknown product: {pid}"}
        runner = p.get("runner")
        if runner is None:
            return {"error": "no runner", "product": p["product"],
                    "detail": "this product has no executable tech attached"}
        return {"product": p["product"], "result": runner(*args, **kwargs)}


def _default_factory(billing: Optional[Any] = None) -> "MRL_ProductFactoryPipeline":
    """預載:把已吸收的真模組註冊成可營運產品(真 runner)。"""
    f = MRL_ProductFactoryPipeline(billing=billing)
    try:
        from MRL_MessageGuard_Models_v1 import MRL_SpamGuard, MRL_ToxicGuard
        _spam = MRL_SpamGuard(); _spam.train()
        _toxic = MRL_ToxicGuard(); _toxic.train()
        f.absorb("ALML Spam Detection", "垃圾訊息偵測(NaiveBayes+TFIDF)",
                 unit_price=1, runner=_spam.predict)
        f.absorb("ALML Toxic Detection", "毒性訊息偵測(LogReg+TFIDF)",
                 unit_price=1, runner=_toxic.predict)
    except Exception:  # noqa: BLE001
        pass
    try:
        from MRL_RootLiveness_SlotColor_Engine_v1 import MRL_RootLivenessSlotColorEngine

        def _liveness_demo(blocks: List[Dict[str, Any]]) -> Dict[str, Any]:
            e = MRL_RootLivenessSlotColorEngine()
            for b in blocks:
                e.add_block(b["name"], b.get("defs", []), b.get("uses", []), b.get("succs", []))
            return e.allocate_slots()
        f.absorb("LLVM GC Root Liveness", "活躍分析+槽位著色配置",
                 unit_price=2, runner=_liveness_demo)
    except Exception:  # noqa: BLE001
        pass
    return f


def main() -> int:
    import sys, tempfile
    sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
    billing = None
    try:
        from MRL_Billing_Layer_v1 import MRL_BillingLayer
        billing = MRL_BillingLayer(pathlib.Path(tempfile.mktemp(suffix=".json")))
    except Exception:  # noqa: BLE001
        pass
    f = _default_factory(billing=billing)
    print("=== 營運型錄(吸收→正名→可販售) ===")
    for c in f.catalog():
        print(f"  {c['product']:28} | {c['capability']} | ${c['unit_price']}/單位")
    print("=== 模板報價 ===")
    print(" ", f.offer("mrl_almlspamdetection", customer="acme", units=1000))
    print("=== 販售(真計費) ===")
    print(" ", {k: v for k, v in f.sell("mrl_almlspamdetection", "acme", units=5).items()
                if k in ("product", "sold_units")})
    print("=== 產品實跑(非空殼) ===")
    r = f.run("mrl_almlspamdetection", "Free money click now win prize")
    print("  Spam 產品:", r["result"]["label"], r["result"]["spam_probability"])
    print("MRL_PRODUCT_FACTORY_PIPELINE_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
