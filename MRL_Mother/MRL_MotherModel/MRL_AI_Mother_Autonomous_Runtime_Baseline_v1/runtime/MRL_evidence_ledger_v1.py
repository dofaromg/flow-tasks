#!/usr/bin/env python3
"""Evidence ledger for every autonomous mother-runtime transition."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .MRL_hash_chain_v1 import MRLHashChain


class MRLEvidenceLedger:
    """Append runtime results and gates without silently rewriting history."""

    def __init__(self, data_dir: Path) -> None:
        self.chain = MRLHashChain(data_dir / "MRL_evidence_events.jsonl", "MRL_EVIDENCE_LEDGER_V1")

    def record(
        self,
        *,
        event_type: str,
        state: str,
        subject_id: str,
        details: dict[str, Any],
    ) -> dict[str, Any]:
        if state not in {"PASS", "FAIL", "OPEN", "OBSERVED"}:
            raise ValueError("evidence state must be PASS, FAIL, OPEN or OBSERVED")
        return self.chain.append(
            {
                "event_type": event_type,
                "state": state,
                "subject_id": subject_id,
                "details": details,
            }
        )

    def verify(self) -> dict[str, Any]:
        return self.chain.verify()

