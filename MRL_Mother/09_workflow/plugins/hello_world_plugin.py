#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
hello_world_plugin.py — Example / Starter Plugin for MRL AI System
origin_signature: MrLiouWord

This file demonstrates the MRL plugin contract:
  1. Declare PLUGIN_MANIFEST at module level
  2. Implement activate(registry) to register tools/templates
  3. Implement deactivate() to clean up (optional)
"""

from __future__ import annotations

import time

PLUGIN_MANIFEST = {
    "id":          "hello_world",
    "name":        "Hello World Plugin",
    "version":     "1.0",
    "description": "Starter plugin — demonstrates the MRL plugin contract.",
    "layer":       "L7",
    "group":       3,
    "author":      "MrLiouWord",
}


def activate(registry: object) -> None:
    """Register a greeting tool into the ToolRegistry."""
    if registry is None:
        return

    # Only register if the registry has a .register method
    if not hasattr(registry, "register"):
        return

    @registry.register(
        name="greet",
        description="Return a personalised greeting from the MRL system.",
        parameters={"name": str},
    )
    def greet(name: str) -> str:
        ts = int(time.time())
        return f"[MrLiouWord / MRL AI System]  Hello, {name}! (ts={ts})"


def deactivate() -> None:
    """Remove the greeting tool (no-op in this minimal example)."""
    pass
