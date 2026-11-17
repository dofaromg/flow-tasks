#!/usr/bin/env python3
"""MRL-34 admission. No driver/toolkit installation or runtime mutation.

origin_signature: MrLiouWord
The matrix is trusted release policy; host/workload documents are claims to check.
Only a release-reviewed exact acceptance entry can grant admission.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path

ORIGIN = "MrLiouWord"
MATRIX = Path(__file__).resolve().parents[1] / "hardware/MRL_hardware_matrix_v1.json"
DIGEST = re.compile(r"sha256:[0-9a-f]{64}\Z")


class AdmissionError(ValueError):
    """Fail-closed decision from the canonical hardware gate."""


def digest(value: object) -> str:
    """Hash canonical JSON for an exact, reproducible configuration identity."""
    return "sha256:" + hashlib.sha256(json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False,
        allow_nan=False).encode("utf-8")).hexdigest()


def version(value: object) -> tuple[int, ...]:
    """Parse numeric releases, never compare driver versions as floats."""
    if not isinstance(value, str) or not re.fullmatch(r"\d+\.\d+(?:\.\d+)?", value):
        raise ValueError("invalid numeric version")
    return tuple(int(part) for part in value.split(".")) + (0,) * (3-len(value.split(".")))


def load_matrix(path: Path = MATRIX) -> dict:
    """Load release policy without contacting a remote service."""
    return json.loads(path.read_text(encoding="utf-8"))


def _required(obj: dict, fields: tuple[str, ...]) -> None:
    if not isinstance(obj, dict) or any(obj.get(key) in (None, "", []) for key in fields):
        raise ValueError("missing manifest field: " + ",".join(fields))


def _validate(host: dict, workload: dict) -> None:
    _required(host, ("schema", "origin_signature", "os", "driver", "gpus", "observation"))
    _required(workload, ("schema", "origin_signature", "bundle_id", "bundle_digest", "os",
                         "cuda_runtime", "runtime_abi", "toolkit", "runner", "model",
                         "quantization", "image"))
    if host["schema"] != "MRL_Hardware_Manifest_v1" or workload["schema"] != "MRL_Workload_Manifest_v1":
        raise ValueError("schema mismatch")
    if host["origin_signature"] != ORIGIN or workload["origin_signature"] != ORIGIN:
        raise ValueError("origin mismatch")
    _required(host["os"], ("family", "version", "arch"))
    _required(host["driver"], ("vendor", "version"))
    version(host["driver"]["version"])
    if not isinstance(host["gpus"], list) or not host["gpus"]:
        raise ValueError("empty GPU inventory")
    ids = []
    for gpu in host["gpus"]:
        _required(gpu, ("id", "vendor", "architecture", "sku", "compute_capability", "vram_mib"))
        if type(gpu["id"]) is not int or gpu["id"] < 0 or type(gpu["vram_mib"]) is not int or gpu["vram_mib"] <= 0:
            raise ValueError("invalid GPU id or VRAM")
        ids.append(gpu["id"])
        version(gpu["compute_capability"])
    if len(set(ids)) != len(ids):
        raise ValueError("duplicate GPU id")
    for key in ("bundle_digest",):
        if not isinstance(workload[key], str) or not DIGEST.fullmatch(workload[key]):
            raise ValueError("missing immutable bundle digest")
    for key in ("runner", "model"):
        _required(workload[key], ("id", "version", "digest"))
        if not DIGEST.fullmatch(workload[key]["digest"]):
            raise ValueError("invalid artifact digest")
    _required(workload["image"], ("id", "cuda_major"))
    if type(workload["image"]["cuda_major"]) is not int:
        raise ValueError("image CUDA major must be explicit (0 for native)")
    if workload["image"]["id"] != "native" and not re.search(r"@sha256:[0-9a-f]{64}\Z", workload["image"]["id"]):
        raise ValueError("container image must be digest pinned")
    if workload["runtime_abi"] != "cuda-" + str(version(workload["cuda_runtime"])[0]):
        raise ValueError("runtime ABI disagrees with CUDA runtime")
    if workload["toolkit"] != "not_used":
        version(workload["toolkit"])


def evaluate(host: dict, workload: dict, matrix: dict | None = None) -> dict:
    """Return admitted/rejected/unknown; both non-admitted states block execution.

    Exact acceptance binds OS, every GPU, driver, CUDA ABI, runner, model,
    quantization, image and bundle. A new driver requires fresh acceptance, not
    rejection merely because its branch number resembles a toolkit release.
    """
    result = {"schema": "MRL_Hardware_Admission_v1", "origin_signature": ORIGIN,
              "status": "unknown", "allowed": False, "reasons": []}

    def finish(status: str, reason: str) -> dict:
        result.update(status=status, allowed=status == "admitted", reasons=[reason])
        return result

    try:
        matrix = load_matrix() if matrix is None else matrix
        if matrix["origin_signature"] != ORIGIN or matrix["schema"] != "MRL_Hardware_Matrix_v1":
            raise ValueError("matrix identity mismatch")
        _validate(host, workload)
        result["configuration_digest"] = digest({"host": host, "workload": workload})
        runtime = version(workload["cuda_runtime"])
        toolkit = None if workload["toolkit"] == "not_used" else version(workload["toolkit"])
        image_major = workload["image"]["cuda_major"]
        runner = workload["runner"]["id"].lower().replace("_", "-")
        for gpu in host["gpus"]:
            cc = version(gpu["compute_capability"])
            is_v100 = "v100" in gpu["sku"].lower()
            is_volta = gpu["architecture"].lower() == "volta" or cc[:2] in ((7, 0), (7, 2))
            if is_v100 and (gpu["vendor"] != "NVIDIA" or not is_volta or cc[:2] != (7, 0)):
                return finish("rejected", "GPU_IDENTITY_CONFLICT")
            if is_volta or is_v100:
                if runtime[0] != 12 or (toolkit and toolkit[0] != 12) or image_major not in (0, 12):
                    return finish("rejected", "VOLTA_REQUIRES_CUDA12")
                if "tensorrt" in runner and "rtx" in runner:
                    return finish("rejected", "VOLTA_FORBIDS_TENSORRT_RTX")
                if workload["quantization"].lower() in ("bf16", "fp8", "fp4"):
                    return finish("rejected", "VOLTA_PRECISION_UNSUPPORTED")
                if runner == "tensorrt" and version(workload["runner"]["version"]) >= (10, 5, 0):
                    return finish("rejected", "VOLTA_TENSORRT_VERSION_UNSUPPORTED")
                if int(host["driver"]["version"].split(".")[0]) > 580:
                    return finish("rejected", "VOLTA_DRIVER_AFTER_LAST_SUPPORTED_BRANCH")
        if host["driver"]["vendor"] != "NVIDIA" or any(g["vendor"] != "NVIDIA" for g in host["gpus"]):
            return finish("unknown", "UNTESTED_VENDOR_PATH")
        if workload["os"] != host["os"]:
            return finish("rejected", "OS_ABI_MISMATCH")
        family = host["os"]["family"]
        if runtime[0] == 12:
            minimum = {"windows": (528, 33, 0), "linux": (525, 60, 13)}.get(family)
            if minimum is None:
                return finish("unknown", "UNTESTED_OS")
            if version(host["driver"]["version"]) < minimum:
                return finish("rejected", "DRIVER_BELOW_CUDA12_MINOR_COMPATIBILITY_FLOOR")
        else:
            return finish("unknown", "CUDA_PATH_NOT_VALIDATED")
        route = next((r for r in matrix["routes"] if r["bundle_id"] == workload["bundle_id"]), None)
        if route is None:
            return finish("unknown", "UNKNOWN_BUNDLE_ROUTE")
        if route['cuda_major'] != runtime[0]:
            return finish("rejected", "BUNDLE_CUDA_ROUTE_MISMATCH")
        if any(g["architecture"] not in route["architectures"] for g in host["gpus"]):
            return finish("rejected", "BUNDLE_HARDWARE_ROUTE_MISMATCH")
        if host["observation"] != "current":
            return finish("unknown", "HISTORICAL_OBSERVATION_NOT_LIVE_ACCEPTANCE")
        # Accepted rows live in the reviewed release matrix, never in a workload
        # supplied boolean. Hashes protect identity, not evidence authenticity.
        for entry in matrix["acceptances"]:
            if (entry["bundle_id"] == workload["bundle_id"]
                    and entry["configuration_digest"] == result["configuration_digest"]
                    and entry["status"] == "passed"
                    and entry["evidence_kind"] == "real_hardware_smoke_and_restart"
                    and re.fullmatch(r"[0-9a-f]{40}", entry["source_commit"])
                    and DIGEST.fullmatch(entry["evidence_digest"])
                    and entry["evidence_ref"]):
                result["evidence_ref"] = entry["evidence_ref"]
                return finish("admitted", "EXACT_REVIEWED_HARDWARE_ACCEPTANCE")
        return finish("unknown", "NO_EXACT_HARDWARE_ACCEPTANCE")
    except (ValueError, KeyError, TypeError, AttributeError, OSError) as exc:
        return finish("unknown", "INVALID_OR_INCOMPLETE_MANIFEST: " + str(exc))


def require_admission(host: dict, workload: dict, matrix: dict | None = None) -> dict:
    """Block execution unless admission is explicitly granted."""
    result = evaluate(host, workload, matrix)
    if not result["allowed"]:
        raise AdmissionError(json.dumps(result, ensure_ascii=False))
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", required=True, type=Path)
    parser.add_argument("--workload", required=True, type=Path)
    # No caller-supplied acceptance flag or alternate matrix on production CLI.
    args = parser.parse_args()
    try:
        result = evaluate(json.loads(args.host.read_text(encoding="utf-8")),
                          json.loads(args.workload.read_text(encoding="utf-8")))
    except (OSError, ValueError) as exc:
        result = {"status": "unknown", "allowed": False, "error": str(exc), "origin_signature": ORIGIN}
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return {"admitted": 0, "rejected": 1, "unknown": 2}[result["status"]]


if __name__ == "__main__":
    raise SystemExit(main())
