#!/usr/bin/env python3
"""Verify an MRL live-model acceptance receipt without inventing live evidence."""

from __future__ import annotations

import argparse
import json
import re
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse

HEX40 = re.compile(r"^[0-9a-f]{40}$")
HEX64 = re.compile(r"^[0-9a-f]{64}$")
MRL_ID = re.compile(r"^MRL_[A-Za-z0-9_.:-]+$")
EXPECTED_FIELDS = {
    "schema", "canonical_id", "origin_signature", "git_head", "hardware_id",
    "runtime_id", "backend", "model", "model_endpoint", "model_release_id",
    "model_release_manifest_sha256", "model_artifact_sha256",
    "model_artifact_size_bytes", "model_sha256_verified", "health_ready", "memory_chain_head",
    "evidence_chain_head", "passport_hash", "return_anchor", "evidence_ref",
    "request_sha256", "result_sha256", "external_model_disconnected",
    "accepted_at", "operator_id", "acceptance_gate",
}


def validate(receipt: object) -> list[str]:
    if not isinstance(receipt, dict):
        return ["root_not_object"]
    failures: list[str] = []
    for field in sorted(EXPECTED_FIELDS - set(receipt)):
        failures.append(f"missing.{field}")
    for field in sorted(set(receipt) - EXPECTED_FIELDS):
        failures.append(f"extra.{field}")
    constants = {
        "schema": "MRL_AI_Mother_Live_Acceptance_v1",
        "canonical_id": "MRL_AI_Mother_Autonomous_Runtime_Baseline_v1",
        "origin_signature": "MrLiouWord",
        "model_sha256_verified": True,
        "health_ready": True,
        "external_model_disconnected": True,
        "acceptance_gate": "MRL_AI_MOTHER_AUTONOMOUS_RUNTIME_ACCEPTANCE_PASS",
    }
    for field, value in constants.items():
        if receipt.get(field) != value:
            failures.append(field)
    if not HEX40.fullmatch(str(receipt.get("git_head", ""))):
        failures.append("git_head")
    for field in ("hardware_id", "operator_id", "model_release_id"):
        if not MRL_ID.fullmatch(str(receipt.get(field, ""))):
            failures.append(field)
    for field in (
        "model_artifact_sha256",
        "model_release_manifest_sha256",
        "memory_chain_head",
        "evidence_chain_head",
        "passport_hash",
        "return_anchor",
        "evidence_ref",
        "request_sha256",
        "result_sha256",
    ):
        if not HEX64.fullmatch(str(receipt.get(field, ""))):
            failures.append(field)
    if receipt.get("backend") not in {"ollama", "llama.cpp"}:
        failures.append("backend")
    if not isinstance(receipt.get("model_artifact_size_bytes"), int) or receipt["model_artifact_size_bytes"] < 1:
        failures.append("model_artifact_size_bytes")
    endpoint = urlparse(str(receipt.get("model_endpoint", "")))
    if endpoint.scheme not in {"http", "https"} or endpoint.hostname not in {
        "127.0.0.1", "localhost", "::1"
    }:
        failures.append("model_endpoint")
    for field in ("runtime_id", "model"):
        if not isinstance(receipt.get(field), str) or not receipt[field].strip():
            failures.append(field)
    try:
        timestamp = str(receipt.get("accepted_at", "")).replace("Z", "+00:00")
        parsed = datetime.fromisoformat(timestamp)
        if parsed.tzinfo is None:
            raise ValueError
    except ValueError:
        failures.append("accepted_at")
    return sorted(set(failures))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("receipt", type=Path)
    args = parser.parse_args()
    receipt = json.loads(args.receipt.read_text(encoding="utf-8"))
    failures = validate(receipt)
    report = {
        "receipt": str(args.receipt),
        "failures": failures,
        "acceptance_receipt_gate": "PASS" if not failures else "FAIL",
    }
    print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
