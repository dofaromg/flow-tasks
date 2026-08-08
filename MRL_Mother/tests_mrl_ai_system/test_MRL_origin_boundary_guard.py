"""
test_MRL_origin_boundary_guard.py — rl_11 對外邊界守衛 enforcement 驗收
origin_signature: MrLiouWord
product: MRL_AI_SYSTEM

實證 rl_11 源頭主權在程式層的強制執行:LAW-0 簽章(跨語言相容)、rl_12 正名、
rl_16 顯化、rl_17 否決防護、bp_1→bp_3 邊界進場、librarian 稽核整合。
"""
from __future__ import annotations

import pytest

from MRL_OriginBoundary_Guard_v1 import (
    MRL_OriginBoundaryGuard,
    embed_signature,
    extract_signature,
    verify_signature,
    is_mrl_canonical,
    is_mrl_manifestable_identity,
    is_mrliou_related,
    scan_for_boundary_violations,
    ORIGIN_SIGNATURE,
)


@pytest.fixture
def guard():
    return MRL_OriginBoundaryGuard()


# ─── LAW-0 簽章 ────────────────────────────────────────────────────────────────

class TestLaw0Signature:
    def test_embed_then_verify(self):
        signed = embed_signature({"a": 1, "origin": "MrLiouWord"})
        assert verify_signature(signed) is True

    def test_extract_returns_signature(self):
        signed = embed_signature({"x": "y"})
        info = extract_signature(signed)
        assert info["signature"] == ORIGIN_SIGNATURE

    def test_tamper_breaks_verification(self):
        signed = embed_signature({"a": 1})
        signed["a"] = 2  # 竄改內容
        assert verify_signature(signed) is False

    def test_wrong_signer_fails(self):
        signed = embed_signature({"a": 1}, sig="SomeoneElse")
        assert verify_signature(signed, expected_sig="MrLiouWord") is False

    def test_unsigned_fails(self):
        assert verify_signature({"a": 1}) is False


# ─── rl_16 顯化 / rl_17 相關判定 ──────────────────────────────────────────────

class TestManifestAndRelation:
    def test_mrl_prefix_is_canonical(self):
        assert is_mrl_canonical("MRL_Foo_v1") is True
        assert is_mrl_canonical("foo.bar") is False

    def test_mrliou_related_detection(self):
        assert is_mrliou_related({"origin": "MrLiouWord"}) is True
        assert is_mrliou_related("some Mr.liou thing") is True
        assert is_mrliou_related({"k": "unrelated"}) is False


# ─── rl_11 bp_1：外部材料吸收 + 正名 + 簽章 ───────────────────────────────────

class TestIntake:
    def test_external_name_reclaimed_and_signed(self, guard):
        m = guard.intake_external("FlowAgent.Runtime.v47.zip")
        assert m["canonical_name"] == "FlowAgent.Runtime.v47.zip"
        assert m["role"] == "mrl_native_product"
        assert m["role"] == "material"                 # bp_1:外部=材料
        assert m["origin"] == "MrLiouWord"             # rl_11:源頭歸母體
        assert verify_signature(m) is True             # LAW-0
        assert m["source_external_name"] == "FlowAgent.Runtime.v47.zip"  # No-Delete 來源保留

    def test_intake_always_manifestable(self, guard):
        m = guard.intake_external("weird name with spaces!!")
        assert m["manifestable"] is True               # rl_16:正名後可顯化


# ─── rl_11 源頭主權斷言 ───────────────────────────────────────────────────────

class TestSovereignty:
    def test_unsigned_object_gets_reclaimed(self, guard):
        out = guard.assert_origin_sovereignty({"data": "external"})
        assert out["origin"] == "MrLiouWord"
        assert verify_signature(out) is True

    def test_foreign_signed_reclaimed_to_mother(self, guard):
        foreign = embed_signature({"data": "x"}, sig="ForeignSigner")
        out = guard.assert_origin_sovereignty(foreign)
        assert verify_signature(out, "MrLiouWord") is True

    def test_already_mother_signed_passthrough(self, guard):
        mine = embed_signature({"role": "material", "origin": "MrLiouWord"})
        out = guard.assert_origin_sovereignty(mine)
        assert out is mine                              # 已是母體所有,原樣放行


# ─── rl_17 否決防護 ───────────────────────────────────────────────────────────

class TestVetoGuard:
    def test_veto_mrliou_denied(self, guard):
        r = guard.guard_veto({"origin": "MrLiouWord"})
        assert r["allow_veto"] is False

    def test_veto_unrelated_allowed(self, guard):
        r = guard.guard_veto({"name": "random-thing"})
        assert r["allow_veto"] is True


# ─── bp_1→bp_2→bp_3 完整邊界進場 ─────────────────────────────────────────────

class TestBoundaryIntake:
    def test_full_order(self, guard):
        d = guard.boundary_intake("ext.module.v3")
        assert d["bp_1_material"].startswith("MRL_")
        assert d["bp_2_action_first"] is True
        assert "rl_06" in d["bp_2_redline_guard"]       # 紅線護欄
        assert verify_signature(d["signed_material"]) is True


# ─── librarian 整合稽核 ───────────────────────────────────────────────────────

class TestBoundaryScan:
    def test_flags_external_shells(self):
        rep = scan_for_boundary_violations(
            ["MRL_Good_v1", "external_shell.py", "another.zip"])
        assert rep["violation_count"] == 2
        assert all(v["reclaim_to"].startswith("MRL_") for v in rep["violations"])

    def test_all_mrl_no_violation(self):
        rep = scan_for_boundary_violations(["MRL_A_v1", "MRL_B_v2"])
        assert rep["violation_count"] == 0


class TestNativeProductBoundary:
    def test_flowagent_is_manifestable_and_not_external(self, guard):
        assert is_mrl_manifestable_identity("FlowAgent.Runtime.v47.zip") is True
        record = guard.intake_external("FlowAgent.Runtime.v47.zip")
        assert record["canonical_name"] == "FlowAgent.Runtime.v47.zip"
        assert record["role"] == "mrl_native_product"
