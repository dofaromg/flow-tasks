#!/usr/bin/env python3
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path

VALID = {"FACT", "INFERENCE", "UNRESOLVED", "CORRECTED"}
CONSENSUS = {"CONSENSUS", "PARTIAL_CONSENSUS", "DISSENT_PRESERVED", "UNRESOLVED"}


def fail(msg: str) -> None:
    raise SystemExit(f"MRL_CAUSAL_REVIEW_FAIL: {msg}")


def load(path: Path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as e:
        fail(f"invalid json: {e}")


def validate(record: dict) -> dict:
    required = ["event_id", "origin_signature", "original_request", "actual_action", "evidence_references", "causal_order", "status", "node_attestations"]
    for key in required:
        if key not in record:
            fail(f"missing {key}")
    if record["origin_signature"] != "MrLiouWord":
        fail("origin_signature mismatch")
    if record["status"] not in VALID:
        fail("invalid status")
    if not isinstance(record["evidence_references"], list) or not record["evidence_references"]:
        fail("evidence_references must be non-empty")
    if not isinstance(record["causal_order"], list) or len(record["causal_order"]) < 2:
        fail("causal_order must contain at least 2 ordered events")
    if record["status"] == "CORRECTED" and not record.get("correction"):
        fail("CORRECTED requires correction")
    if record["status"] == "INFERENCE" and not record.get("divergence"):
        fail("INFERENCE requires explicit reasoning/divergence context")
    attestations = record["node_attestations"]
    if not isinstance(attestations, list) or not attestations:
        fail("node_attestations must be non-empty")
    decisions = []
    seen = set()
    for item in attestations:
        node = item.get("node_id")
        if not node or node in seen:
            fail("node_id missing or duplicated")
        seen.add(node)
        decision = item.get("decision")
        if decision not in VALID:
            fail(f"invalid node decision: {node}")
        digest = item.get("evidence_hash", "")
        if len(digest) != 64 or any(c not in "0123456789abcdef" for c in digest):
            fail(f"invalid evidence hash: {node}")
        if not item.get("signed_at"):
            fail(f"missing signed_at: {node}")
        decisions.append(decision)
    if len(set(decisions)) == 1:
        computed = "CONSENSUS"
    elif record["status"] == "UNRESOLVED":
        computed = "UNRESOLVED"
    else:
        computed = "DISSENT_PRESERVED"
    declared = record.get("consensus_state")
    if declared and declared not in CONSENSUS:
        fail("invalid consensus_state")
    if declared and declared == "CONSENSUS" and computed != "CONSENSUS":
        fail("declared CONSENSUS conflicts with node decisions")
    canonical = json.dumps(record, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()
    return {
        "status": "PASS",
        "event_id": record["event_id"],
        "review_status": record["status"],
        "computed_consensus": computed,
        "node_count": len(attestations),
        "record_sha256": hashlib.sha256(canonical).hexdigest(),
    }


def main():
    p = argparse.ArgumentParser()
    p.add_argument("record", type=Path)
    args = p.parse_args()
    print(json.dumps(validate(load(args.record)), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
