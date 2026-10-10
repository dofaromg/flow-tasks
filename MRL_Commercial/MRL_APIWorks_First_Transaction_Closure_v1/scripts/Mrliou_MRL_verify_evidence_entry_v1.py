#!/usr/bin/env python3
"""Verify an offline evidence entry without extracting or executing its ZIP."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import stat
import zipfile
from pathlib import Path, PurePosixPath
from typing import Any

PRODUCT = "MRL_APIWorks_BYOH_Deployment_Product_v1"
BUNDLE = f"{PRODUCT}.zip"
MANIFEST = "MRL_PRODUCT_BUNDLE_MANIFEST.json"
MUTABLE = "customer_config/MRL_runtime.local.json"
MAX_BYTES = 100 * 1024 * 1024


def digest(data: bytes) -> str:
    """Return a lowercase SHA-256 digest."""
    return hashlib.sha256(data).hexdigest()


def safe_name(name: str) -> bool:
    """Accept only normalized relative POSIX file names."""
    return (
        isinstance(name, str)
        and bool(name)
        and not name.startswith("/")
        and "\\" not in name
        and ":" not in name
        and not any(ord(char) < 32 for char in name)
        and not any(part in {"", ".", ".."} for part in name.split("/"))
        and str(PurePosixPath(name)) == name
    )


def verify_zip(path: Path, expected: dict[str, Any]) -> list[str]:
    """Bind all original ZIP bytes to the pre-build source inventory."""
    failures: list[str] = []
    try:
        if not expected or any(not safe_name(name) for name in expected):
            return ["zip.invalid_expected_inventory"]
        with zipfile.ZipFile(path) as archive:
            entries = archive.infolist()
            names = [item.filename for item in entries]
            if len(names) != len(set(names)):
                failures.append("zip.duplicate_members")
            if any(not safe_name(name) for name in names):
                failures.append("zip.unsafe_path")
            if any(stat.S_ISLNK(item.external_attr >> 16) for item in entries):
                failures.append("zip.symlink")
            if sum(item.file_size for item in entries) > MAX_BYTES:
                failures.append("zip.expanded_size_limit")
            prefix = PRODUCT + "/"
            wanted = {prefix + name for name in expected} | {prefix + MANIFEST}
            if set(names) != wanted:
                failures.append("zip.member_set")
            if failures:
                return failures
            manifest = json.loads(archive.read(prefix + MANIFEST))
            if (
                manifest.get("archive_root") != PRODUCT
                or manifest.get("canonical_id") != PRODUCT
                or manifest.get("sku") != "MRL-APIWORKS-BYOH-DEPLOY-V1"
                or manifest.get("origin_signature") != "MrLiouWord"
                or manifest.get("mutable_after_extraction") != [MUTABLE]
            ):
                failures.append("zip.manifest_identity")
            records = manifest["files"]
            if not isinstance(records, list):
                return failures + ["zip.manifest_files_type"]
            indexed = {item["path"]: item for item in records}
            if len(indexed) != len(records) or set(indexed) != set(expected):
                failures.append("zip.manifest_member_set")
            for name, identity in expected.items():
                data = archive.read(prefix + name)
                actual = {"size_bytes": len(data), "sha256": digest(data)}
                if actual != identity:
                    failures.append("zip.source_mismatch:" + name)
                item = indexed.get(name, {})
                if item.get("size") != len(data) or item.get("sha256") != actual["sha256"]:
                    failures.append("zip.manifest_mismatch:" + name)
                if item.get("mutable_after_extraction") is not (name == MUTABLE):
                    failures.append("zip.mutable_flag:" + name)
    except (OSError, ValueError, KeyError, TypeError, AttributeError,
            zipfile.BadZipFile, RuntimeError) as error:
        failures.append("zip.invalid:" + type(error).__name__)
    return failures


def verify_directory(root: Path) -> dict[str, Any]:
    """Compare the exact file set, hashes, copied source, and delivered ZIP."""
    report: dict[str, Any] = {
        "scope": "EVIDENCE_ENTRY_INTEGRITY_ONLY",
        "missing": [], "extra": [], "empty": [], "mismatch": [],
        "failures": [],
    }
    try:
        expected = (root / "Expected_File_List.txt").read_text().splitlines()
        if (not expected or len(expected) != len(set(expected))
                or any(not safe_name(name) for name in expected)):
            raise ValueError("invalid or duplicate expected file name")
        files = [item for item in root.rglob("*") if item.is_file() or item.is_symlink()]
        actual = {item.relative_to(root).as_posix() for item in files}
        report["expected_count"] = len(expected)
        report["actual_count"] = len(actual)
        report["missing"] = sorted(set(expected) - actual)
        report["extra"] = sorted(actual - set(expected))
        if any(item.is_symlink() for item in root.rglob("*")):
            report["failures"].append("entry.symlink")
            raise ValueError("symlink found; no linked files read")
        rows: dict[str, str] = {}
        for line in (root / "SHA256SUMS.txt").read_text().splitlines():
            checksum, name = line.split("  ", 1)
            if not safe_name(name) or name in rows or not re.fullmatch("[0-9a-f]{64}", checksum):
                raise ValueError("invalid checksum row")
            rows[name] = checksum
        if set(rows) != set(expected) - {"SHA256SUMS.txt"}:
            report["failures"].append("entry.checksum_coverage")
        for name in sorted(set(expected) & actual):
            data = (root / name).read_bytes()
            if not data:
                report["empty"].append(name)
            if name in rows and digest(data) != rows[name]:
                report["mismatch"].append(name)
        if not any(report[key] for key in ("missing", "extra", "empty", "mismatch", "failures")):
            inventory = json.loads((root / "SOURCE_INVENTORY.json").read_text())
            for name, identity in inventory.items():
                if not safe_name(name) or "source/" + name not in actual:
                    raise ValueError("invalid source inventory entry")
                data = (root / "source" / name).read_bytes()
                if identity != {"size_bytes": len(data), "sha256": digest(data)}:
                    report["failures"].append("entry.source_identity:" + name)
            source_names = {name[7:] for name in actual if name.startswith("source/")}
            if set(inventory) != source_names:
                report["failures"].append("entry.source_coverage")
            expected_zip = json.loads((root / "EXPECTED_PRODUCT_FILES.json").read_text())
            report["failures"].extend(verify_zip(root / BUNDLE, expected_zip))
            ledger = json.loads((root / "EVIDENCE_LEDGER.json").read_text())
            blob = (root / BUNDLE).read_bytes()
            if ledger.get("artifact") != {"path": BUNDLE, "size_bytes": len(blob), "sha256": digest(blob)}:
                report["failures"].append("entry.artifact_identity")
    except (OSError, ValueError, KeyError, TypeError, AttributeError) as error:
        report["failures"].append("entry.invalid:" + str(error))
    report["integrity_gate"] = (
        "PASS" if not any(report[key] for key in ("missing", "extra", "empty", "mismatch", "failures"))
        else "FAIL"
    )
    return report


def main() -> int:
    """Print machine-readable integrity results; never infer business status."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("directory", type=Path)
    args = parser.parse_args()
    result = verify_directory(args.directory.resolve())
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["integrity_gate"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
