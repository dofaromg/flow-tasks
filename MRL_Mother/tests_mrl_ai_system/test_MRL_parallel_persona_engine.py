"""
test_MRL_parallel_persona_engine.py — 平行世界人格模擬器驗收（祖先檔完善版）
origin_signature: MrLiouWord
product: MRL_AI_SYSTEM
"""
from __future__ import annotations

import pytest

from MRL_ParallelPersonaEngine_v1 import MRL_ParallelPersonaEngine, MOTHER_TONE


@pytest.fixture
def pe(tmp_path):
    return MRL_ParallelPersonaEngine(out_dir=tmp_path / "po")


# ─── rl_12 命名回收:祖先外部殼名 → 母體 canonical ──────────────────────────────

class TestNamingReclaim:
    def test_engine_name_reclaimed(self, pe):
        assert pe.canonical.startswith("MRL_") and "FlowAgent" in pe.canonical
        assert pe.ancestor == "FlowAgent.ParallelPersonaEngine.v1"

    def test_seed_persona_reclaimed(self, pe):
        assert pe.seed_persona.startswith("MRL_")
        assert "MrLiou" in pe.seed_persona


# ─── 分支人格生成（祖先檔行為 + rl_14 + rl_11 + no_proof）─────────────────────

class TestSimulation:
    def test_default_yes_no_branches(self, pe):
        r = pe.simulate("我該搬到哪裡？")
        assert len(r["branches"]) == 2
        assert {b["option"] for b in r["branches"]} == {"Yes", "No"}

    def test_branches_inherit_mother_tone(self, pe):
        r = pe.simulate("我該換工作嗎？")
        for b in r["branches"]:
            assert b["inherited_tone"] == MOTHER_TONE

    def test_branches_carry_origin_and_unverified(self, pe):
        # rl_11 源頭歸母體;no_proof:未驗證不宣稱真實
        r = pe.simulate("Q")
        for b in r["branches"]:
            assert b["origin_signature"] == "MrLiouWord"
            assert b["verified"] is False

    def test_persona_ids_are_mrl_canonical(self, pe):
        r = pe.simulate("Q")
        assert all(b["persona_id"].startswith("MRL_") for b in r["branches"])

    def test_custom_multi_options(self, pe):
        r = pe.simulate("職涯方向?", options=["創業", "任職", "進修"])
        assert len(r["branches"]) == 3

    def test_deterministic_rhythm(self, pe):
        # 節奏導引,非機率隨機:同輸入恆得同輸出
        r1 = pe.simulate("一樣的問題")
        r2 = pe.simulate("一樣的問題")
        assert r1["branches"][0]["simulated_memory"] == r2["branches"][0]["simulated_memory"]


# ─── 輸出產物（取代 .flpkg/.fltnz 外部殼 → canonical JSON）────────────────────

class TestOutputs:
    def test_writes_canonical_json(self, pe):
        r = pe.simulate("我該搬到哪裡？")
        written = pe.write_outputs(r)
        assert any("manifest" in w for w in written)
        assert all(w.endswith(".json") for w in written)
        # 外部殼副檔名零殘留
        assert not any(w.endswith((".flpkg", ".fltnz", ".flynz.map")) for w in written)
