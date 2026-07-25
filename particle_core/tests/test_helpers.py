#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Shared test utilities for particle_core/tests.
Provides helpers that load modules directly from file paths to avoid
sys.modules cache collisions between particle_core/src/memory/ (new API)
and particle_core/src/ (older API) when running the full test suite.
"""

import sys
import importlib.util
from contextlib import contextmanager
from pathlib import Path

_MEM_DIR = Path(__file__).parent.parent / "src" / "memory"


def load_from_file(logical_name: str, filename: str, base_dir: Path = _MEM_DIR):
    """Load a module directly from a file path, bypassing sys.modules cache."""
    spec = importlib.util.spec_from_file_location(logical_name, str(base_dir / filename))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@contextmanager
def register_modules(**name_to_module):
    """
    Temporarily register modules in sys.modules under the given names.
    Restores the previous values (or removes) when the context exits.

    Usage::

        with register_modules(memory_cache_disk=_mcd, memory_quick_mount=_mqm):
            _pwb = load_from_file("_pwb_v2", "particle_wire_bridge.py")
    """
    previous = {name: sys.modules.get(name) for name in name_to_module}
    sys.modules.update(name_to_module)
    try:
        yield
    finally:
        for name, prev in previous.items():
            if prev is not None:
                sys.modules[name] = prev
            else:
                sys.modules.pop(name, None)
