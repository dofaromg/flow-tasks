"""Build an offline-installable module ZIP from explicit source files and wheels."""

from __future__ import annotations

import argparse
from email.parser import BytesParser
import hashlib
import json
from pathlib import Path
import re
import zipfile

BASE = "MRL_Mother/MRL_Extensions/MRL_Financial_Core_v1/"
MODULE_FILES = (
    "__init__.py", "core.py", "cli.py", "test_core.py", "README.md", "CONSTITUTION.md",
    "module.json", "requirements.txt", "AUDIT.json", "external/__init__.py",
    "external/transport.py", "external/gate.py", "external/mercury.py", "external/evm.py",
    "external/gateway.py", "external/cli.py", "external/test_external.py",
    "external/README.md", "external/requirements.txt", "external/sources.json",
    "delivery/__init__.py", "delivery/build_package.py", "delivery/bootstrap.py",
    "delivery/test_delivery.py", "delivery/README.md",
)
SOURCE_FILES = tuple(BASE + name for name in MODULE_FILES) + (
    "MRL_Mother/09_workflow/tool_registry.py", "MRL_Mother/MRL_MotherModel/module_registry.json",
)
BOOTSTRAP = BASE + "delivery/bootstrap.py"


def read_regular(root, relative):
    """Reject missing, empty or symlinked source dependencies."""
    root = Path(root).resolve()
    path = root / relative
    if not path.is_file() or any(p.is_symlink() for p in (path, *path.parents) if p != root):
        raise ValueError("SOURCE_FILE_MISSING_OR_SYMLINK: " + relative)
    raw = path.read_bytes()
    if not raw:
        raise ValueError("EMPTY_SOURCE: " + relative)
    return raw


def wheel_identity(path):
    """Read bounded wheel metadata to construct a fully hashed install lock."""
    with zipfile.ZipFile(path) as wheel:
        entries = [n for n in wheel.namelist() if n.endswith(".dist-info/METADATA")]
        if len(entries) != 1 or wheel.getinfo(entries[0]).file_size > 1024 * 1024:
            raise ValueError("INVALID_WHEEL_METADATA")
        metadata = BytesParser().parsebytes(wheel.read(entries[0]))
    name, version = metadata.get("Name", ""), metadata.get("Version", "")
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]*", name) or not re.fullmatch(r"[A-Za-z0-9.!+_-]+", version):
        raise ValueError("INVALID_WHEEL_IDENTITY")
    return re.sub(r"[-_.]+", "-", name).lower(), version


def build(source_root, wheelhouse, output, target_os, source_sha, source_mode="GITHUB_EXACT_HEAD"):
    """Package verified original paths and actual dependency wheels, create-only."""
    if target_os not in {"Linux", "Windows"} or not re.fullmatch(r"[0-9a-f]{40}", source_sha):
        raise ValueError("INVALID_BUILD_IDENTITY")
    if source_mode not in {"GITHUB_EXACT_HEAD", "WORKSPACE_SNAPSHOT"}:
        raise ValueError("INVALID_SOURCE_MODE")
    payload = {name: read_regular(source_root, name) for name in SOURCE_FILES}
    paths = sorted(Path(wheelhouse).glob("*.whl"))
    if not paths:
        raise ValueError("DEPENDENCY_WHEELS_REQUIRED")
    locked, identities = [], {}
    for path in paths:
        if path.is_symlink() or not re.fullmatch(r"[A-Za-z0-9_.+!-]+\.whl", path.name):
            raise ValueError("INVALID_WHEEL_PATH")
        name, version = wheel_identity(path)
        if name in identities:
            raise ValueError("DUPLICATE_WHEEL_DISTRIBUTION")
        identities[name] = version
        raw = path.read_bytes()
        payload["wheelhouse/" + path.name] = raw
        locked.append(f"{name}=={version} --hash=sha256:{hashlib.sha256(raw).hexdigest()}")
    if identities.get("cryptography") != "50.0.2" or identities.get("eth-account") != "0.14.0":
        raise ValueError("REQUIRED_RUNTIME_WHEELS_MISSING")
    payload["requirements.lock"] = ("\n".join(sorted(locked)) + "\n").encode()
    payload["MRL_INSTALL_WINDOWS.cmd"] = (
        '@echo off\r\npy -3.12 "%~dp0' + BOOTSTRAP.replace("/", "\\") + '" install\r\nexit /b %errorlevel%\r\n'
    ).encode("ascii")
    payload["MRL_INSTALL_LINUX.sh"] = (
        '#!/bin/sh\nset -eu\nMRL_BUNDLE_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)\n'
        'exec python3.12 "$MRL_BUNDLE_DIR/' + BOOTSTRAP + '" install\n'
    ).encode("ascii")
    manifest = {
        "schema": "MRL_Financial_Standalone/v1", "origin_signature": "MrLiouWord",
        "canonical_authority": "Mr.liou", "target_os": target_os, "python": "3.12",
        "source_sha": source_sha, "source_mode": source_mode,
        "expected_file_count": len(payload) + 1, "wheel_count": len(paths),
        "files": [{"path": p, "size": len(raw), "sha256": hashlib.sha256(raw).hexdigest()}
                  for p, raw in sorted(payload.items())],
        "manifest_self_hash": "Recorded by the archive SHA-256 sidecar; not recursive",
        "external_access": "DISABLED_UNTIL_EXPLICIT_AUTHORIZATION_AND_CONFIGURATION",
        "cloudflare_required": False, "python_interpreter_included": False,
    }
    payload["PACKAGE_MANIFEST.json"] = (json.dumps(manifest, ensure_ascii=False, indent=2) + "\n").encode()
    output = Path(output)
    if output.exists() or output.with_suffix(output.suffix + ".sha256").exists():
        raise FileExistsError("PACKAGE_OUTPUT_EXISTS")
    output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output, "x", compression=zipfile.ZIP_DEFLATED) as archive:
        for name, raw in sorted(payload.items()):
            archive.writestr(name, raw)
    with zipfile.ZipFile(output) as archive:
        if set(archive.namelist()) != set(payload) or archive.testzip() is not None:
            raise ValueError("PACKAGE_ARCHIVE_MISMATCH")
        if any(archive.read(name) != raw for name, raw in payload.items()):
            raise ValueError("PACKAGE_READBACK_MISMATCH")
    digest = hashlib.sha256(output.read_bytes()).hexdigest()
    with output.with_suffix(output.suffix + ".sha256").open("x", encoding="ascii") as stream:
        stream.write(digest + "  " + output.name + "\n")
    return {"archive": output.name, "sha256": digest, "file_count": len(payload),
            "wheel_count": len(paths), "coverage": 100, "missing": [], "mismatch": []}


def main(argv=None):
    parser = argparse.ArgumentParser(description="Build standalone MRL financial module")
    parser.add_argument("--source-root", required=True)
    parser.add_argument("--wheelhouse", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--target-os", choices=["Linux", "Windows"], required=True)
    parser.add_argument("--source-sha", required=True)
    parser.add_argument("--source-mode", choices=["GITHUB_EXACT_HEAD", "WORKSPACE_SNAPSHOT"], default="GITHUB_EXACT_HEAD")
    args = parser.parse_args(argv)
    result = build(args.source_root, args.wheelhouse, args.output, args.target_os,
                   args.source_sha, args.source_mode)
    print(json.dumps(result))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
