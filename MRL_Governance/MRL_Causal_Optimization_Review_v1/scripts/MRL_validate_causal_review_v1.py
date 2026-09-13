#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator, FormatChecker
from jsonschema.exceptions import SchemaError

VALID = {"FACT", "INFERENCE", "UNRESOLVED", "CORRECTED"}
CONSENSUS = {"CONSENSUS", "PARTIAL_CONSENSUS", "DISSENT_PRESERVED", "UNRESOLVED"}
SCHEMA_PATH = (
    Path(__file__).resolve().parents[1]
    / "schema"
    / "MRL_Causal_Review_Record_v1.schema.json"
)


def fail(msg: str) -> None:
    """Stop validation with a stable MRL failure prefix."""
    raise SystemExit(f"MRL_CAUSAL_REVIEW_FAIL: {msg}")


def load(path: Path) -> Any:
    """Load a UTF-8 JSON document or fail closed."""
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        fail(f"invalid json: {exc}")


def schema_path(error: Any) -> str:
    """Render a deterministic JSON path for a schema validation error."""
    return "$" + "".join(
        f"[{part}]" if isinstance(part, int) else f".{part}" for part in error.path
    )


def enforce_schema(record: Any) -> None:
    """Enforce every constraint in the published Draft 2020-12 schema."""
    schema = load(SCHEMA_PATH)
    try:
        Draft202012Validator.check_schema(schema)
    except SchemaError as exc:
        fail(f"invalid published schema: {exc.message}")
    validator = Draft202012Validator(schema, format_checker=FormatChecker())
    errors = sorted(validator.iter_errors(record), key=lambda error: list(error.path))
    if errors:
        error = errors[0]
        fail(f"schema violation at {schema_path(error)}: {error.message}")


def receipt_payload(attestation: dict[str, Any]) -> bytes:
    """Canonicalize all attestation fields except the detached receipt."""
    unsigned = {key: value for key, value in attestation.items() if key != "signature"}
    return json.dumps(
        unsigned,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def verify_signature(attestation: dict[str, Any]) -> bool:
    """Verify the v1 deterministic SHA-256 integrity receipt."""
    if attestation["signature_scheme"] != "SHA256_RECEIPT_V1":
        return False
    expected = "sha256:" + hashlib.sha256(receipt_payload(attestation)).hexdigest()
    return attestation["signature"] == expected


def validate(record: dict[str, Any]) -> dict[str, Any]:
    """Validate a causal record and compute consensus from verified votes only."""
    enforce_schema(record)
    if record["status"] == "CORRECTED" and not record.get("correction"):
        fail("CORRECTED requires correction")
    if record["status"] == "INFERENCE" and not record.get("divergence"):
        fail("INFERENCE requires explicit reasoning/divergence context")

    decisions: list[str] = []
    seen: set[str] = set()
    for item in record["node_attestations"]:
        node = item["node_id"]
        if node in seen:
            fail(f"duplicated node_id: {node}")
        seen.add(node)
        if not verify_signature(item):
            fail(f"invalid signature receipt: {node}")
        decisions.append(item["decision"])

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
    canonical = json.dumps(
        record,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return {
        "status": "PASS",
        "event_id": record["event_id"],
        "review_status": record["status"],
        "computed_consensus": computed,
        "node_count": len(record["node_attestations"]),
        "record_sha256": hashlib.sha256(canonical).hexdigest(),
    }


def main() -> None:
    """Validate the record supplied on the command line."""
    parser = argparse.ArgumentParser()
    parser.add_argument("record", type=Path)
    args = parser.parse_args()
    print(json.dumps(validate(load(args.record)), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
