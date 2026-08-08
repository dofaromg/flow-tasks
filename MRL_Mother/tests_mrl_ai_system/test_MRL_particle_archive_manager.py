"""
test_MRL_particle_archive_manager.py — 粒子庫取回/觀測/復活驗收(T3)
origin_signature: MrLiouWord

補洞:粒子庫從「只存」→「可取回、可觀測、可復活」。
rl_15 復活不刪源;rl_18 怎麼過去怎麼回來;no_proof 找不到誠實回錯。
"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "09_workflow"))

from MRL_ParticleArchive_Manager_v1 import MRL_ParticleArchiveManager  # noqa: E402


def _mgr():
    return MRL_ParticleArchiveManager()


class TestList:
    def test_list_returns_files(self):
        r = _mgr().list()
        assert r["total_files"] > 0
        assert "groups" in r
        assert r["origin_signature"] == "MrLiouWord"

    def test_list_has_known_groups(self):
        r = _mgr().list()
        assert "PR19" in r["groups"] or "External" in r["groups"]


class TestObserve:
    def test_observe_existing(self):
        r = _mgr().observe("MRL_OpenGraphProtocol_v1")
        assert "preview" in r
        assert r["mother_signed"] is True       # 母體簽章粒子
        assert r["lines"] > 0

    def test_observe_not_found(self):
        r = _mgr().observe("does_not_exist_xyz")
        assert "error" in r                      # no_proof:誠實回錯


class TestSearch:
    def test_search_by_filename(self):
        r = _mgr().search("OpenGraph")
        assert r["hit_count"] >= 1

    def test_search_by_content(self):
        r = _mgr().search("og:title")
        assert r["hit_count"] >= 1               # 內容裡有 og:title

    def test_search_miss(self):
        r = _mgr().search("zzz_no_such_keyword_zzz")
        assert r["hit_count"] == 0


class TestRestore:
    def test_restore_creates_file_and_keeps_source(self, tmp_path):
        mgr = _mgr()
        rel = "_restore_test_pytest/idx.html"
        try:
            r = mgr.restore("ui__mrl_app__index.html", rel)
            assert r["restored"] is True
            assert r["source_particle"].startswith("MRL_ParticleArchive")  # 源仍在(rl_15)
            from MRL_ParticleArchive_Manager_v1 import _REPO
            assert (_REPO / rel).exists()
        finally:
            import shutil
            from MRL_ParticleArchive_Manager_v1 import _REPO
            shutil.rmtree(_REPO / "_restore_test_pytest", ignore_errors=True)

    def test_restore_not_found(self):
        r = _mgr().restore("nope_particle", "_x/y.txt")
        assert r["restored"] is False

    def test_restore_no_overwrite_by_default(self, tmp_path):
        mgr = _mgr()
        rel = "_restore_test_pytest2/a.html"
        from MRL_ParticleArchive_Manager_v1 import _REPO
        try:
            mgr.restore("ui__mrl_app__index.html", rel)
            r2 = mgr.restore("ui__mrl_app__index.html", rel)  # 第二次不給 overwrite
            assert r2["restored"] is False
            assert "exists" in r2["error"]
        finally:
            import shutil
            shutil.rmtree(_REPO / "_restore_test_pytest2", ignore_errors=True)

    def test_restore_rejects_outside_repo(self):
        r = _mgr().restore("ui__mrl_app__index.html", "../escape.txt")
        assert r["restored"] is False
