from __future__ import annotations
import datetime as dt, hashlib, json, threading, uuid
from pathlib import Path

class TraceChain:
    def __init__(self, log_dir: Path):
        self.log_dir = log_dir
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.path = self.log_dir / "trace.jsonl"
        self.state_path = self.log_dir / "trace_state.json"
        self.lock = threading.Lock()
        self.state = self._load()

    def _load(self) -> dict:
        if self.state_path.exists():
            return json.loads(self.state_path.read_text(encoding="utf-8"))
        return {"run_id": uuid.uuid4().hex, "tick": 0, "merkle_root": "0" * 64}

    def emit(self, event: str, payload: dict) -> dict:
        with self.lock:
            self.state["tick"] += 1
            rec = {"run_id": self.state["run_id"], "tick": self.state["tick"], "event": event,
                   "timestamp": dt.datetime.now(dt.timezone.utc).isoformat(), "payload": payload}
            leaf = hashlib.sha256(json.dumps(rec, sort_keys=True, ensure_ascii=False).encode()).hexdigest()
            root = hashlib.sha256((self.state["merkle_root"] + leaf).encode()).hexdigest()
            self.state["merkle_root"] = root
            rec["merkle_root"] = root
            with self.path.open("a", encoding="utf-8") as f:
                f.write(json.dumps(rec, ensure_ascii=False) + "\n")
            self.state_path.write_text(json.dumps(self.state, indent=2), encoding="utf-8")
            return rec
