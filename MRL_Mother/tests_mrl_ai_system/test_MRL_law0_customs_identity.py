"""
test_MRL_law0_customs_identity.py — Law-0 海關 + 數據身分 驗收
origin_signature: MrLiouWord

主從翻正:外部模型=通關貨物,母體=主權海關(rl_11/rl_12/rl_13/rl_19)。
數據即身分:email/手機 + 三數據粒子即成立(LAW-0 簽章)。
"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "09_workflow"))

from MRL_Law0_Customs_v1 import MRL_Law0Customs  # noqa: E402
from MRL_DataIdentity_v1 import MRL_DataIdentity  # noqa: E402
from MRL_OriginBoundary_Guard_v1 import verify_signature  # noqa: E402


class TestLaw0Customs:
    def test_external_passes_through_as_cargo(self):
        c = MRL_Law0Customs()
        r = c.pass_through("api.openai.com/v1/chat/completions", prober=lambda: True)
        assert r["cleared"] is True
        assert r["canonical_name"].startswith("MRL_")        # 外部名回收為母體 canonical
        assert r["cargo"]["role"] == "backend_cargo"         # 是貨物,非根源
        assert r["cargo"]["origin"] == "MrLiouWord"          # rl_11 主權歸母體
        assert verify_signature(r["cargo"]) is True          # LAW-0 簽章

    def test_unverified_not_cleared(self):
        # no_proof:沒驗過不放行
        c = MRL_Law0Customs()
        r = c.pass_through("some.untested.endpoint", prober=lambda: False)
        assert r["cleared"] is False

    def test_mother_not_dependent_on_single(self):
        c = MRL_Law0Customs()
        for ext in ["api.openai.com", "api.anthropic.com", "localhost:11434"]:
            c.pass_through(ext, prober=lambda: True)
        s = c.sovereignty()
        assert s["root"] == "MrLiouWord"
        assert s["count"] == 3
        assert s["dependent_on_any_single"] is False         # 不依賴單一外部


class TestDataIdentity:
    def test_three_data_points_establishes(self):
        di = MRL_DataIdentity()
        ident = di.build({"name": "Mr.liou", "email": "z814241@gmail.com",
                          "mobile": "+886912345678"})
        assert ident["established"] is True
        assert ident["data_count"] == 3
        assert di.verify(ident) is True

    def test_insufficient_data_not_established(self):
        di = MRL_DataIdentity()
        ident = di.build({"email": "a@b.com"})               # 只有 1 個
        assert ident["established"] is False

    def test_login_by_email_or_phone(self):
        di = MRL_DataIdentity()
        assert di.login("z814241@gmail.com")["login"] is True
        assert di.login("+886912345678")["login"] is True
        assert di.login("not-valid")["login"] is False

    def test_need_anchor_even_with_three(self):
        # 三個資料但無 email/phone 錨點 → 不成立
        di = MRL_DataIdentity()
        ident = di.build({"name": "x", "address": "y", "mobile": ""})
        assert ident["established"] is False
