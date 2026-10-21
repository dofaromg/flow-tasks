"""
test_conversation_manager.py — Smoke tests for conversation_manager.py
origin_signature: MrLiouWord
"""
from __future__ import annotations

import pathlib
import tempfile

import pytest

from conversation_manager import ConversationManager


@pytest.fixture
def tmp_mgr(tmp_path: pathlib.Path) -> ConversationManager:
    """Return a ConversationManager backed by a temp file."""
    store = tmp_path / "test_conversations.json"
    return ConversationManager(store_path=store)


# ─── Session lifecycle ────────────────────────────────────────────────────────

class TestSessionLifecycle:
    def test_new_session_returns_id(self, tmp_mgr):
        sid = tmp_mgr.new_session()
        assert isinstance(sid, str)
        assert len(sid) > 0

    def test_new_session_with_label(self, tmp_mgr):
        sid = tmp_mgr.new_session(label="test-chat")
        sess = tmp_mgr.get_session(sid)
        assert sess is not None
        assert sess.label == "test-chat"

    def test_session_count_increments(self, tmp_mgr):
        assert len(tmp_mgr) == 0
        tmp_mgr.new_session()
        assert len(tmp_mgr) == 1
        tmp_mgr.new_session()
        assert len(tmp_mgr) == 2

    def test_delete_session(self, tmp_mgr):
        sid = tmp_mgr.new_session()
        deleted = tmp_mgr.delete_session(sid)
        assert deleted is True
        assert tmp_mgr.get_session(sid) is None

    def test_delete_nonexistent_session_returns_false(self, tmp_mgr):
        assert tmp_mgr.delete_session("does-not-exist") is False

    def test_list_sessions(self, tmp_mgr):
        s1 = tmp_mgr.new_session(label="a")
        s2 = tmp_mgr.new_session(label="b")
        summaries = tmp_mgr.list_sessions()
        ids = [s["session_id"] for s in summaries]
        assert s1 in ids
        assert s2 in ids


# ─── Message operations ───────────────────────────────────────────────────────

class TestMessages:
    def test_add_and_retrieve_messages(self, tmp_mgr):
        sid = tmp_mgr.new_session()
        tmp_mgr.add_message(sid, "user", "Hello!")
        tmp_mgr.add_message(sid, "assistant", "Hi there!")
        history = tmp_mgr.get_history(sid)
        roles = [m["role"] for m in history]
        assert "user" in roles
        assert "assistant" in roles

    def test_messages_have_origin_signature(self, tmp_mgr):
        sid = tmp_mgr.new_session()
        tmp_mgr.add_message(sid, "user", "test")
        history = tmp_mgr.get_history(sid)
        for msg in history:
            assert msg.get("origin_signature") == "MrLiouWord"

    def test_invalid_role_raises(self, tmp_mgr):
        sid = tmp_mgr.new_session()
        with pytest.raises(ValueError):
            tmp_mgr.add_message(sid, "invalid_role", "content")

    def test_clear_session_keeps_system(self, tmp_mgr):
        sid = tmp_mgr.new_session(system_prompt="You are MRL.")
        tmp_mgr.add_message(sid, "user", "Hello")
        tmp_mgr.clear_session(sid, keep_system=True)
        history = tmp_mgr.get_history(sid)
        assert any(m["role"] == "system" for m in history)
        assert not any(m["role"] == "user" for m in history)


# ─── Persistence ──────────────────────────────────────────────────────────────

class TestPersistence:
    def test_sessions_reload_from_disk(self, tmp_path):
        store = tmp_path / "conv.json"
        mgr1 = ConversationManager(store_path=store)
        sid = mgr1.new_session(label="reload-test")
        mgr1.add_message(sid, "user", "Remember me?")

        mgr2 = ConversationManager(store_path=store)
        sess = mgr2.get_session(sid)
        assert sess is not None
        assert sess.label == "reload-test"

    def test_store_file_permissions(self, tmp_path):
        import os
        import stat
        store = tmp_path / "conv.json"
        mgr = ConversationManager(store_path=store)
        mgr.new_session()
        if os.name == "posix":
            mode = stat.S_IMODE(os.stat(store).st_mode)
            # File should be restricted to owner read/write only (0o600)
            assert mode == 0o600


# ─── export_markdown ─────────────────────────────────────────────────────────

class TestExportMarkdown:
    def test_export_returns_markdown_string(self, tmp_mgr):
        sid = tmp_mgr.new_session(label="My Chat")
        tmp_mgr.add_message(sid, "user", "Hello world")
        tmp_mgr.add_message(sid, "assistant", "Hi!")
        md = tmp_mgr.export_markdown(sid)
        assert isinstance(md, str)
        assert "# Conversation:" in md
        assert "My Chat" in md
        assert "Hello world" in md
        assert "Hi!" in md

    def test_export_nonexistent_session_returns_empty(self, tmp_mgr):
        md = tmp_mgr.export_markdown("no-such-id")
        assert md == ""

    def test_export_contains_origin_signature(self, tmp_mgr):
        sid = tmp_mgr.new_session()
        tmp_mgr.add_message(sid, "user", "test")
        md = tmp_mgr.export_markdown(sid)
        assert "MrLiouWord" in md
