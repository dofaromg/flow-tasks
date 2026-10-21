from __future__ import annotations
import datetime as dt, hashlib, json, shutil
from pathlib import Path
from .trace import TraceChain

class ReversibleStore:
    def __init__(self, root: Path, trace: TraceChain):
        self.root, self.trace = root, trace
        self.snapshot_dir = root / "data" / "snapshots"
        self.snapshot_dir.mkdir(parents=True, exist_ok=True)

    def write_text(self, relative_path: str, text: str) -> dict:
        target = (self.root / relative_path).resolve()
        if self.root not in target.parents and target != self.root:
            raise ValueError("path escapes MRL root")
        target.parent.mkdir(parents=True, exist_ok=True)
        snapshot = None
        if target.exists():
            stamp = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
            snapshot = self.snapshot_dir / f"{stamp}_{target.name}"
            shutil.copy2(target, snapshot)
        target.write_text(text, encoding="utf-8")
        digest = hashlib.sha256(text.encode()).hexdigest()
        rec = self.trace.emit("vault_write", {"path": relative_path, "sha256": digest,
                                               "snapshot": str(snapshot) if snapshot else None})
        return {"path": relative_path, "sha256": digest, "snapshot": str(snapshot) if snapshot else None,
                "trace": rec["merkle_root"]}
