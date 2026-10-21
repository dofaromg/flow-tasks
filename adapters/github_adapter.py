from __future__ import annotations

from pathlib import Path
from typing import Dict, List


class GitHubAdapter:
    """Placeholder adapter that mirrors the ledger data into a local file.

    The adapter is intentionally lightweight to keep the demo self-contained.
    In production this would publish content to a GitHub repo via the API.
    """

    def __init__(self, data_dir: Path) -> None:
        self.data_dir = data_dir

    def export(self, entries: List[Dict[str, str]]) -> Path:
        target = self.data_dir / "github_export.json"
        import json

        target.write_text(json.dumps(entries, indent=2, ensure_ascii=False))
        return target
