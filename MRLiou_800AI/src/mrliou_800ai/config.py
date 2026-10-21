from __future__ import annotations
import json, os
from pathlib import Path

ROOT = Path(os.environ.get("MRL_HOME", Path.cwd())).resolve()

def load_json(path: str | Path) -> dict:
    with Path(path).open("r", encoding="utf-8") as f:
        return json.load(f)

def project_path(*parts: str) -> Path:
    return ROOT.joinpath(*parts)
