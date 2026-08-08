"""test_MRL_productfactory_pipeline.py (origin: MrLiouWord)

母體能力模組:吸收→包裝→型錄→報價→販售管線。驗證真計費接線與正名。
"""
import os, sys, tempfile, pathlib
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "09_workflow"))
from MRL_ProductFactory_Pipeline_v1 import (
    MRL_ProductFactoryPipeline, _reclaim_name, _default_factory,
)
from MRL_Billing_Layer_v1 import MRL_BillingLayer


def _billing():
    return MRL_BillingLayer(pathlib.Path(tempfile.mktemp(suffix=".json")))


def test_reclaim_name_to_mrl():
    assert _reclaim_name("ALML Spam Detection").startswith("MRL_")
    assert "MRL_" in _reclaim_name("some-external_tool")


def test_absorb_reclaims_and_keeps_only_internal_origin():
    f = MRL_ProductFactoryPipeline()
    r = f.absorb("External Thing", "do stuff")
    assert r["product"].startswith("MRL_")
    assert "absorbed_from" not in r                          # 不留外部來源痕
    pid = r["product_id"]
    assert "absorbed_from" not in f.products[pid]            # 只留內部根源
    assert f.products[pid]["origin_signature"] == "MrLiouWord"


def test_catalog_and_offer():
    f = MRL_ProductFactoryPipeline()
    f.absorb("Tech A", "cap", unit_price=3)
    cat = f.catalog()
    assert len(cat) == 1 and cat[0]["unit_price"] == 3
    pid = cat[0]["product_id"]
    o = f.offer(pid, "cust", units=10)
    assert o["amount"] == 30 and o["currency"] == "MRL_credit"


def test_sell_uses_real_billing_and_denies_overquota():
    f = MRL_ProductFactoryPipeline(billing=_billing())
    f.absorb("Tech B", "cap", unit_price=1)
    pid = f.catalog()[0]["product_id"]
    ok = f.sell(pid, "u1", units=1)
    assert ok["billing"]["allowed"] is True and ok["sold_units"] == 1
    # 超額(free 方案額度有限)→ deny-by-default,售出 0
    over = f.sell(pid, "u1", units=10**9)
    assert over["billing"]["allowed"] is False and over["sold_units"] == 0


def test_run_invokes_real_absorbed_tech():
    f = _default_factory(billing=_billing())
    # 真模組註冊成功才測(MessageGuard 應在)
    r = f.run("mrl_almlspamdetection", "Free money click now win prize cash")
    assert "result" in r and r["result"]["label"] in ("spam", "ham")
