#!/usr/bin/env python3
"""Create and verify immutable MRL before/forward/return receipts.

This module records plans and evidence. It never executes deployment commands,
changes a driver, restarts a service, or mutates a DL580 host.

origin_signature: MrLiouWord
canonical_authority: Mr.liou
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
from pathlib import Path

ORIGIN = "MrLiouWord"
SCHEMA = "MRL_Reversible_Change_Receipt_v1"
DIGEST = re.compile(r"sha256:[0-9a-f]{64}\Z")
CHANGE_ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{7,127}\Z")
PHASES = ("before", "forward", "return")


class ReceiptError(ValueError):
    """The reversible change chain is incomplete, mutable, or inconsistent."""


def canonical_digest(value: object) -> str:
    payload = json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")
    return "sha256:" + hashlib.sha256(payload).hexdigest()


def _safe_artifact(root: Path, relative: str) -> Path:
    path = Path(relative)
    if not relative or path.is_absolute() or ".." in path.parts:
        raise ReceiptError("artifact path must be a root-relative immutable copy")
    root = root.resolve()
    resolved = (root / path).resolve()
    if resolved != root and root not in resolved.parents:
        raise ReceiptError("artifact escapes evidence root")
    return resolved


def _artifact_row(root: Path, relative: str) -> dict:
    original = root / relative
    current = Path(root)
    for part in Path(relative).parts:
        current = current / part
        if current.is_symlink():
            raise ReceiptError('rollback evidence may not contain symlinks')
    path = _safe_artifact(root, relative)
    if not path.is_file() or path.stat().st_size <= 0:
        raise ReceiptError("artifact missing or empty: " + relative)
    if __package__:
        from .MRL_hardware_admission_v1 import _file_digest
    else:
        from MRL_hardware_admission_v1 import _file_digest
    try:
        actual_digest, size = _file_digest(original)
    except (OSError, ValueError) as exc:
        raise ReceiptError(str(exc)) from exc
    return {"path": relative, "size": size, "sha256": actual_digest}


def _validate_commands(phase: str, commands: list[dict]) -> None:
    if not isinstance(commands, list):
        raise ReceiptError("commands must be a list")
    if phase in ("forward", "return") and not commands:
        raise ReceiptError(phase + " requires an explicit argv plan")
    for item in commands:
        if not isinstance(item, dict):
            raise ReceiptError("command entry must be an object")
        argv = item.get("argv")
        exits = item.get("expected_exit_codes")
        if not isinstance(argv, list) or not argv or not all(isinstance(part, str) and part for part in argv):
            raise ReceiptError("command must use a non-empty argv array")
        if not isinstance(exits, list) or not exits or not all(type(code) is int for code in exits):
            raise ReceiptError("expected_exit_codes must be explicit integers")
        if phase in ("forward", "return") and item.get("requires_owner_go") is not True:
            raise ReceiptError("forward/return command is missing owner Go gate")


def build_receipt(
    *,
    evidence_root: Path,
    change_id: str,
    phase: str,
    state: dict,
    artifacts: list[str],
    commands: list[dict],
    status: str,
    previous_receipt_digest: str | None = None,
) -> dict:
    """Build a content-bound receipt from immutable local evidence copies."""
    if not isinstance(change_id, str) or not CHANGE_ID.fullmatch(change_id):
        raise ReceiptError("invalid change_id")
    if phase not in PHASES:
        raise ReceiptError("phase must be before, forward, or return")
    if not isinstance(state, dict) or not state:
        raise ReceiptError("state must be a non-empty object")
    if status not in ("captured", "prepared", "passed", "failed"):
        raise ReceiptError("invalid receipt status")
    if phase == "before" and previous_receipt_digest is not None:
        raise ReceiptError("before receipt cannot have a previous receipt")
    if phase != "before" and (not isinstance(previous_receipt_digest, str)
                               or not DIGEST.fullmatch(previous_receipt_digest)):
        raise ReceiptError(phase + " receipt must bind the previous receipt")
    if (not isinstance(artifacts, list) or not artifacts
            or any(not isinstance(item, str) for item in artifacts)
            or len(set(artifacts)) != len(artifacts)):
        raise ReceiptError("receipt requires at least one immutable artifact")
    _validate_commands(phase, commands)
    receipt = {
        "schema": SCHEMA,
        "origin_signature": ORIGIN,
        "change_id": change_id,
        "phase": phase,
        "status": status,
        "state_digest": canonical_digest(state),
        "state": state,
        "artifacts": [_artifact_row(evidence_root, item) for item in artifacts],
        "commands": commands,
        "previous_receipt_digest": previous_receipt_digest,
    }
    receipt["receipt_digest"] = canonical_digest(receipt)
    return receipt


def verify_receipt(receipt: dict, evidence_root: Path) -> None:
    if not isinstance(receipt, dict):
        raise ReceiptError("receipt must be an object")
    expected = receipt.get("receipt_digest")
    unsigned = {key: value for key, value in receipt.items() if key != "receipt_digest"}
    if not isinstance(expected, str) or expected != canonical_digest(unsigned):
        raise ReceiptError("receipt digest mismatch")
    if receipt.get("schema") != SCHEMA or receipt.get("origin_signature") != ORIGIN:
        raise ReceiptError("receipt identity mismatch")
    if (receipt.get('phase') not in PHASES
            or receipt.get('status') not in ('captured', 'prepared', 'passed', 'failed')
            or not isinstance(receipt.get('change_id'), str)
            or not CHANGE_ID.fullmatch(receipt['change_id'])):
        raise ReceiptError('invalid receipt phase, status, or change_id')
    if receipt['phase'] == 'before' and receipt.get('previous_receipt_digest') is not None:
        raise ReceiptError('before must not bind a prior receipt')
    if canonical_digest(receipt.get("state")) != receipt.get("state_digest"):
        raise ReceiptError("state digest mismatch")
    _validate_commands(receipt.get("phase"), receipt.get("commands"))
    rows = receipt.get("artifacts")
    if not isinstance(rows, list) or not rows:
        raise ReceiptError("artifact evidence missing")
    for row in rows:
        if not isinstance(row, dict) or set(row) != {"path", "size", "sha256"}:
            raise ReceiptError("invalid artifact row")
        actual = _artifact_row(evidence_root, row["path"])
        if actual != row:
            raise ReceiptError("artifact changed after receipt: " + row["path"])


def verify_roundtrip(before: dict, forward: dict, returned: dict, evidence_root: Path) -> dict:
    """Require an exact before -> forward -> return chain and restored state."""
    for receipt in (before, forward, returned):
        verify_receipt(receipt, evidence_root)
    if [before["phase"], forward["phase"], returned["phase"]] != list(PHASES):
        raise ReceiptError("receipt phases are out of order")
    if len({before["change_id"], forward["change_id"], returned["change_id"]}) != 1:
        raise ReceiptError("change_id mismatch")
    if forward["previous_receipt_digest"] != before["receipt_digest"]:
        raise ReceiptError("forward is not linked to before")
    if returned["previous_receipt_digest"] != forward["receipt_digest"]:
        raise ReceiptError("return is not linked to forward")
    if before["status"] not in ("captured", "passed") or forward["status"] != "passed" or returned["status"] != "passed":
        raise ReceiptError("roundtrip contains a non-passing phase")
    if returned["state_digest"] != before["state_digest"]:
        raise ReceiptError("return state does not reproduce before state")
    content_set = lambda item: sorted((row['size'], row['sha256']) for row in item['artifacts'])
    if content_set(returned) != content_set(before):
        raise ReceiptError('return artifact bytes do not reproduce before artifacts')
    return {
        "schema": "MRL_Reversible_Change_Verification_v1",
        "origin_signature": ORIGIN,
        "change_id": before["change_id"],
        "status": "roundtrip_verified",
        "allowed_for_owner_review": True,
        "receipt_digests": [before["receipt_digest"], forward["receipt_digest"], returned["receipt_digest"]],
    }


def write_new(path: Path, receipt: dict) -> None:
    """Create a receipt once; never replace an existing evidence object."""
    payload = (json.dumps(receipt, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
    except Exception:
        path.unlink(missing_ok=True)
        raise


def _read(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="action", required=True)
    record = sub.add_parser("record", help="create one receipt from a JSON specification")
    record.add_argument("--root", required=True, type=Path)
    record.add_argument("--spec", required=True, type=Path)
    record.add_argument("--output", required=True, type=Path)
    verify = sub.add_parser("verify", help="verify a complete reversible receipt chain")
    verify.add_argument("--root", required=True, type=Path)
    verify.add_argument("--before", required=True, type=Path)
    verify.add_argument("--forward", required=True, type=Path)
    verify.add_argument("--return-receipt", required=True, type=Path)
    args = parser.parse_args()
    try:
        if args.action == "record":
            receipt = build_receipt(evidence_root=args.root, **_read(args.spec))
            write_new(args.output, receipt)
            result = {"status": "receipt_created", "receipt_digest": receipt["receipt_digest"], "path": str(args.output)}
        else:
            result = verify_roundtrip(_read(args.before), _read(args.forward), _read(args.return_receipt), args.root)
        print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
        return 0
    except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError) as exc:
        print(json.dumps({"status": "verification_failed", "error": str(exc), "origin_signature": ORIGIN}, ensure_ascii=False))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
