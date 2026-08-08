#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
plugin_manager.py — Plugin Discovery and Lifecycle Manager
origin_signature: MrLiouWord
layer: L7 LOOP
group: Y=3 FlowAgentRuntime

Industry capability: extensible plugin / extension architecture
                     (similar to VSCode extensions or LangChain integrations).
MRL extension: every plugin is required to declare its Y-group and X-layer
               coordinates so it integrates with the TXYZ FileIndexGovernance.

A *Plugin* is a Python module placed under a designated plugin directory that
exposes a ``PLUGIN_MANIFEST`` dict and an optional ``activate(registry)``
function.  The PluginManager discovers, loads, activates, and deactivates
plugins, and maintains a lifecycle log.

Plugin contract
---------------
Every plugin module must define at the top level:

    PLUGIN_MANIFEST = {
        "id":          "my_plugin",       # unique identifier
        "name":        "My Plugin",       # human-readable name
        "version":     "1.0",
        "description": "...",
        "layer":       "L7",              # TXYZ X coordinate
        "group":       3,                 # TXYZ Y coordinate
        "author":      "MrLiouWord",
    }

    def activate(registry):  # optional
        # register tools, templates, etc.
        pass

    def deactivate():  # optional
        pass

Usage (library)
---------------
    from plugin_manager import PluginManager

    mgr = PluginManager(plugin_dir="my_plugins/")
    mgr.discover()
    mgr.activate_all()

CLI
---
    python 09_workflow/plugin_manager.py discover --dir 09_workflow/plugins
    python 09_workflow/plugin_manager.py list
    python 09_workflow/plugin_manager.py activate --id my_plugin
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import pathlib
import sys
import time
import traceback
from typing import Any, Callable, Dict, List, Optional

ORIGIN_SIGNATURE = "MrLiouWord"

_REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
_DEFAULT_PLUGIN_DIR = _REPO_ROOT / "09_workflow" / "plugins"


# ─── PluginRecord ────────────────────────────────────────────────────────────

class PluginRecord:
    """Runtime state for a single discovered plugin."""

    def __init__(
        self,
        manifest: Dict[str, Any],
        path: pathlib.Path,
        module: Any,
    ) -> None:
        self.id: str = manifest["id"]
        self.manifest: Dict[str, Any] = manifest
        self.path = path
        self.module = module
        self.active: bool = False
        self.loaded_at_ms: int = int(time.time() * 1000)
        self.error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "manifest": self.manifest,
            "path": str(self.path),
            "active": self.active,
            "loaded_at_ms": self.loaded_at_ms,
            "error": self.error,
        }


# ─── PluginManager ───────────────────────────────────────────────────────────

class PluginManager:
    """
    Discovers, loads, activates, and deactivates plugins from a directory.
    """

    def __init__(
        self,
        plugin_dir: pathlib.Path = _DEFAULT_PLUGIN_DIR,
        registry: Any = None,
    ) -> None:
        self._dir = pathlib.Path(plugin_dir)
        self._registry = registry
        self._plugins: Dict[str, PluginRecord] = {}
        self._lifecycle_log: List[Dict[str, Any]] = []

    # ── Discovery ─────────────────────────────────────────────────────────────

    def discover(self) -> List[str]:
        """
        Scan plugin_dir for ``*.py`` files that expose ``PLUGIN_MANIFEST``.
        Returns the list of discovered plugin ids.
        """
        if not self._dir.exists():
            return []
        found: List[str] = []
        for py_file in sorted(self._dir.glob("*.py")):
            if py_file.name.startswith("_"):
                continue
            plugin_id = self._load_file(py_file)
            if plugin_id:
                found.append(plugin_id)
        return found

    def _load_file(self, path: pathlib.Path) -> Optional[str]:
        """Load a single plugin file. Returns plugin id on success, None on failure."""
        spec = importlib.util.spec_from_file_location(path.stem, path)
        if spec is None or spec.loader is None:
            return None
        mod = importlib.util.module_from_spec(spec)
        try:
            spec.loader.exec_module(mod)  # type: ignore[arg-type]
        except Exception as exc:  # noqa: BLE001
            self._log("load_error", None, str(exc))
            return None

        manifest = getattr(mod, "PLUGIN_MANIFEST", None)
        if not manifest or "id" not in manifest:
            return None  # Not a valid plugin

        plugin_id: str = manifest["id"]
        record = PluginRecord(manifest, path, mod)
        self._plugins[plugin_id] = record
        self._log("discovered", plugin_id)
        return plugin_id

    # ── Lifecycle ────────────────────────────────────────────────────────────

    def activate(self, plugin_id: str) -> bool:
        """Activate a plugin. Returns True on success."""
        record = self._plugins.get(plugin_id)
        if record is None:
            self._log("activate_error", plugin_id, "plugin not found")
            return False
        if record.active:
            return True  # already active

        activate_fn: Optional[Callable[..., Any]] = getattr(record.module, "activate", None)
        if activate_fn is not None:
            try:
                activate_fn(self._registry)
            except Exception as exc:  # noqa: BLE001
                record.error = traceback.format_exc()
                self._log("activate_error", plugin_id, str(exc))
                return False

        record.active = True
        self._log("activated", plugin_id)
        return True

    def deactivate(self, plugin_id: str) -> bool:
        """Deactivate a plugin. Returns True on success."""
        record = self._plugins.get(plugin_id)
        if record is None:
            return False
        if not record.active:
            return True

        deactivate_fn: Optional[Callable[[], None]] = getattr(record.module, "deactivate", None)
        if deactivate_fn is not None:
            try:
                deactivate_fn()
            except Exception as exc:  # noqa: BLE001
                record.error = traceback.format_exc()
                self._log("deactivate_error", plugin_id, str(exc))
                return False

        record.active = False
        self._log("deactivated", plugin_id)
        return True

    def activate_all(self) -> Dict[str, bool]:
        return {pid: self.activate(pid) for pid in self._plugins}

    def deactivate_all(self) -> Dict[str, bool]:
        return {pid: self.deactivate(pid) for pid in self._plugins}

    # ── Query ─────────────────────────────────────────────────────────────────

    def list_plugins(self) -> List[Dict[str, Any]]:
        return [r.to_dict() for r in self._plugins.values()]

    def get(self, plugin_id: str) -> Optional[PluginRecord]:
        return self._plugins.get(plugin_id)

    def lifecycle_log(self) -> List[Dict[str, Any]]:
        return list(self._lifecycle_log)

    # ── Internal ──────────────────────────────────────────────────────────────

    def _log(
        self,
        event: str,
        plugin_id: Optional[str],
        detail: str = "",
    ) -> None:
        self._lifecycle_log.append({
            "event": event,
            "plugin_id": plugin_id,
            "detail": detail,
            "ts_ms": int(time.time() * 1000),
            "origin_signature": ORIGIN_SIGNATURE,
        })


# ─── CLI ─────────────────────────────────────────────────────────────────────

def _cmd_discover(args: argparse.Namespace) -> None:
    plugin_dir = pathlib.Path(args.dir) if args.dir else _DEFAULT_PLUGIN_DIR
    mgr = PluginManager(plugin_dir)
    found = mgr.discover()
    print(f"Discovered {len(found)} plugin(s) in '{plugin_dir}':")
    for pid in found:
        r = mgr.get(pid)
        print(f"  {pid}  v{r.manifest.get('version','?')}  — {r.manifest.get('description','')}")


def _cmd_list(_args: argparse.Namespace) -> None:
    mgr = PluginManager()
    mgr.discover()
    plugins = mgr.list_plugins()
    print(f"{len(plugins)} plugin(s):")
    for p in plugins:
        status = "active" if p["active"] else "inactive"
        print(f"  [{status}]  {p['id']}  path={p['path']}")


def _cmd_activate(args: argparse.Namespace) -> None:
    mgr = PluginManager()
    mgr.discover()
    ok = mgr.activate(args.id)
    print(f"{'✅ Activated' if ok else '❌ Failed to activate'}  '{args.id}'")


def _build_argparser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="PluginManager — plugin lifecycle manager")
    sub = p.add_subparsers(dest="cmd", required=True)

    d = sub.add_parser("discover", help="Discover plugins in a directory")
    d.add_argument("--dir", default="", help="Plugin directory path")

    sub.add_parser("list", help="List discovered plugins")

    a = sub.add_parser("activate", help="Activate a plugin by id")
    a.add_argument("--id", required=True)

    return p


def main() -> None:
    parser = _build_argparser()
    args = parser.parse_args()
    dispatch = {
        "discover": _cmd_discover,
        "list":     _cmd_list,
        "activate": _cmd_activate,
    }
    dispatch[args.cmd](args)


if __name__ == "__main__":
    main()
