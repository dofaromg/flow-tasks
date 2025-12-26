from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List, Optional, Any


class Storage:
    def __init__(self, data_dir: Path) -> None:
        self.data_dir = data_dir
        self.snapshots_dir = self.data_dir / "snapshots"
        self.chain_file = self.data_dir / "chain.jsonl"
        self.dag_edges_file = self.data_dir / "dag_edges.jsonl"
        self.refs_file = self.data_dir / "refs.json"

    def ensure_structure(self) -> None:
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.snapshots_dir.mkdir(parents=True, exist_ok=True)
        if not self.chain_file.exists():
            self.chain_file.write_text("")
        if not self.dag_edges_file.exists():
            self.dag_edges_file.write_text("")
        if not self.refs_file.exists():
            self.save_refs({"head": None, "length": 0})

    def load_chain_entries(self) -> List[Dict[str, Any]]:
        entries: List[Dict[str, Any]] = []
        if not self.chain_file.exists():
            return entries
        with self.chain_file.open() as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                entries.append(json.loads(line))
        return entries

    def append_chain_entry(self, entry: Dict[str, Any]) -> None:
        with self.chain_file.open("a") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")

    def load_refs(self) -> Dict[str, Any]:
        if not self.refs_file.exists():
            return {"head": None, "length": 0}
        return json.loads(self.refs_file.read_text())

    def save_refs(self, refs: Dict[str, Any]) -> None:
        self.refs_file.write_text(json.dumps(refs, indent=2, ensure_ascii=False))

    def append_dag_edge(self, edge: Dict[str, Optional[str]]) -> None:
        with self.dag_edges_file.open("a") as f:
            f.write(json.dumps(edge, ensure_ascii=False) + "\n")

    def write_snapshot(self, name: str, data: Dict[str, Any]) -> Path:
        snapshot_path = self.snapshots_dir / f"{name}.json"
        snapshot_path.write_text(json.dumps(data, indent=2, ensure_ascii=False))
        return snapshot_path

    def tail_chain(self, n: int) -> List[Dict[str, Any]]:
        entries = self.load_chain_entries()
        if n <= 0:
            return entries
        return entries[-n:]

    def reset(self) -> None:
        """Remove all ledger data. Useful for clean init."""
        if self.data_dir.exists():
            for path in [self.chain_file, self.dag_edges_file, self.refs_file]:
                if path.exists():
                    path.unlink()
            if self.snapshots_dir.exists():
                for child in self.snapshots_dir.glob("*.json"):
                    child.unlink()
