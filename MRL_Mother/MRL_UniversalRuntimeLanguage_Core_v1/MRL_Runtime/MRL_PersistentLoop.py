# MRL_PersistentLoop
# origin_signature: MrLiouWord
# layer: MRL_Runtime
"""永續循環：checkpoint 落盤、crash restore、背景編排。

「survive restart」以可驗證方式實作：每步將進度寫入磁碟 checkpoint；
新建一個 loop 實例（模擬 process 重啟）能由磁碟 checkpoint 接續而不丟失進度。
"""

from __future__ import annotations

import json
import pathlib
import time
from typing import Any, Dict, Optional

ORIGIN_SIGNATURE = "MrLiouWord"


class MRL_PersistentLoop:
    def __init__(self, runtime_dir: str, loop_id: str = "default") -> None:
        self.dir = pathlib.Path(runtime_dir)
        self.dir.mkdir(parents=True, exist_ok=True)
        self.loop_id = loop_id
        self.checkpoint_path = self.dir / f"persistent_loop_{loop_id}.json"
        self.state = self._load() or {
            "loop_id": loop_id,
            "iteration": 0,
            "history": [],
            "origin_signature": ORIGIN_SIGNATURE,
        }

    def _load(self) -> Optional[Dict[str, Any]]:
        if self.checkpoint_path.exists():
            return json.loads(self.checkpoint_path.read_text(encoding="utf-8"))
        return None

    def _persist(self) -> None:
        self.checkpoint_path.write_text(
            json.dumps(self.state, ensure_ascii=False, indent=2), encoding="utf-8"
        )

    def step(self, payload: Any = None) -> Dict[str, Any]:
        self.state["iteration"] += 1
        self.state["history"].append({
            "iteration": self.state["iteration"],
            "ts_ms": int(time.time() * 1000),
            "payload": payload,
        })
        self._persist()  # 每步落盤 → crash 後可由此接續
        return self.state

    def run(self, iterations: int, payload_fn=None) -> Dict[str, Any]:
        for _ in range(iterations):
            self.step(payload_fn() if payload_fn else None)
        return self.state

    @property
    def iteration(self) -> int:
        return self.state["iteration"]

    def survives_restart(self) -> bool:
        """以新實例自磁碟接續，確認進度未丟失。"""
        reborn = MRL_PersistentLoop(str(self.dir), self.loop_id)
        return reborn.iteration == self.iteration
