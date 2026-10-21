# MRL_Registry
# origin_signature: MrLiouWord
# layer: MRL_DB
"""Registry：runtime 工件登錄（in-memory + 可選 json 落盤），依 content hash 去重。"""

from __future__ import annotations

import hashlib
import json
import pathlib
from typing import Any, Dict, List, Optional

ORIGIN_SIGNATURE = "MrLiouWord"


class MRL_Registry:
    def __init__(self, store_path: Optional[str] = None) -> None:
        self.store_path = pathlib.Path(store_path) if store_path else None
        self.entries: Dict[str, Dict[str, Any]] = {}
        if self.store_path and self.store_path.exists():
            self.entries = json.loads(self.store_path.read_text(encoding="utf-8"))

    def register(self, kind: str, payload: Any) -> str:
        blob = json.dumps(payload, ensure_ascii=False, sort_keys=True)
        h = hashlib.sha256(f"{kind}|{blob}".encode("utf-8")).hexdigest()
        self.entries[h] = {"kind": kind, "hash": h, "payload": payload}
        self._persist()
        return h

    def get(self, h: str) -> Optional[Dict[str, Any]]:
        return self.entries.get(h)

    def by_kind(self, kind: str) -> List[Dict[str, Any]]:
        return [e for e in self.entries.values() if e["kind"] == kind]

    def _persist(self) -> None:
        if self.store_path:
            self.store_path.parent.mkdir(parents=True, exist_ok=True)
            self.store_path.write_text(
                json.dumps(self.entries, ensure_ascii=False, indent=2), encoding="utf-8"
            )
