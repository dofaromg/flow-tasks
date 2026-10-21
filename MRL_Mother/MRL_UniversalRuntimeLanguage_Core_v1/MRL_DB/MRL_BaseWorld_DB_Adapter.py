# MRL_BaseWorld_DB_Adapter
# origin_signature: MrLiouWord
# layer: MRL_DB
"""MRL_BaseWorld_DB_v1 接線 Adapter（不重建另一套 schema）。

誠實邊界：本檔不重建 MRL_BaseWorld_DB 的正式 27 tables / 8 indexes。它提供：
  1. ATTACHMENT_POINTS — 命令 §5 指定的 7 個邏輯掛接點。
  2. connect(dsn) — 連線正式 DB（產線）。dsn 形如 postgres://... 或 sqlite:///path。
  3. local_emulation() — 以本地 sqlite 建立「7 個邏輯掛接點」的最小鏡像，
     供離線開發/測試；正式運轉必須 connect 至真正的 MRL_BaseWorld_DB_v1。

⚠ 產線部署前，請以 DL580 上的真實連線字串覆寫，並對齊正式 27-table schema。
"""

from __future__ import annotations

import sqlite3
from typing import Any, Dict, List, Optional

ORIGIN_SIGNATURE = "MrLiouWord"

# §5 指定之邏輯掛接點（不等同正式 27 tables；為 runtime 對接介面）
ATTACHMENT_POINTS = [
    "Canon",
    "Registry",
    "FLTNZ_Asset",
    "Memory_Sphere",
    "Proof",
    "Trace",
    "Mirror",
]

# 正式 schema 規模（來自命令 §5；由真實 MRL_BaseWorld_DB_v1 提供，非本檔重建）
PROD_SCHEMA = {"tables": 27, "indexes": 8, "rebuild_forbidden": True}


class MRL_BaseWorld_DB_Adapter:
    def __init__(self, dsn: Optional[str] = None) -> None:
        self.dsn = dsn
        self._conn: Optional[sqlite3.Connection] = None
        self.mode = "unbound"

    def connect(self, dsn: Optional[str] = None) -> "MRL_BaseWorld_DB_Adapter":
        """連線正式 MRL_BaseWorld_DB_v1（產線）。

        本核心不內建各家 DB driver；產線請注入連線。未提供 dsn 時退回本地鏡像。
        """
        self.dsn = dsn or self.dsn
        if not self.dsn:
            return self.local_emulation()
        if self.dsn.startswith("sqlite:///"):
            self._conn = sqlite3.connect(self.dsn[len("sqlite:///"):])
            self.mode = "sqlite_prod"
            return self
        # postgres/mysql 等：交由產線注入（此核心不捆綁 driver）
        raise NotImplementedError(
            f"非 sqlite dsn 需由 DL580 產線注入對應 driver 並對齊 27-table schema: {self.dsn!r}"
        )

    def local_emulation(self) -> "MRL_BaseWorld_DB_Adapter":
        """本地 sqlite 最小鏡像：僅建 7 個邏輯掛接點，供離線測試。"""
        self._conn = sqlite3.connect(":memory:")
        cur = self._conn.cursor()
        for ap in ATTACHMENT_POINTS:
            cur.execute(
                f'CREATE TABLE IF NOT EXISTS "{ap}" '
                "(hash TEXT PRIMARY KEY, kind TEXT, payload TEXT, ts_ms INTEGER)"
            )
        self._conn.commit()
        self.mode = "local_emulation"
        return self

    def attach(self, point: str, hash_: str, kind: str, payload: str, ts_ms: int) -> None:
        if point not in ATTACHMENT_POINTS:
            raise ValueError(f"unknown attachment point: {point!r}")
        assert self._conn is not None, "call connect()/local_emulation() first"
        self._conn.execute(
            f'INSERT OR REPLACE INTO "{point}" (hash, kind, payload, ts_ms) VALUES (?,?,?,?)',
            (hash_, kind, payload, ts_ms),
        )
        self._conn.commit()

    def count(self, point: str) -> int:
        assert self._conn is not None
        return self._conn.execute(f'SELECT COUNT(*) FROM "{point}"').fetchone()[0]

    def status(self) -> Dict[str, Any]:
        return {
            "origin_signature": ORIGIN_SIGNATURE,
            "mode": self.mode,
            "dsn": self.dsn,
            "attachment_points": ATTACHMENT_POINTS,
            "prod_schema": PROD_SCHEMA,
        }
