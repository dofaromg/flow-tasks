from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Dict, List

import requests


class NotionAdapter:
    def __init__(self, data_dir: Path, token: str | None = None) -> None:
        self.data_dir = data_dir
        self.token = token or os.environ.get("NOTION_TOKEN")

    def _require_token(self) -> str:
        if not self.token:
            raise RuntimeError("NOTION_TOKEN is required for Notion sync")
        return self.token

    def sync_entries(self, entries: List[Dict[str, Any]], config: Dict[str, Any]) -> Path:
        """
        A lightweight sync that stores the payload locally while also
        attempting a minimal Notion API call if credentials are present.
        """
        token = self._require_token()
        export_path = self.data_dir / "notion_export.json"
        payload = {"config": config, "entries": entries}
        export_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False))

        # Best-effort ping to Notion API so users can verify connectivity.
        notion_version = "2022-06-28"
        headers = {"Authorization": f"Bearer {token}", "Notion-Version": notion_version}
        try:
            response = requests.get("https://api.notion.com/v1/users", headers=headers, timeout=5)
            response.raise_for_status()
        except Exception as exc:  # pragma: no cover - best effort only
            # We still keep the local export so users can inspect the payload.
            raise RuntimeError(f"Failed to contact Notion API: {exc}")

        return export_path
