"""
Tests for plugin_manager — PluginManager discover / activate / deactivate.
"""
import pathlib
import sys
import textwrap

import pytest

from plugin_manager import PluginManager, PluginRecord, ORIGIN_SIGNATURE


# ─── Helpers ──────────────────────────────────────────────────────────────────

def _write_plugin(dir_: pathlib.Path, filename: str, content: str) -> pathlib.Path:
    """Write a plugin Python file and return its path."""
    path = dir_ / filename
    path.write_text(textwrap.dedent(content), encoding="utf-8")
    return path


# ─── PluginRecord ─────────────────────────────────────────────────────────────

class TestPluginRecord:
    def test_to_dict_keys(self, tmp_path):
        manifest = {"id": "test_plugin", "name": "Test", "version": "1.0"}

        class FakeMod:
            pass

        record = PluginRecord(manifest, tmp_path / "p.py", FakeMod())
        d = record.to_dict()
        for key in ("id", "manifest", "path", "active", "loaded_at_ms", "error"):
            assert key in d

    def test_initial_active_false(self, tmp_path):
        manifest = {"id": "p", "name": "P", "version": "1.0"}

        class FakeMod:
            pass

        record = PluginRecord(manifest, tmp_path / "p.py", FakeMod())
        assert record.active is False


# ─── PluginManager — empty / missing directory ────────────────────────────────

class TestPluginManagerEmptyDir:
    def test_discover_nonexistent_dir(self, tmp_path):
        mgr = PluginManager(plugin_dir=tmp_path / "no_such_dir")
        found = mgr.discover()
        assert found == []

    def test_discover_empty_dir(self, tmp_path):
        plugin_dir = tmp_path / "plugins"
        plugin_dir.mkdir()
        mgr = PluginManager(plugin_dir=plugin_dir)
        assert mgr.discover() == []

    def test_list_plugins_empty(self, tmp_path):
        mgr = PluginManager(plugin_dir=tmp_path / "nope")
        assert mgr.list_plugins() == []


# ─── PluginManager — valid plugin ────────────────────────────────────────────

class TestPluginManagerValidPlugin:
    VALID_PLUGIN = """
        PLUGIN_MANIFEST = {
            "id":          "my_plugin",
            "name":        "My Plugin",
            "version":     "1.0",
            "description": "A test plugin.",
            "layer":       "L7",
            "group":       3,
            "author":      "TestAuthor",
        }

        activated_with = []

        def activate(registry):
            activated_with.append(registry)

        def deactivate():
            activated_with.clear()
    """

    @pytest.fixture
    def plugin_dir(self, tmp_path):
        d = tmp_path / "plugins"
        d.mkdir()
        _write_plugin(d, "my_plugin.py", self.VALID_PLUGIN)
        return d

    def test_discover_finds_plugin(self, plugin_dir):
        mgr = PluginManager(plugin_dir=plugin_dir)
        found = mgr.discover()
        assert "my_plugin" in found

    def test_get_returns_record(self, plugin_dir):
        mgr = PluginManager(plugin_dir=plugin_dir)
        mgr.discover()
        r = mgr.get("my_plugin")
        assert r is not None
        assert r.id == "my_plugin"

    def test_activate_sets_active(self, plugin_dir):
        mgr = PluginManager(plugin_dir=plugin_dir)
        mgr.discover()
        ok = mgr.activate("my_plugin")
        assert ok is True
        assert mgr.get("my_plugin").active is True

    def test_activate_calls_activate_fn(self, plugin_dir):
        sentinel = object()
        mgr = PluginManager(plugin_dir=plugin_dir, registry=sentinel)
        mgr.discover()
        mgr.activate("my_plugin")
        record = mgr.get("my_plugin")
        activated_with = record.module.activated_with
        assert len(activated_with) == 1
        assert activated_with[0] is sentinel

    def test_activate_idempotent(self, plugin_dir):
        mgr = PluginManager(plugin_dir=plugin_dir)
        mgr.discover()
        mgr.activate("my_plugin")
        ok = mgr.activate("my_plugin")
        assert ok is True
        # activate_fn called only once
        assert len(mgr.get("my_plugin").module.activated_with) == 1

    def test_deactivate_sets_inactive(self, plugin_dir):
        mgr = PluginManager(plugin_dir=plugin_dir)
        mgr.discover()
        mgr.activate("my_plugin")
        ok = mgr.deactivate("my_plugin")
        assert ok is True
        assert mgr.get("my_plugin").active is False

    def test_deactivate_calls_deactivate_fn(self, plugin_dir):
        mgr = PluginManager(plugin_dir=plugin_dir)
        mgr.discover()
        mgr.activate("my_plugin")
        mgr.deactivate("my_plugin")
        # deactivate() clears activated_with
        assert mgr.get("my_plugin").module.activated_with == []

    def test_deactivate_idempotent(self, plugin_dir):
        mgr = PluginManager(plugin_dir=plugin_dir)
        mgr.discover()
        ok = mgr.deactivate("my_plugin")
        assert ok is True

    def test_activate_all(self, plugin_dir):
        mgr = PluginManager(plugin_dir=plugin_dir)
        mgr.discover()
        results = mgr.activate_all()
        assert results["my_plugin"] is True

    def test_deactivate_all(self, plugin_dir):
        mgr = PluginManager(plugin_dir=plugin_dir)
        mgr.discover()
        mgr.activate_all()
        results = mgr.deactivate_all()
        assert results["my_plugin"] is True

    def test_lifecycle_log_events(self, plugin_dir):
        mgr = PluginManager(plugin_dir=plugin_dir)
        mgr.discover()
        mgr.activate("my_plugin")
        events = [e["event"] for e in mgr.lifecycle_log()]
        assert "discovered" in events
        assert "activated" in events

    def test_lifecycle_log_returns_copy(self, plugin_dir):
        mgr = PluginManager(plugin_dir=plugin_dir)
        mgr.discover()
        log = mgr.lifecycle_log()
        log.clear()
        assert len(mgr.lifecycle_log()) > 0


# ─── PluginManager — file without manifest ───────────────────────────────────

class TestPluginManagerNoManifest:
    def test_file_without_manifest_ignored(self, tmp_path):
        plugin_dir = tmp_path / "plugins"
        plugin_dir.mkdir()
        _write_plugin(plugin_dir, "no_manifest.py", "x = 1")
        mgr = PluginManager(plugin_dir=plugin_dir)
        found = mgr.discover()
        assert found == []

    def test_underscore_file_ignored(self, tmp_path):
        plugin_dir = tmp_path / "plugins"
        plugin_dir.mkdir()
        _write_plugin(plugin_dir, "_internal.py", """
            PLUGIN_MANIFEST = {"id": "internal", "name": "X"}
        """)
        mgr = PluginManager(plugin_dir=plugin_dir)
        found = mgr.discover()
        assert "internal" not in found


# ─── PluginManager — error handling ──────────────────────────────────────────

class TestPluginManagerErrors:
    def test_activate_unknown_plugin(self, tmp_path):
        mgr = PluginManager(plugin_dir=tmp_path)
        assert mgr.activate("nonexistent") is False

    def test_deactivate_unknown_plugin(self, tmp_path):
        mgr = PluginManager(plugin_dir=tmp_path)
        assert mgr.deactivate("nonexistent") is False

    def test_plugin_with_syntax_error_not_loaded(self, tmp_path):
        plugin_dir = tmp_path / "plugins"
        plugin_dir.mkdir()
        _write_plugin(plugin_dir, "broken.py", "def oops(: invalid syntax")
        mgr = PluginManager(plugin_dir=plugin_dir)
        found = mgr.discover()
        assert "broken" not in found

    def test_activate_error_logged(self, tmp_path):
        plugin_dir = tmp_path / "plugins"
        plugin_dir.mkdir()
        _write_plugin(plugin_dir, "bad_activate.py", """
            PLUGIN_MANIFEST = {"id": "bad_activate", "name": "Bad", "version": "1.0"}

            def activate(registry):
                raise RuntimeError("activation failed")
        """)
        mgr = PluginManager(plugin_dir=plugin_dir)
        mgr.discover()
        ok = mgr.activate("bad_activate")
        assert ok is False
        events = [e["event"] for e in mgr.lifecycle_log()]
        assert "activate_error" in events
