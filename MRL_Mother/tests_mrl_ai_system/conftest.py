"""
conftest.py — pytest shared fixtures for MRL AI System tests
origin_signature: MrLiouWord
"""
from __future__ import annotations

import pathlib
import sys

# ── Add all source directories to sys.path so tests can import modules ────────

_REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent

for _sub in [
    _REPO_ROOT,
    _REPO_ROOT / "09_workflow",
    _REPO_ROOT / "03_memory" / "merkle",
    _REPO_ROOT / "03_memory" / "vector",
    _REPO_ROOT / "05_persona",
]:
    _p = str(_sub)
    if _p not in sys.path:
        sys.path.insert(0, _p)
