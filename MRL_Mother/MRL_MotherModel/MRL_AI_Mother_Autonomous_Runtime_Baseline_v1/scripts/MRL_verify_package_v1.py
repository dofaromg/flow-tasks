#!/usr/bin/env python3
"""Verify file coverage, checksums and autonomous endpoint policy."""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
EXPECTED = ROOT / "EXPECTED_FILE_LIST.txt"
CHECKSUMS = ROOT / "SHA256SUMS.txt"
MANIFEST = ROOT / "MANIFEST.json"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> int:
    expected = [line.strip() for line in EXPECTED.read_text(encoding="utf-8").splitlines() if line.strip()]
    actual = sorted(
        str(path.relative_to(ROOT)).replace("\\", "/")
        for path in ROOT.rglob("*")
        if path.is_file() and "__pycache__" not in path.parts
    )
    missing = sorted(set(expected) - set(actual))
    extra = sorted(set(actual) - set(expected))
    empty = sorted(name for name in expected if (ROOT / name).exists() and (ROOT / name).stat().st_size == 0)

    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    manifest_ok = (
        manifest.get("canonical_id") == "MRL_AI_Mother_Autonomous_Runtime_Baseline_v1"
        and manifest.get("origin_signature") == "MrLiouWord"
        and manifest.get("expected_file_count") == len(expected)
    )

    checksum_rows: dict[str, str] = {}
    for line in CHECKSUMS.read_text(encoding="utf-8").splitlines():
        if line.strip():
            digest, name = line.split("  ", 1)
            checksum_rows[name] = digest
    checksum_expected = sorted(name for name in expected if name != "SHA256SUMS.txt")
    checksum_missing = sorted(set(checksum_expected) - set(checksum_rows))
    checksum_extra = sorted(set(checksum_rows) - set(checksum_expected))
    checksum_mismatch = sorted(
        name
        for name in checksum_expected
        if (ROOT / name).exists()
        and name in checksum_rows
        and sha256(ROOT / name) != checksum_rows[name]
    )

    autonomy_violations: list[str] = []
    config = json.loads(
        (ROOT / "config" / "MRL_runtime.local.example.json").read_text(encoding="utf-8")
    )
    required_policy = {
        "local_model_required": True,
        "external_model_endpoints_allowed": False,
        "stub_counts_as_inference": False,
        "loopback_gateway_only": True,
    }
    if config.get("autonomy_policy") != required_policy:
        autonomy_violations.append("config/MRL_runtime.local.example.json:autonomy_policy")
    endpoint = str((config.get("local_model") or {}).get("endpoint") or "")
    endpoint_url = urlparse(endpoint)
    if endpoint_url.scheme not in {"http", "https"} or endpoint_url.hostname not in {
        "127.0.0.1",
        "localhost",
        "::1",
    }:
        autonomy_violations.append("config/MRL_runtime.local.example.json:local_model.endpoint")
    gateway_host = str((config.get("apiworks_gateway") or {}).get("host") or "")
    if gateway_host not in {"127.0.0.1", "localhost", "::1"}:
        autonomy_violations.append("config/MRL_runtime.local.example.json:apiworks_gateway.host")

    policy_files = list((ROOT / "runtime").glob("*.py")) + [
        ROOT / "config" / "MRL_runtime.local.example.json"
    ]
    for path in policy_files:
        content = path.read_text(encoding="utf-8")
        for candidate in re.findall(r'https?://[^\s"\']+', content):
            if "{" in candidate or "}" in candidate:
                continue
            hostname = urlparse(candidate.rstrip("/),]")).hostname
            if hostname not in {"127.0.0.1", "localhost", "::1"}:
                autonomy_violations.append(
                    f"{path.relative_to(ROOT)}:non_loopback_url:{hostname or candidate}"
                )

    report = {
        "canonical_id": manifest.get("canonical_id"),
        "expected_files": len(expected),
        "actual_files": len(actual),
        "missing_files": missing,
        "unexpected_files": extra,
        "empty_files": empty,
        "manifest_ok": manifest_ok,
        "checksum_missing": checksum_missing,
        "checksum_extra": checksum_extra,
        "checksum_mismatch": checksum_mismatch,
        "autonomy_policy_violations": autonomy_violations,
    }
    passed = not any(
        [missing, extra, empty, checksum_missing, checksum_extra, checksum_mismatch, autonomy_violations]
    ) and manifest_ok
    report["coverage_percent"] = 100 if not missing else round((len(expected) - len(missing)) / len(expected) * 100, 2)
    report["delivery_gate"] = "DELIVERY_PASS" if passed else "DELIVERY_FAIL"
    print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
