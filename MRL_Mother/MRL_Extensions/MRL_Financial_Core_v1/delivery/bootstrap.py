"""Verify and install the standalone bundle locally without a package index."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import platform
import re
import os
import subprocess
import sys
import venv

BASE_MODULE = "MRL_Mother.MRL_Extensions.MRL_Financial_Core_v1"
ENV_NAME = ".mrl-finance-venv"
RECEIPT = "MRL_INSTALL_RECEIPT.json"


def bundle_root():
    return Path(__file__).resolve().parents[4]


def verify(root):
    """Verify original source paths, every wheel, lock and launcher; reject extras."""
    root = Path(root).resolve()
    manifest_path = root / "PACKAGE_MANIFEST.json"
    if manifest_path.is_symlink():
        raise ValueError("MANIFEST_SYMLINK")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    if manifest.get("schema") != "MRL_Financial_Standalone/v1" or manifest.get("origin_signature") != "MrLiouWord":
        raise ValueError("INVALID_PACKAGE_MANIFEST")
    expected = {"PACKAGE_MANIFEST.json"}
    folded = {"package_manifest.json"}
    for item in manifest["files"]:
        if type(item) is not dict or set(item) != {"path", "size", "sha256"}:
            raise ValueError("INVALID_PACKAGE_ENTRY")
        name = item["path"]
        if not isinstance(name, str) or not name or "\\" in name or ":" in name:
            raise ValueError("UNSAFE_PACKAGE_PATH")
        path = PurePosixPath(name)
        if path.is_absolute() or ".." in path.parts or str(path) != name or name.casefold() in folded:
            raise ValueError("UNSAFE_OR_DUPLICATE_PACKAGE_PATH")
        expected.add(name)
        folded.add(name.casefold())
        target = root / path
        if not target.is_file() or any(p.is_symlink() for p in (target, *target.parents) if p != root):
            raise ValueError("PACKAGE_FILE_MISSING_OR_SYMLINK")
        raw = target.read_bytes()
        if (type(item["size"]) is not int or item["size"] <= 0 or len(raw) != item["size"] or
                not isinstance(item["sha256"], str) or not re.fullmatch(r"[0-9a-f]{64}", item["sha256"]) or
                hashlib.sha256(raw).hexdigest() != item["sha256"]):
            raise ValueError("PACKAGE_HASH_OR_SIZE_MISMATCH")
    if type(manifest.get("expected_file_count")) is not int or manifest["expected_file_count"] != len(expected):
        raise ValueError("PACKAGE_COUNT_MISMATCH")
    if manifest.get("wheel_count") != sum(name.startswith("wheelhouse/") for name in expected):
        raise ValueError("PACKAGE_WHEEL_COUNT_MISMATCH")
    if (root / ENV_NAME).is_symlink():
        raise ValueError("INSTALL_ENVIRONMENT_SYMLINK")
    actual = set()
    for path in root.rglob("*"):
        relative = path.relative_to(root)
        if relative.parts[0] == ENV_NAME or str(relative) == RECEIPT:
            continue
        if path.is_file() or path.is_symlink():
            actual.add(relative.as_posix())
    if actual != expected:
        raise ValueError("PACKAGE_FILE_SET_MISMATCH")
    return manifest


def runtime_match(manifest):
    if sys.version_info[:2] != (3, 12) or manifest.get("python") != "3.12":
        raise ValueError("PYTHON_312_REQUIRED")
    if platform.system() != manifest.get("target_os") or platform.machine().lower() not in {"x86_64", "amd64"}:
        raise ValueError("PACKAGE_PLATFORM_MISMATCH")


def python_path(root):
    return Path(root) / ENV_NAME / ("Scripts/python.exe" if platform.system() == "Windows" else "bin/python")


def clean_environment(for_tests=False):
    env = dict(os.environ)
    for key in ("PYTHONPATH", "PYTHONHOME"):
        env.pop(key, None)
    if for_tests:
        env.pop("MRL_MERCURY_API_TOKEN", None)
    env.update(PYTHONDONTWRITEBYTECODE="1", PIP_CONFIG_FILE=os.devnull,
               PIP_DISABLE_PIP_VERSION_CHECK="1", PIP_NO_INDEX="1")
    return env


def run_tests(root):
    """Only mock-provider/cryptographic tests; no account provisioning or transfers."""
    root = Path(root).resolve()
    manifest = verify(root)
    runtime_match(manifest)
    interpreter = python_path(root)
    if not interpreter.is_file():
        raise ValueError("INSTALL_FIRST")
    code = "import sys,unittest;sys.path.insert(0,sys.argv.pop(1));unittest.main(module=None)"
    subprocess.run([str(interpreter), "-I", "-X", "utf8", "-B", "-c", code, str(root),
                    BASE_MODULE + ".test_core", BASE_MODULE + ".external.test_external",
                    BASE_MODULE + ".delivery.test_delivery", "-v"],
                   check=True, cwd=root, env=clean_environment(for_tests=True))


def install(root):
    """Create a new version-local venv, install hashed wheels offline, then self-test."""
    root = Path(root).resolve()
    manifest = verify(root)
    runtime_match(manifest)
    target = root / ENV_NAME
    if target.exists() or (root / RECEIPT).exists():
        raise FileExistsError("INSTALL_TARGET_EXISTS")
    target.mkdir()
    venv.EnvBuilder(with_pip=True, symlinks=False).create(target)
    interpreter = python_path(root)
    subprocess.run([str(interpreter), "-I", "-X", "utf8", "-m", "pip", "install", "--no-index", "--no-compile",
                    "--find-links", str(root / "wheelhouse"), "--require-hashes",
                    "-r", str(root / "requirements.lock")],
                   check=True, cwd=root, env=clean_environment(for_tests=True))
    run_tests(root)
    receipt = {"origin_signature": "MrLiouWord", "state": "OFFLINE_INSTALL_AND_SELF_TEST_PASS",
               "source_sha": manifest["source_sha"], "source_mode": manifest["source_mode"],
               "target_os": manifest["target_os"], "package_file_count": manifest["expected_file_count"],
               "manifest_sha256": hashlib.sha256((root / "PACKAGE_MANIFEST.json").read_bytes()).hexdigest(),
               "external_accounts_enabled": False, "real_asset_transfer_performed": False,
               "dl580_live_acceptance": "NOT_ESTABLISHED_BY_THIS_RECEIPT"}
    with (root / RECEIPT).open("x", encoding="utf-8") as stream:
        json.dump(receipt, stream, ensure_ascii=False, indent=2)
        stream.write("\n")
    return receipt


def launch(root, module, arguments):
    root = Path(root).resolve()
    runtime_match(verify(root))
    interpreter = python_path(root)
    if not interpreter.is_file():
        raise ValueError("INSTALL_FIRST")
    code = "import runpy,sys;sys.path.insert(0,sys.argv.pop(1));runpy.run_module(sys.argv.pop(1),run_name='__main__')"
    return subprocess.run([str(interpreter), "-I", "-X", "utf8", "-B", "-c", code, str(root), module, *arguments],
                          cwd=root, check=False, env=clean_environment()).returncode


def main(argv=None):
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description="MRL 本地離線安裝及驗收")
    sub = parser.add_subparsers(dest="command", required=True)
    for command in ("verify", "install", "self-test"):
        sub.add_parser(command)
    for command in ("ledger", "external"):
        sub.add_parser(command).add_argument("arguments", nargs=argparse.REMAINDER)
    args = parser.parse_args(argv)
    root = bundle_root()
    try:
        if args.command == "install":
            result = install(root)
        elif args.command == "self-test":
            run_tests(root)
            result = {"state": "SELF_TEST_PASS"}
        elif args.command == "verify":
            m = verify(root)
            result = {"state": "PACKAGE_VERIFIED", "files": m["expected_file_count"], "source_sha": m["source_sha"]}
        else:
            arguments = args.arguments[1:] if args.arguments[:1] == ["--"] else args.arguments
            module = BASE_MODULE + (".external.cli" if args.command == "external" else ".cli")
            return launch(root, module, arguments)
        print(json.dumps(result, ensure_ascii=False))
        return 0
    except (OSError, ValueError, KeyError, TypeError, subprocess.CalledProcessError) as exc:
        reason = str(exc) if re.fullmatch(r"[A-Z0-9_]+", str(exc)) else type(exc).__name__
        print(json.dumps({"state": "INSTALL_OR_VERIFY_FAILED", "reason": reason}))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
