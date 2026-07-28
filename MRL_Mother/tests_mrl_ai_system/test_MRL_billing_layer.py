"""test_MRL_billing_layer.py — 金錢層驗收 (origin_signature: MrLiouWord)"""
from __future__ import annotations
import os, sys, tempfile, pathlib
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "09_workflow"))
from MRL_Billing_Layer_v1 import MRL_BillingLayer, PLANS  # noqa: E402


def _b():
    return MRL_BillingLayer(store=pathlib.Path(tempfile.mktemp(suffix=".json")))


def test_register_plans():
    b = _b()
    assert b.register("u1", "standard")["quota"] == PLANS["standard"]["monthly_quota"]
    assert b.register("u2", "unlimited")["quota"] == PLANS["unlimited"]["monthly_quota"]


def test_charge_and_remaining():
    b = _b(); b.register("u1", "standard")
    r = b.charge("u1", 1)
    assert r["allowed"] is True and r["remaining"] == PLANS["standard"]["monthly_quota"] - 1


def test_quota_exceeded_denies():
    b = _b(); b.register("u1", "standard")
    r = b.charge("u1", PLANS["standard"]["monthly_quota"] + 1)
    assert r["allowed"] is False and r["reason"] == "quota_exceeded"


def test_usage_and_audit_ledger():
    b = _b(); b.register("u1", "standard")
    b.charge("u1", 1); b.charge("u1", 1)
    u = b.usage("u1")
    assert u["used"] == 2 and u["ledger_entries"] == 2
    assert u["origin_signature"] == "MrLiouWord"


def test_unknown_plan_rejected():
    assert "error" in _b().register("u1", "nonsense")


def test_reject_negative_units():
    b=_b(); b.register("u","standard")
    assert b.charge("u",-100)["reason"]=="invalid_units"

def test_reject_zero_units():
    b=_b(); b.register("u","standard")
    assert b.charge("u",0)["reason"]=="invalid_units"
