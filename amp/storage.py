from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List, Optional, Any, Iterator


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

    def iter_chain_entries(self) -> Iterator[Dict[str, Any]]:
        """
        Iterator for chain entries - memory efficient for large files.
        Use this for processing large chain files without loading everything into memory.
        
        Yields:
            Individual chain entries as dictionaries
        """
        if not self.chain_file.exists():
            return
        with self.chain_file.open() as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    yield json.loads(line)
                except json.JSONDecodeError:
                    # Skip malformed lines
                    continue

    def load_chain_entries(self) -> List[Dict[str, Any]]:
        """
        Load all chain entries into memory.
        For large files, consider using iter_chain_entries() instead.
        
        Returns:
            List of all chain entries
        """
        return list(self.iter_chain_entries())

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
        """
        Get the last n entries from the chain efficiently.
        
        Args:
            n: Number of entries to retrieve from the end
            
        Returns:
            List of the last n entries (or all if fewer than n exist)
        """
        if n <= 0:
            return self.load_chain_entries()
        
        # For small n, read from the end of the file more efficiently
        if not self.chain_file.exists():
            return []
        
        # Read only last n lines instead of entire file
        entries: List[Dict[str, Any]] = []
        with self.chain_file.open('rb') as f:
            # Seek to end
            f.seek(0, 2)  # Move to end of file
            file_size = f.tell()
            
            # If file is small, just read all
            if file_size < 10000:  # Less than 10KB
                f.seek(0)
                for line in f:
                    line_str = line.decode('utf-8').strip()
                    if line_str:
                        entries.append(json.loads(line_str))
                return entries[-n:] if len(entries) > n else entries
            
            # For larger files, read backwards to find last n lines
            # Start with a reasonable buffer size
            buffer_size = min(8192, file_size)
            f.seek(max(0, file_size - buffer_size))
            
            # Read and process lines
            lines = []
            remaining_bytes = f.read().decode('utf-8', errors='ignore')
            lines = [l for l in remaining_bytes.split('\n') if l.strip()]
            
            # If we don't have enough lines, read more
            while len(lines) < n and buffer_size < file_size:
                buffer_size = min(buffer_size * 2, file_size)
                f.seek(max(0, file_size - buffer_size))
                remaining_bytes = f.read().decode('utf-8', errors='ignore')
                lines = [l for l in remaining_bytes.split('\n') if l.strip()]
            
            # Parse the last n lines
            for line in lines[-n:]:
                try:
                    entries.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
        
        return entries

    def reset(self) -> None:
        """Remove all ledger data. Useful for clean init."""
        if self.data_dir.exists():
            for path in [self.chain_file, self.dag_edges_file, self.refs_file]:
                if path.exists():
                    path.unlink()
            if self.snapshots_dir.exists():
                for child in self.snapshots_dir.glob("*.json"):
                    child.unlink()
