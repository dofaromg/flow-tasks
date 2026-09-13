#!/usr/bin/env python3
from __future__ import annotations

import argparse
import base64
import hashlib
import json
from pathlib import Path
from typing import Any

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
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


def load_trusted_keys(path: Path) -> dict[str, Ed25519PublicKey]:
    """Load the explicit Ed25519 node trust registry used for this validation."""
    registry = load(path)
    if not isinstance(registry, dict):
        fail("trusted-node registry must be an object")
    if registry.get("signature_scheme") != "ED25519":
        fail("trusted-node registry signature_scheme must be ED25519")
    keys = registry.get("keys")
    if not isinstance(keys, dict) or not keys:
        fail("trusted-node registry keys must be a non-empty object")
    trusted: dict[str, Ed25519PublicKey] = {}
    for node_id, encoded_key in keys.items():
        if not isinstance(node_id, str) or not node_id:
            fail("trusted-node registry contains an invalid node_id")
        try:
            raw_key = base64.b64decode(encoded_key, validate=True)
            trusted[node_id] = Ed25519PublicKey.from_public_bytes(raw_key)
        except (TypeError, ValueError) as exc:
            fail(f"invalid Ed25519 public key for {node_id}: {exc}")
    return trusted


def verify_signature(
    attestation: dict[str, Any], trusted_keys: dict[str, Ed25519PublicKey]
) -> bool:
    """Verify a node signature against an explicitly trusted Ed25519 public key."""
    if attestation["signature_scheme"] != "ED25519":
        return False
    public_key = trusted_keys.get(attestation["node_id"])
    if public_key is None:
        return False
    try:
        signature = base64.b64decode(attestation["signature"], validate=True)
        public_key.verify(signature, receipt_payload(attestation))
    except (InvalidSignature, TypeError, ValueError):
        return False
    return True


def validate(
    record: dict[str, Any], trusted_keys: dict[str, Ed25519PublicKey]
) -> dict[str, Any]:
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
        if not verify_signature(item, trusted_keys):
            fail(f"untrusted or invalid signature: {node}")
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
    parser.add_argument("trusted_node_keys", type=Path)
    args = parser.parse_args()
    trusted_keys = load_trusted_keys(args.trusted_node_keys)
    print(
        json.dumps(
            validate(load(args.record), trusted_keys),
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
