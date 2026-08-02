#!/usr/bin/env python3
"""MRL RelayStation authority runtime.

External models provide candidate records only. This module validates provenance,
artifact hashes, scope coverage, and explicit MRL approval before promotion.
It uses only the Python standard library and does not call external providers.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

AUTHORITY_LEVELS = {"L0", "L1", "L2", "L3", "L4", "L5"}
EXTERNAL_PROVIDERS = {"chatgpt", "claude", "copilot", "gemini", "other"}


class AuthorityError(ValueError):
    """Raised when a candidate cannot pass the MRL authority gate."""


def canonical_json(data: Any) -> str:
    return json.dumps(data, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


@dataclass(frozen=True)
class GateResult:
    passed: bool
    errors: tuple[str, ...]
    record_hash: str


def validate_record(record: dict[str, Any], repository_root: Path) -> GateResult:
    errors: list[str] = []

    source = record.get("source") or {}
    provider = str(source.get("provider", "")).lower()
    if provider not in EXTERNAL_PROVIDERS:
        errors.append("source.provider is missing or unsupported")

    if record.get("authority_level") not in {"L0", "L1", "L2"}:
        errors.append("external candidate authority_level must be L0, L1, or L2")

    requested = set(record.get("requested_scope") or [])
    generated = set(record.get("generated_artifacts") or [])
    missing = sorted(requested - generated)
    if missing:
        errors.append(f"scope coverage incomplete; missing: {missing}")

    artifacts = record.get("artifacts") or []
    declared_paths: set[str] = set()
    for artifact in artifacts:
        rel_path = str(artifact.get("path", ""))
        expected_hash = str(artifact.get("sha256", ""))
        if not rel_path:
            errors.append("artifact path is empty")
            continue
        declared_paths.add(rel_path)
        absolute = (repository_root / rel_path).resolve()
        try:
            absolute.relative_to(repository_root.resolve())
        except ValueError:
            errors.append(f"artifact escapes repository root: {rel_path}")
            continue
        if not absolute.is_file():
            errors.append(f"artifact missing: {rel_path}")
            continue
        actual_hash = sha256_file(absolute)
        if expected_hash != actual_hash:
            errors.append(f"sha256 mismatch: {rel_path}")

    undeclared = sorted(generated - declared_paths)
    if undeclared:
        errors.append(f"generated artifacts lack evidence entries: {undeclared}")

    verification = record.get("verification") or {}
    if verification.get("status") != "passed":
        errors.append("verification.status must be passed")

    record_hash = sha256_text(canonical_json(record))
    return GateResult(not errors, tuple(errors), record_hash)


def promote_record(
    record: dict[str, Any],
    repository_root: Path,
    approver: str,
    target_level: str,
) -> dict[str, Any]:
    if target_level not in {"L3", "L4", "L5"}:
        raise AuthorityError("target_level must be L3, L4, or L5")
    if not approver.strip():
        raise AuthorityError("MRL approver identity is required")

    result = validate_record(record, repository_root)
    if not result.passed:
        raise AuthorityError("; ".join(result.errors))

    promoted = dict(record)
    promoted["authority_level"] = target_level
    promoted["canonical_status"] = "adopted" if target_level == "L3" else "released"
    promoted["promotion"] = {
        "authority": "MRL",
        "approver": approver,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "source_record_sha256": result.record_hash,
    }
    promoted["record_sha256"] = sha256_text(canonical_json(promoted))
    return promoted


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate and promote an MRL relay record")
    parser.add_argument("record", type=Path)
    parser.add_argument("--repo-root", type=Path, default=Path.cwd())
    parser.add_argument("--approver")
    parser.add_argument("--target-level", default="L3")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()

    record = json.loads(args.record.read_text(encoding="utf-8"))
    if args.approver:
        output = promote_record(record, args.repo_root, args.approver, args.target_level)
    else:
        result = validate_record(record, args.repo_root)
        output = {
            "passed": result.passed,
            "errors": list(result.errors),
            "record_sha256": result.record_hash,
        }

    text = json.dumps(output, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text, encoding="utf-8")
    else:
        print(text, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
