#!/usr/bin/env python3
"""Run non-activating MRL hardware smoke checks and write a redacted local record."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import platform
import re
import subprocess
from pathlib import Path

if __package__:
    from .MRL_hardware_admission_v1 import ORIGIN, digest, verify_artifact_bytes
else:
    from MRL_hardware_admission_v1 import ORIGIN, digest, verify_artifact_bytes


def _read(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError("input must be a JSON object")
    return value


def _device_query(host: dict) -> dict:
    result = subprocess.run(
        ["nvidia-smi", "--query-gpu=index,uuid,name,driver_version,memory.total",
         "--format=csv,noheader"],
        check=True, capture_output=True, text=True, timeout=15,
    )
    observed = {}
    for row in csv.reader(result.stdout.splitlines()):
        if len(row) != 5:
            raise ValueError("invalid nvidia-smi device-query row")
        index, uuid, sku, driver, memory = (field.strip() for field in row)
        observed[int(index)] = {
            "uuid": uuid, "sku": sku, "driver": driver,
            "vram_mib": int(memory.split()[0]),
        }
    expected = {
        gpu["id"]: {"uuid": gpu["uuid"], "sku": gpu["sku"],
                    "driver": host["driver"]["version"], "vram_mib": gpu["vram_mib"]}
        for gpu in host["gpus"]
    }
    if observed != expected:
        raise ValueError("live device query differs from the current Passport manifest")
    import torch

    if not torch.cuda.is_available() or torch.cuda.device_count() != len(expected):
        raise ValueError("live CUDA inventory differs from the current Passport manifest")
    gpu_by_id = {gpu["id"]: gpu for gpu in host["gpus"]}
    for gpu_id in expected:
        capability = ".".join(str(part) for part in torch.cuda.get_device_capability(gpu_id))
        if capability != gpu_by_id[gpu_id]["compute_capability"]:
            raise ValueError("live compute capability differs from the Passport manifest")
    return {"ok": True, "inventory_digest": digest(observed)}


def _run_smoke(name: str, spec: dict) -> dict:
    if not isinstance(spec, dict):
        raise ValueError(name + " command must be an object")
    argv = spec.get("argv")
    expected = spec.get("expected_stdout_sha256")
    timeout = spec.get("timeout_seconds", 180)
    if (not isinstance(argv, list) or not argv
            or not all(isinstance(part, str) and part for part in argv)
            or not isinstance(expected, str)
            or not re.fullmatch(r"[0-9a-f]{64}", expected)
            or type(timeout) is not int or not 1 <= timeout <= 600):
        raise ValueError("invalid " + name + " command specification")
    result = subprocess.run(argv, check=False, capture_output=True, timeout=timeout)
    stdout_digest = hashlib.sha256(result.stdout).hexdigest()
    stderr_digest = hashlib.sha256(result.stderr).hexdigest()
    return {
        "ok": result.returncode == 0 and stdout_digest == expected,
        "exit_code": result.returncode,
        "stdout_sha256": stdout_digest,
        "stderr_sha256": stderr_digest,
    }


def build_record(
    host: dict, workload: dict, artifact_root: Path, artifact_paths: dict,
    smoke_commands: dict, replay_record: dict | None = None,
) -> dict:
    if host.get("observation") != "current":
        raise ValueError("historical Passport observations cannot be used for smoke")
    current_os = {"family": platform.system().lower(), "version": platform.version(),
                  "arch": platform.machine()}
    if host.get("os") != current_os:
        raise ValueError("live OS differs from the current Passport manifest")
    if host.get("loaded_runner") != workload.get("runner"):
        raise ValueError("Passport runner differs from the workload")
    if host.get("loaded_runtime") != workload.get("runtime_binary"):
        raise ValueError("Passport runtime differs from the workload")
    if host.get("loaded_image") != (workload.get("image") or {}).get("id"):
        raise ValueError("Passport image differs from the workload")
    verify_artifact_bytes(workload, artifact_root, artifact_paths)
    configuration_digest = digest({"host": host, "workload": workload})
    if replay_record:
        unsigned = {key: value for key, value in replay_record.items() if key != "record_digest"}
        if (replay_record.get("schema") != "MRL_Hardware_Smoke_Record_v1"
                or replay_record.get("record_digest") != digest(unsigned)
                or replay_record.get("configuration_digest") != configuration_digest):
            raise ValueError("replay record or configuration is invalid")
    checks = {"device_query": _device_query(host)}
    for name in ("runtime_smoke", "model_smoke"):
        checks[name] = _run_smoke(name, smoke_commands.get(name))
    passed = all(check["ok"] for check in checks.values())
    record = {
        "schema": "MRL_Hardware_Smoke_Record_v1",
        "origin_signature": ORIGIN,
        "status": "smoke_passed_pending_restart_and_owner_review" if passed else "smoke_failed",
        "source_commit": workload["source_commit"],
        "configuration_digest": configuration_digest,
        "bundle_digest": workload["bundle_digest"],
        "model_digest": workload["model"]["digest"],
        "runner_digest": workload["runner"]["digest"],
        "runtime_digest": workload["runtime_binary"]["digest"],
        "checks": checks,
        "replay_of_digest": (replay_record or {}).get("record_digest"),
    }
    record["record_digest"] = digest(record)
    return record


def write_new(path: Path, record: dict) -> None:
    payload = (json.dumps(record, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode()
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


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", required=True, type=Path, help="existing current Passport output")
    parser.add_argument("--workload", required=True, type=Path)
    parser.add_argument("--artifact-root", required=True, type=Path)
    parser.add_argument("--artifact-paths", required=True, type=Path)
    parser.add_argument("--smoke-commands", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--replay-record", type=Path)
    args = parser.parse_args(argv)
    try:
        replay = _read(args.replay_record) if args.replay_record else None
        record = build_record(
            _read(args.host), _read(args.workload), args.artifact_root,
            _read(args.artifact_paths), _read(args.smoke_commands), replay,
        )
        write_new(args.output, record)
        print(json.dumps({"status": record["status"], "record_digest": record["record_digest"],
                          "record": args.output.name}, ensure_ascii=False))
        return 0 if record["status"].startswith("smoke_passed") else 1
    except (OSError, ValueError, KeyError, TypeError, subprocess.SubprocessError) as exc:
        print(json.dumps({"status": "smoke_failed", "error": str(exc), "origin_signature": ORIGIN},
                         ensure_ascii=False))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
