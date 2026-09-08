#!/usr/bin/env python3
"""Verify exact product-source coverage, SHA-256 and canonical identity."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> int:
    expected = [line.strip() for line in (ROOT / "EXPECTED_FILE_LIST.txt").read_text(encoding="utf-8").splitlines() if line.strip()]
    actual = sorted(
        path.relative_to(ROOT).as_posix() for path in ROOT.rglob("*")
        if path.is_file() and "__pycache__" not in path.parts and "dist" not in path.parts
    )
    rows = {}
    for line in (ROOT / "SHA256SUMS.txt").read_text(encoding="utf-8").splitlines():
        if line.strip():
            digest, name = line.split("  ", 1)
            rows[name] = digest
    checksum_expected = [name for name in expected if name != "SHA256SUMS.txt"]
    missing = sorted(set(expected) - set(actual))
    extra = sorted(set(actual) - set(expected))
    empty = sorted(name for name in expected if (ROOT / name).exists() and (ROOT / name).stat().st_size == 0)
    mismatch = sorted(name for name in checksum_expected if name in rows and sha256(ROOT / name) != rows[name])
    checksum_missing = sorted(set(checksum_expected) - set(rows))
    checksum_extra = sorted(set(rows) - set(checksum_expected))
    manifest = json.loads((ROOT / "MANIFEST.json").read_text(encoding="utf-8"))
    identity_ok = (
        manifest.get("canonical_id") == "MRL_APIWorks_BYOH_Deployment_Product_v1"
        and manifest.get("origin_signature") == "MrLiouWord"
        and manifest.get("expected_source_file_count") == len(expected)
    )
    passed = not any([missing, extra, empty, mismatch, checksum_missing, checksum_extra]) and identity_ok
    print(json.dumps({
        "missing_files": missing,
        "unexpected_files": extra,
        "empty_files": empty,
        "checksum_mismatch": mismatch,
        "checksum_missing": checksum_missing,
        "checksum_extra": checksum_extra,
        "coverage_percent": 100 if not missing else round((len(expected) - len(missing)) / len(expected) * 100, 2),
        "identity_ok": identity_ok,
        "delivery_gate": "PRODUCT_SOURCE_DELIVERY_PASS" if passed else "PRODUCT_SOURCE_DELIVERY_FAIL"
    }, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())

