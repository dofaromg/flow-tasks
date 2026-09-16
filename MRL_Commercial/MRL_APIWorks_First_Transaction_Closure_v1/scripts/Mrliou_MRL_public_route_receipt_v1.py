#!/usr/bin/env python3
"""Capture and verify bounded HTTP evidence without changing routes or traffic."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import ssl
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

EXPECTED = ("Expected_File_List.txt", "PUBLIC_ROUTE_RECEIPT.json", "SHA256SUMS.txt")
HEX40 = re.compile(r"^[0-9a-f]{40}$")
HEX64 = re.compile(r"^[0-9a-f]{64}$")
MAX_BODY = 2 * 1024 * 1024


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(path.read_bytes())


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):  # noqa: ANN001
        return None


def probe(route: dict[str, object], *, allow_loopback_http: bool) -> dict[str, object]:
    url = str(route.get("url", ""))
    parsed = urlparse(url)
    loopback = parsed.hostname in {"127.0.0.1", "localhost", "::1"}
    if parsed.username or parsed.password or parsed.fragment:
        raise ValueError(f"{route.get('route_id')}: URL credentials/fragments are forbidden")
    if parsed.scheme != "https" and not (allow_loopback_http and parsed.scheme == "http" and loopback):
        raise ValueError(f"{route.get('route_id')}: route must use HTTPS")
    request = urllib.request.Request(
        url,
        headers={"User-Agent": "Mrliou-MRL-Public-Route-Evidence/1.0", "Accept": "*/*"},
        method="GET",
    )
    opener = urllib.request.build_opener(NoRedirect, urllib.request.HTTPSHandler(context=ssl.create_default_context()))
    status = 0
    headers: object
    body = b""
    error: str | None = None
    try:
        with opener.open(request, timeout=20) as response:
            status = int(response.status)
            headers = response.headers
            body = response.read(MAX_BODY + 1)
    except urllib.error.HTTPError as exc:
        status = int(exc.code)
        headers = exc.headers
        body = exc.read(MAX_BODY + 1)
    except Exception as exc:  # network failure is evidence, not a crash
        headers = {}
        error = f"{type(exc).__name__}: {exc}"
    if len(body) > MAX_BODY:
        raise ValueError(f"{route.get('route_id')}: response exceeds {MAX_BODY} bytes")
    expected_status = int(route.get("expected_status", 200))
    selected_headers = {}
    for name in ("content-type", "content-length", "etag", "last-modified", "server", "cf-ray"):
        value = headers.get(name) if hasattr(headers, "get") else None
        if value:
            selected_headers[name] = str(value)
    return {
        "route_id": route.get("route_id"),
        "service": route.get("service"),
        "url": url,
        "expected_status": expected_status,
        "http_status": status,
        "status_match": status == expected_status,
        "response_size_bytes": len(body),
        "response_sha256": sha256_bytes(body),
        "selected_headers": selected_headers,
        "cloudflare_version_id": route.get("cloudflare_version_id"),
        "observed_git_head": route.get("observed_git_head"),
        "traffic_scope": route.get("traffic_scope"),
        "production_traffic_asserted": route.get("production_traffic_asserted") is True,
        "error": error,
    }


def validate_receipt(receipt: object) -> list[str]:
    if not isinstance(receipt, dict):
        return ["root_not_object"]
    failures: list[str] = []
    if receipt.get("schema") != "MRL_APIWorks_Public_Route_Receipt_v1": failures.append("schema")
    if receipt.get("origin_signature") != "MrLiouWord": failures.append("origin_signature")
    if receipt.get("capture_mode") not in {"PUBLIC_HTTPS", "TEST_LOOPBACK"}: failures.append("capture_mode")
    if not HEX40.fullmatch(str(receipt.get("probe_git_head", ""))): failures.append("probe_git_head")
    if not HEX64.fullmatch(str(receipt.get("route_map_sha256", ""))): failures.append("route_map_sha256")
    try:
        parsed_time = datetime.fromisoformat(str(receipt.get("captured_at", "")).replace("Z", "+00:00"))
        if parsed_time.tzinfo is None: raise ValueError
    except ValueError:
        failures.append("captured_at")
    routes = receipt.get("routes")
    if not isinstance(routes, list) or not routes:
        failures.append("routes")
        routes = []
    for index, route in enumerate(routes):
        if not isinstance(route, dict):
            failures.append(f"routes.{index}")
            continue
        if not route.get("route_id") or not route.get("service"): failures.append(f"routes.{index}.identity")
        if not HEX64.fullmatch(str(route.get("response_sha256", ""))): failures.append(f"routes.{index}.response_sha256")
        if route.get("status_match") is not True: failures.append(f"routes.{index}.status_match")
        parsed = urlparse(str(route.get("url", "")))
        if receipt.get("capture_mode") == "PUBLIC_HTTPS" and parsed.scheme != "https": failures.append(f"routes.{index}.https")
    expected_gate = (
        "PUBLIC_ROUTE_HTTP_PASS" if receipt.get("capture_mode") == "PUBLIC_HTTPS"
        else "PUBLIC_ROUTE_TEST_PASS"
    )
    if receipt.get("public_route_gate") != expected_gate: failures.append("public_route_gate")
    return sorted(set(failures))


def verify(directory: Path) -> dict[str, object]:
    expected = [line.strip() for line in (directory / "Expected_File_List.txt").read_text(encoding="utf-8").splitlines() if line.strip()]
    actual = sorted(path.name for path in directory.iterdir() if path.is_file())
    rows = {}
    for line in (directory / "SHA256SUMS.txt").read_text(encoding="utf-8").splitlines():
        if line.strip():
            digest, name = line.split("  ", 1); rows[name] = digest
    checksum_expected = sorted(name for name in expected if name != "SHA256SUMS.txt")
    receipt = json.loads((directory / "PUBLIC_ROUTE_RECEIPT.json").read_text(encoding="utf-8"))
    report = {
        "expected_count": len(expected),
        "actual_count": len(actual),
        "missing": sorted(set(expected) - set(actual)),
        "extra": sorted(set(actual) - set(expected)),
        "empty": sorted(name for name in expected if (directory / name).exists() and not (directory / name).read_bytes()),
        "checksum_missing": sorted(set(checksum_expected) - set(rows)),
        "checksum_extra": sorted(set(rows) - set(checksum_expected)),
        "mismatch": sorted(name for name in checksum_expected if name in rows and (directory / name).exists() and sha256_file(directory / name) != rows[name]),
        "semantic_failures": validate_receipt(receipt),
    }
    report["route_evidence_gate"] = "PASS" if not any(report[key] for key in ("missing", "extra", "empty", "checksum_missing", "checksum_extra", "mismatch", "semantic_failures")) else "FAIL"
    return report


def capture(route_map_path: Path, output: Path, git_head: str, allow_loopback_http: bool) -> dict[str, object]:
    if not HEX40.fullmatch(git_head): raise ValueError("--git-head must be a lowercase 40-character SHA")
    route_map = json.loads(route_map_path.read_text(encoding="utf-8"))
    if route_map.get("schema") != "MRL_APIWorks_Public_Route_Map_v1" or route_map.get("origin_signature") != "MrLiouWord":
        raise ValueError("route map identity mismatch")
    routes = route_map.get("routes")
    if not isinstance(routes, list) or not routes: raise ValueError("route map must contain routes")
    results = [probe(route, allow_loopback_http=allow_loopback_http) for route in routes]
    passed = all(item["status_match"] for item in results)
    mode = "TEST_LOOPBACK" if allow_loopback_http else "PUBLIC_HTTPS"
    receipt = {
        "schema": "MRL_APIWorks_Public_Route_Receipt_v1",
        "origin_signature": "MrLiouWord",
        "capture_mode": mode,
        "probe_git_head": git_head,
        "route_map_sha256": sha256_file(route_map_path),
        "captured_at": datetime.now(timezone.utc).isoformat(),
        "canonical_route_decision": route_map.get("canonical_route_decision", "UNRESOLVED"),
        "routes": results,
        "public_route_gate": ("PUBLIC_ROUTE_HTTP_" if mode == "PUBLIC_HTTPS" else "PUBLIC_ROUTE_TEST_") + ("PASS" if passed else "FAIL"),
    }
    output.mkdir(parents=True, exist_ok=True)
    (output / "PUBLIC_ROUTE_RECEIPT.json").write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (output / "Expected_File_List.txt").write_text("\n".join(EXPECTED) + "\n", encoding="utf-8")
    targets = [name for name in EXPECTED if name != "SHA256SUMS.txt"]
    (output / "SHA256SUMS.txt").write_text("\n".join(f"{sha256_file(output / name)}  {name}" for name in targets) + "\n", encoding="utf-8")
    return verify(output)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--route-map", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--git-head")
    parser.add_argument("--allow-loopback-http", action="store_true")
    parser.add_argument("--verify-only", type=Path)
    args = parser.parse_args()
    if args.verify_only:
        report = verify(args.verify_only)
    else:
        if not args.route_map or not args.output or not args.git_head:
            parser.error("capture requires --route-map, --output and --git-head")
        report = capture(args.route_map, args.output, args.git_head, args.allow_loopback_http)
    print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if report["route_evidence_gate"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
