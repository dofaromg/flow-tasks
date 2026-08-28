#!/usr/bin/env python3
"""Build and verify explicit-consent MRL return bundles on user-owned hardware."""

from __future__ import annotations

import argparse
import hashlib
import json
import uuid
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

from . import ORIGIN_SIGNATURE

MANIFEST_NAME = "MRL_RETURN_MANIFEST.json"


class MRLReturnBundleError(ValueError):
    """Raised when a return bundle violates the local export policy."""


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_policy(path: Path) -> dict[str, Any]:
    policy = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(policy, dict):
        raise MRLReturnBundleError("return policy must be a JSON object")
    if policy.get("automatic_upload_allowed") is not False:
        raise MRLReturnBundleError("baseline policy must disable automatic upload")
    return policy


def build_return_bundle(
    *,
    files: Iterable[Path],
    output_path: Path,
    policy: dict[str, Any],
    consent: bool,
    purpose: str,
    hardware_id: str,
    model_release_id: str,
) -> dict[str, Any]:
    """Package only explicitly selected files and embed a checksummed manifest."""
    if not consent:
        raise MRLReturnBundleError("explicit user consent is required")
    if not purpose.strip():
        raise MRLReturnBundleError("return purpose is required")
    if not hardware_id.strip() or not model_release_id.strip():
        raise MRLReturnBundleError("hardware_id and model_release_id are required")

    selected = [Path(item) for item in files]
    if not selected:
        raise MRLReturnBundleError("at least one explicit file is required")
    allowed = {str(item).lower() for item in policy.get("allowed_extensions", [])}
    max_bytes = int(policy.get("max_bundle_bytes", 0))
    blocked_names = {str(item).lower() for item in policy.get("blocked_filenames", [])}
    total_bytes = 0
    entries: list[dict[str, Any]] = []
    validated_sources: list[Path] = []
    seen_names: set[str] = set()

    for raw in selected:
        if raw.is_symlink() or not raw.is_file():
            raise MRLReturnBundleError(f"not a regular file: {raw.name}")
        source = raw.resolve(strict=True)
        if source.is_symlink():
            raise MRLReturnBundleError(f"not a regular file: {source.name}")
        if source.name.lower() in blocked_names:
            raise MRLReturnBundleError(f"blocked filename: {source.name}")
        if allowed and source.suffix.lower() not in allowed:
            raise MRLReturnBundleError(f"extension not allowed: {source.suffix or '<none>'}")
        if source.name in seen_names:
            raise MRLReturnBundleError(f"duplicate payload name: {source.name}")
        seen_names.add(source.name)
        size = source.stat().st_size
        if size <= 0:
            raise MRLReturnBundleError(f"empty file rejected: {source.name}")
        total_bytes += size
        entries.append({"name": source.name, "size": size, "sha256": _sha256(source)})
        validated_sources.append(source)

    if max_bytes <= 0 or total_bytes > max_bytes:
        raise MRLReturnBundleError("selected files exceed the configured bundle limit")

    manifest = {
        "schema": "MRL_Return_Bundle_v1",
        "bundle_id": f"MRL_return_{uuid.uuid4().hex}",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "origin_signature": ORIGIN_SIGNATURE,
        "hardware_id": hardware_id,
        "model_release_id": model_release_id,
        "purpose": purpose,
        "consent": {"explicit": True, "automatic_upload": False},
        "files": entries,
        "total_bytes": total_bytes,
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr(MANIFEST_NAME, json.dumps(manifest, ensure_ascii=False, indent=2))
        for source in validated_sources:
            archive.write(source, arcname=f"payload/{source.name}")
    return {"manifest": manifest, "bundle_path": str(output_path), "bundle_sha256": _sha256(output_path)}


def verify_return_bundle(path: Path) -> dict[str, Any]:
    """Verify manifest coverage, sizes and SHA-256 values without extracting files."""
    with zipfile.ZipFile(path, "r") as archive:
        names = set(archive.namelist())
        if MANIFEST_NAME not in names:
            return {"ok": False, "reason": "manifest_missing"}
        try:
            manifest = json.loads(archive.read(MANIFEST_NAME).decode("utf-8"))
            if not isinstance(manifest, dict) or not isinstance(manifest.get("files"), list):
                return {"ok": False, "reason": "manifest_malformed"}
        except (ValueError, KeyError) as exc:
            return {"ok": False, "reason": f"manifest_parse_error: {exc}"}
        required = {
            "schema",
            "bundle_id",
            "created_at",
            "origin_signature",
            "hardware_id",
            "model_release_id",
            "purpose",
            "consent",
            "files",
            "total_bytes",
        }
        if not required.issubset(manifest):
            return {"ok": False, "reason": "manifest_required_field_missing"}
        if any(
            not isinstance(entry, dict)
            or not isinstance(entry.get("name"), str)
            or not isinstance(entry.get("size"), int)
            or not isinstance(entry.get("sha256"), str)
            for entry in manifest["files"]
        ):
            return {"ok": False, "reason": "manifest_file_entry_malformed"}
        expected = {f"payload/{entry['name']}" for entry in manifest["files"]}
        actual = {n for n in names if not n.endswith("/")} - {MANIFEST_NAME}
        if actual != expected:
            return {"ok": False, "reason": "payload_coverage_mismatch"}
        for entry in manifest["files"]:
            size = 0
            digest = hashlib.sha256()
            with archive.open(f"payload/{entry['name']}", "r") as payload:
                for chunk in iter(lambda: payload.read(1024 * 1024), b""):
                    size += len(chunk)
                    digest.update(chunk)
            if size != entry["size"]:
                return {"ok": False, "reason": "size_mismatch", "file": entry["name"]}
            if digest.hexdigest() != entry["sha256"]:
                return {"ok": False, "reason": "sha256_mismatch", "file": entry["name"]}
    return {"ok": True, "files": len(expected), "bundle_sha256": _sha256(path)}


def main() -> int:
    parser = argparse.ArgumentParser(description="Build an explicit MRL return bundle")
    parser.add_argument("--policy", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--purpose", required=True)
    parser.add_argument("--hardware-id", required=True)
    parser.add_argument("--model-release-id", required=True)
    parser.add_argument("--consent", action="store_true")
    parser.add_argument("files", nargs="+", type=Path)
    args = parser.parse_args()
    result = build_return_bundle(
        files=args.files,
        output_path=args.output,
        policy=load_policy(args.policy),
        consent=args.consent,
        purpose=args.purpose,
        hardware_id=args.hardware_id,
        model_release_id=args.model_release_id,
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
