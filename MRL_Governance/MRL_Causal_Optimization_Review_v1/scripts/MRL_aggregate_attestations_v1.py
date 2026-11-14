#!/usr/bin/env python3
import json, sys
from collections import Counter
from pathlib import Path

VALID = {"CONFIRM","PARTIAL","DISSENT","UNRESOLVED"}


def load_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def main(argv):
    if len(argv) < 2:
        print("usage: MRL_aggregate_attestations_v1.py <attestation.json>...", file=sys.stderr)
        return 2
    records = [load_json(p) for p in argv[1:]]
    event_ids = {r.get("event_id") for r in records}
    hashes = {r.get("observed_record_hash") for r in records}
    if len(event_ids) != 1 or None in event_ids:
        raise SystemExit("attestations must reference exactly one event_id")
    if len(hashes) != 1 or None in hashes:
        raise SystemExit("attestations must reference exactly one observed_record_hash")
    node_ids = [r.get("node_id") for r in records]
    if None in node_ids or len(node_ids) != len(set(node_ids)):
        raise SystemExit("node_id values must be unique")
    decisions = [r.get("decision") for r in records]
    if any(d not in VALID for d in decisions):
        raise SystemExit("invalid decision")
    counts = Counter(decisions)
    if len(counts) == 1 and decisions[0] == "CONFIRM":
        state = "CONSENSUS"
    elif "DISSENT" in counts:
        state = "DISSENT_PRESERVED"
    elif "CONFIRM" in counts or "PARTIAL" in counts:
        state = "PARTIAL_CONSENSUS"
    else:
        state = "UNRESOLVED"
    out = {
        "event_id": records[0]["event_id"],
        "observed_record_hash": records[0]["observed_record_hash"],
        "node_count": len(records),
        "decision_counts": dict(sorted(counts.items())),
        "consensus_state": state,
        "rule": "consensus never overwrites origin, evidence, or dissent"
    }
    print(json.dumps(out, ensure_ascii=False, sort_keys=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
