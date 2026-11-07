#!/usr/bin/env python3
"""MRL-34 admission. No driver/toolkit installation or runtime mutation.

origin_signature: MrLiouWord
The matrix is trusted release policy; host/workload documents are claims to check.
Only a release-reviewed exact acceptance entry can grant admission.
"""
from __future__ import annotations

import argparse
from contextlib import contextmanager, ExitStack
import hashlib
import io
import json
import os
import re
import tempfile
from pathlib import Path
from types import MappingProxyType

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


def load_matrix(path: Path | None = None) -> dict:
    """Load release policy without contacting a remote service."""
    path = MATRIX if path is None else Path(path)
    matrix = json.loads(path.read_text(encoding="utf-8"))
    if (matrix.get("origin_signature") != ORIGIN
            or matrix.get("schema") != "MRL_Hardware_Matrix_v1"
            or not isinstance(matrix.get("routes"), list)
            or not isinstance(matrix.get("acceptances"), list)):
        raise ValueError("invalid hardware matrix")
    routes = {}
    route_digests = set()
    for route in matrix["routes"]:
        _required(route, ("bundle_id", "track", "architectures", "cuda_major"))
        if route["bundle_id"] in routes or route["track"] not in ("dl580-v100", "modern-gpu"):
            raise ValueError("duplicate or invalid hardware route")
        routes[route["bundle_id"]] = route["track"]
        route_digest = route.get("bundle_digest")
        if route_digest is not None:
            if not DIGEST.fullmatch(route_digest) or route_digest in route_digests:
                raise ValueError("hardware routes must have independent bundle digests")
            route_digests.add(route_digest)
    acceptance_ids = set()
    ownership = {}
    for acceptance in matrix["acceptances"]:
        acceptance_id = acceptance.get("acceptance_id")
        if not isinstance(acceptance_id, str) or not acceptance_id or acceptance_id in acceptance_ids:
            raise ValueError("acceptance IDs must be unique")
        acceptance_ids.add(acceptance_id)
        verify_acceptance_receipt(acceptance, path.parent)
        if routes.get(acceptance["bundle_id"]) != acceptance["track"]:
            raise ValueError("acceptance does not match its hardware route")
        for key in ("bundle_id", "bundle_digest", "evidence_digest", "acceptance_id"):
            identity = (key, acceptance[key])
            previous = ownership.setdefault(identity, acceptance["bundle_id"])
            if previous != acceptance["bundle_id"]:
                raise ValueError("cross-track acceptance reuse")
    return matrix


def _file_digest(path: Path) -> tuple[str, int]:
    before = path.lstat()
    if not path.is_file() or path.is_symlink():
        raise ValueError("artifact entry is not a regular file")
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        opened = os.fstat(stream.fileno())
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
        finished = os.fstat(stream.fileno())
    after = path.lstat()
    identity = lambda stat: (stat.st_dev, stat.st_ino, stat.st_size, stat.st_mtime_ns, stat.st_ctime_ns)
    # Compare path observations with path observations and handle observations
    # with handle observations. Windows stat/fstat timestamp precision differs;
    # comparing their entire tuples creates false mutation reports. The digest
    # still binds the opened bytes, with size equality across both observations.
    if (identity(before) != identity(after) or identity(opened) != identity(finished)
            or before.st_size != opened.st_size or after.st_size <= 0):
        raise ValueError("artifact changed while hashing")
    return "sha256:" + digest.hexdigest(), after.st_size


def artifact_digest(root: Path, relative: str) -> str:
    """Hash one file or a deterministic, complete directory file set."""
    root = Path(root).resolve(strict=True)
    relative_path = Path(relative)
    if relative_path.is_absolute() or ".." in relative_path.parts or not relative_path.parts:
        raise ValueError("artifact path must be relative to the artifact root")
    candidate = root.joinpath(relative_path)
    current = root
    for part in relative_path.parts:
        current = current / part
        if current.is_symlink():
            raise ValueError("artifact paths may not contain symlinks")
    target = candidate.resolve(strict=True)
    if target != root and root not in target.parents:
        raise ValueError("artifact path escapes its root")
    if target.is_file():
        return _file_digest(target)[0]
    if not target.is_dir():
        raise ValueError("artifact must be a regular file or directory")
    entries = []
    for path in sorted(target.rglob("*"), key=lambda item: item.relative_to(target).as_posix()):
        if path.is_symlink():
            raise ValueError("artifact directory may not contain symlinks")
        if path.is_dir():
            continue
        if not path.is_file():
            raise ValueError("artifact directory contains a non-file entry")
        digest, size = _file_digest(path)
        entries.append({"path": path.relative_to(target).as_posix(), "size": size, "sha256": digest})
    if not entries:
        raise ValueError("artifact directory is empty")
    payload = json.dumps(entries, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    return "sha256:" + hashlib.sha256(payload).hexdigest()


class _ReadOnlySnapshot(io.BufferedIOBase):
    """File-like model input without a path, writable API, or exposed descriptor."""

    def __init__(self, stream):
        self._stream = stream

    def read(self, size=-1):
        return self._stream.read(size)

    def readinto(self, buffer):
        return self._stream.readinto(buffer)

    def seek(self, offset, whence=0):
        return self._stream.seek(offset, whence)

    def tell(self):
        return self._stream.tell()

    def readable(self):
        return True

    def seekable(self):
        return True


@contextmanager
def verified_model_streams(workload: dict, artifact_root: Path, artifact_paths: dict):
    """Snapshot verified model bytes; a trusted loader must consume these streams.

    Temporary copies spill to private local disk and are closed on every exit.
    Replacing source paths cannot redirect reads. Source changes during copying
    or loading fail before any model is registered/returned. This is a loader
    contract, not a sandbox for hostile Python code or a runtime DLL loader.
    """
    verify_artifact_bytes(workload, artifact_root, artifact_paths)
    root = Path(artifact_root).resolve(strict=True)
    model_path = root / artifact_paths['model']
    is_directory = model_path.is_dir()
    paths = sorted(model_path.rglob('*')) if is_directory else [model_path]
    with ExitStack() as stack:
        streams, entries = {}, []
        for path in paths:
            if path.is_dir() and not path.is_symlink():
                continue
            name = path.relative_to(model_path).as_posix() if is_directory else '.'
            # Validate every original path, including parents, before opening.
            expected = artifact_digest(root, path.relative_to(root).as_posix())
            snapshot = stack.enter_context(tempfile.TemporaryFile(mode='w+b'))
            hasher, size = hashlib.sha256(), 0
            with path.open('rb') as source:
                for chunk in iter(lambda: source.read(1024 * 1024), b''):
                    snapshot.write(chunk)
                    hasher.update(chunk)
                    size += len(chunk)
            actual = 'sha256:' + hasher.hexdigest()
            if not size or actual != expected:
                raise AdmissionError('model changed while snapshotting')
            entries.append(dict(path=name, size=size, sha256=actual))
            snapshot.seek(0)
            streams[name] = _ReadOnlySnapshot(snapshot)
        actual_model = digest(entries) if is_directory else entries[0]['sha256']
        if actual_model != workload['model']['digest']:
            raise AdmissionError('model snapshot file set differs from manifest')
        verify_artifact_bytes(workload, root, artifact_paths)
        yield MappingProxyType(streams)
        verify_artifact_bytes(workload, root, artifact_paths)


def verify_artifact_bytes(workload: dict, artifact_root: Path, artifact_paths: dict) -> None:
    """Verify actual bundle, sharded model, runner, and runtime bytes."""
    expected = {
        "bundle": workload["bundle_digest"],
        "model": workload["model"]["digest"],
        "runner": workload["runner"]["digest"],
        "runtime": workload["runtime_binary"]["digest"],
    }
    if not isinstance(artifact_paths, dict) or set(artifact_paths) != set(expected):
        raise ValueError("artifact paths must specify bundle, model, runner, and runtime")
    for name, digest in expected.items():
        if not isinstance(artifact_paths[name], str) or not DIGEST.fullmatch(digest):
            raise ValueError("invalid artifact path or digest: " + name)
        if artifact_digest(artifact_root, artifact_paths[name]) != digest:
            raise ValueError("artifact bytes do not match manifest: " + name)


def loaded_module_paths() -> set[Path]:
    """Read this process's mapped libraries; never infer from nvidia-smi CUDA."""
    if os.name == 'nt':
        import ctypes
        from ctypes import wintypes
        psapi = ctypes.WinDLL('psapi', use_last_error=True)
        kernel = ctypes.WinDLL('kernel32', use_last_error=True)
        kernel.GetCurrentProcess.restype = wintypes.HANDLE
        process = kernel.GetCurrentProcess()
        modules = (wintypes.HMODULE * 4096)()
        needed = wintypes.DWORD()
        enum = psapi.EnumProcessModules
        enum.argtypes = (wintypes.HANDLE, ctypes.POINTER(wintypes.HMODULE),
                         wintypes.DWORD, ctypes.POINTER(wintypes.DWORD))
        filename = psapi.GetModuleFileNameExW
        filename.argtypes = (wintypes.HANDLE, wintypes.HMODULE, wintypes.LPWSTR, wintypes.DWORD)
        if not enum(process, modules, ctypes.sizeof(modules), ctypes.byref(needed)):
            raise ValueError('cannot inspect mapped runtime modules')
        if needed.value > ctypes.sizeof(modules):
            raise ValueError('mapped runtime module inventory truncated')
        result = set()
        for module in modules[:needed.value // ctypes.sizeof(wintypes.HMODULE)]:
            buffer = ctypes.create_unicode_buffer(32768)
            length = filename(process, module, buffer, len(buffer))
            if not length or length >= len(buffer):
                raise ValueError('cannot resolve mapped runtime module')
            result.add(Path(buffer.value).resolve(strict=True))
        return result
    maps = Path('/proc/self/maps')
    if not maps.is_file():
        raise ValueError('no trusted loaded-runtime inspection adapter for this OS')
    result = set()
    for line in maps.read_text(encoding='utf-8').splitlines():
        fields = line.split(None, 5)
        if len(fields) == 6 and fields[5].startswith('/'):
            if fields[5].endswith(' (deleted)'):
                raise ValueError('process contains replaced/deleted mapped modules')
            result.add(Path(fields[5]).resolve(strict=True))
    return result


def verify_loaded_process_artifacts(workload, artifact_root, artifact_paths, runner_module):
    """Bind the native PyTorch process to the verified runner and mapped runtime.

    Container image/platform attestation and external runners need their own
    reviewed adapter; a digest-pinned claim alone cannot identify this process.
    """
    if workload['runner']['id'].lower() != 'pytorch' or workload['image']['id'] != 'native':
        raise ValueError('live runner/image adapter is UNKNOWN for this workload')
    root = Path(artifact_root).resolve(strict=True)
    verify_artifact_bytes(workload, root, artifact_paths)
    runner = (root / artifact_paths['runner']).resolve(strict=True)
    actual_runner = Path(runner_module.__file__).resolve(strict=True)
    if actual_runner != runner and not (runner.is_dir() and runner in actual_runner.parents):
        raise ValueError('imported runner is outside the verified runner artifact')
    runtime = (root / artifact_paths['runtime']).resolve(strict=True)
    mapped = {path.resolve(strict=True) for path in loaded_module_paths()}
    if not runtime.is_file() or runtime not in mapped:
        raise ValueError('verified CUDA runtime binary is not mapped in this process')
    if (runner_module.__version__ != workload['runner']['version']
            or runner_module.version.cuda != workload['cuda_runtime']):
        raise ValueError('loaded PyTorch version or CUDA ABI differs from workload')
    verify_artifact_bytes(workload, root, artifact_paths)


def verify_acceptance_receipt(acceptance: dict, evidence_root: Path) -> dict:
    """Verify exact real-hardware receipt bytes before using a registry row."""
    required = ("bundle_id", "configuration_digest", "status", "evidence_kind",
                "source_commit", "evidence_digest", "evidence_ref", "receipt_path",
                "acceptance_id", "track", "bundle_digest")
    _required(acceptance, required)
    if (acceptance["status"] != "passed"
            or acceptance["evidence_kind"] != "real_hardware_smoke_and_restart"
            or not re.fullmatch(r"[0-9a-f]{40}", acceptance["source_commit"])
            or not DIGEST.fullmatch(acceptance["evidence_digest"])
            or not DIGEST.fullmatch(acceptance["bundle_digest"])
            or not DIGEST.fullmatch(acceptance["configuration_digest"])):
        raise ValueError("acceptance is not an exact real-hardware record")
    relative = Path(acceptance["receipt_path"])
    if relative.is_absolute() or ".." in relative.parts:
        raise ValueError("receipt path must be relative to the matrix")
    root = evidence_root.resolve()
    candidate = root
    for part in relative.parts:
        candidate = candidate / part
        if candidate.is_symlink():
            raise ValueError("receipt path may not contain symlinks")
    path = candidate.resolve(strict=True)
    if path == root or root not in path.parents:
        raise ValueError("receipt must remain within the matrix directory")
    raw = path.read_bytes()
    if "sha256:" + hashlib.sha256(raw).hexdigest() != acceptance["evidence_digest"]:
        raise ValueError("acceptance receipt digest mismatch")
    receipt = json.loads(raw)
    expected_checks = {'device_query', 'runtime_smoke', 'model_smoke', 'restart_smoke'}
    checks = receipt.get('checks')
    if (receipt.get("origin_signature") != ORIGIN
            or receipt.get("status") != "hardware_verified"
            or receipt.get("acceptance_id") != acceptance["acceptance_id"]
            or receipt.get("configuration_digest") != acceptance["configuration_digest"]
            or any(receipt.get(key) != acceptance[key]
                   for key in ('bundle_id', 'bundle_digest', 'track', 'source_commit'))
            or not isinstance(checks, dict) or set(checks) != expected_checks
            or any(value is not True for value in checks.values())
            or not receipt.get("source")):
        raise ValueError("incomplete or failed hardware acceptance receipt")
    rollback = receipt.get('rollback')
    if not isinstance(rollback, dict) or set(rollback) != {'before', 'forward', 'return'}:
        raise ValueError('hardware acceptance requires a verified rollback chain')
    rollback_receipts = []
    for phase in ('before', 'forward', 'return'):
        relative = Path(rollback[phase])
        if relative.is_absolute() or '..' in relative.parts:
            raise ValueError('rollback path must remain inside the matrix directory')
        target = root
        for part in relative.parts:
            target = target / part
            if target.is_symlink():
                raise ValueError('rollback receipt may not contain symlinks')
        target = target.resolve(strict=True)
        if root not in target.parents:
            raise ValueError('rollback path escapes matrix directory')
        rollback_receipts.append(json.loads(target.read_text(encoding='utf-8')))
    if __package__:
        from .MRL_reversible_change_v1 import verify_roundtrip
    else:
        from MRL_reversible_change_v1 import verify_roundtrip
    roundtrip = verify_roundtrip(*rollback_receipts, evidence_root=root)
    if receipt.get('change_id') != roundtrip['change_id']:
        raise ValueError('hardware acceptance and rollback change_id differ')
    return receipt


def _required(obj: dict, fields: tuple[str, ...]) -> None:
    if not isinstance(obj, dict) or any(obj.get(key) in (None, "", []) for key in fields):
        raise ValueError("missing manifest field: " + ",".join(fields))
    if any(isinstance(obj[key], str) and obj[key].strip().lower() in
           ('unknown', 'unverified', 'review_required', 'n/a') for key in fields):
        raise ValueError('unknown manifest field: ' + ','.join(fields))


def _validate(host: dict, workload: dict) -> None:
    _required(host, ("schema", "origin_signature", "os", "driver", "gpus", "observation",
                     "loaded_runner", "loaded_runtime", "loaded_image"))
    _required(workload, ("schema", "origin_signature", "source_commit", "track", "gpu_ids",
                         "bundle_id", "bundle_digest", "os",
                         "cuda_runtime", "runtime_abi", "toolkit", "runner", "model",
                         "runtime_binary", "quantization", "image"))
    if host["schema"] != "MRL_Hardware_Manifest_v1" or workload["schema"] != "MRL_Workload_Manifest_v1":
        raise ValueError("schema mismatch")
    if host["origin_signature"] != ORIGIN or workload["origin_signature"] != ORIGIN:
        raise ValueError("origin mismatch")
    _required(host["os"], ("family", "version", "arch"))
    _required(host["driver"], ("vendor", "version"))
    version(host["driver"]["version"])
    if not isinstance(host["gpus"], list) or not host["gpus"]:
        raise ValueError("empty GPU inventory")
    if (not isinstance(workload["gpu_ids"], list) or not workload["gpu_ids"]
            or any(type(gpu_id) is not int or gpu_id < 0 for gpu_id in workload["gpu_ids"])
            or len(set(workload["gpu_ids"])) != len(workload["gpu_ids"])):
        raise ValueError("invalid workload GPU selection")
    ids = []
    for gpu in host["gpus"]:
        _required(gpu, ("id", "uuid", "vendor", "architecture", "sku", "compute_capability", "vram_mib"))
        if type(gpu["id"]) is not int or gpu["id"] < 0 or type(gpu["vram_mib"]) is not int or gpu["vram_mib"] <= 0:
            raise ValueError("invalid GPU id or VRAM")
        ids.append(gpu["id"])
        version(gpu["compute_capability"])
    if len(set(ids)) != len(ids) or len({g['uuid'] for g in host['gpus']}) != len(ids):
        raise ValueError("duplicate GPU id")
    if not set(workload['gpu_ids']).issubset(ids):
        raise ValueError('selected GPU is absent from inventory')
    for key in ("bundle_digest",):
        if not isinstance(workload[key], str) or not DIGEST.fullmatch(workload[key]):
            raise ValueError("missing immutable bundle digest")
    for key in ("runner", "model"):
        _required(workload[key], ("id", "version", "digest"))
        if not DIGEST.fullmatch(workload[key]["digest"]):
            raise ValueError("invalid artifact digest")
    _required(workload["runtime_binary"], ("id", "version", "digest"))
    version(workload["runtime_binary"]["version"])
    if not DIGEST.fullmatch(workload["runtime_binary"]["digest"]):
        raise ValueError("invalid runtime artifact digest")
    _required(workload["image"], ("id", "cuda_major"))
    if type(workload["image"]["cuda_major"]) is not int:
        raise ValueError("image CUDA major must be explicit (0 for native)")
    if workload["image"]["id"] != "native" and not re.search(r"@sha256:[0-9a-f]{64}\Z", workload["image"]["id"]):
        raise ValueError("container image must be digest pinned")
    if workload["image"]["id"] == "native" and workload["image"]["cuda_major"] != 0:
        raise ValueError("native workloads must use image CUDA major 0")
    if workload["runtime_abi"] != "cuda-" + str(version(workload["cuda_runtime"])[0]):
        raise ValueError("runtime ABI disagrees with CUDA runtime")
    if version(workload['runtime_binary']['version']) != version(workload['cuda_runtime']):
        raise ValueError('runtime binary version disagrees with loaded CUDA runtime')
    if workload["track"] not in ("dl580-v100", "modern-gpu"):
        raise ValueError("unknown hardware track")
    if not re.fullmatch(r"[0-9a-f]{40}", workload["source_commit"]):
        raise ValueError("workload source commit must be an exact Git SHA")
    _required(host["loaded_runner"], ("id", "version", "digest"))
    _required(host["loaded_runtime"], ("id", "version", "digest"))
    for runtime in (host["loaded_runner"], host["loaded_runtime"]):
        if not DIGEST.fullmatch(runtime["digest"]):
            raise ValueError("invalid loaded runtime digest")
    if workload["toolkit"] != "not_used":
        version(workload["toolkit"])


def evaluate(host: dict, workload: dict, artifact_root: Path, artifact_paths: dict) -> dict:
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
        matrix = load_matrix()
        if matrix["origin_signature"] != ORIGIN or matrix["schema"] != "MRL_Hardware_Matrix_v1":
            raise ValueError("matrix identity mismatch")
        _validate(host, workload)
        verify_artifact_bytes(workload, artifact_root, artifact_paths)
        result["configuration_digest"] = digest({"host": host, "workload": workload})
        runtime = version(workload["cuda_runtime"])
        toolkit = None if workload["toolkit"] == "not_used" else version(workload["toolkit"])
        image_major = workload["image"]["cuda_major"]
        runner = workload["runner"]["id"].lower().replace("_", "-")
        for gpu in host["gpus"]:
            cc = version(gpu["compute_capability"])
            is_v100 = "v100" in gpu["sku"].lower()
            is_volta = gpu["architecture"].lower() == "volta" or cc[:2] in ((7, 0), (7, 2))
            if (is_volta and (gpu['vendor'] != 'NVIDIA'
                              or gpu['architecture'] != 'Volta'
                              or cc[:2] not in ((7, 0), (7, 2)))):
                return finish('rejected', 'GPU_IDENTITY_CONFLICT')
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
        if (workload["image"]["id"] != "native"
                and image_major != runtime[0]):
            return finish("rejected", "BUNDLE_CUDA_ROUTE_MISMATCH")
        if host["loaded_runner"] != workload["runner"]:
            raise ValueError("loaded runner differs from the workload")
        if host["loaded_runtime"] != workload["runtime_binary"]:
            raise ValueError("loaded runtime differs from the workload")
        if host["loaded_image"] != workload["image"]["id"]:
            raise ValueError("loaded image differs from the workload")
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
        if route.get("track") != workload["track"]:
            return finish("rejected", "BUNDLE_TRACK_MISMATCH")
        if (route.get('bundle_digest') is not None
                and route['bundle_digest'] != workload['bundle_digest']):
            return finish('rejected', 'BUNDLE_DIGEST_ROUTE_MISMATCH')
        if workload['track'] == 'dl580-v100' and any(
                'v100' not in g['sku'].lower() or g['compute_capability'] != '7.0'
                for g in host['gpus']):
            return finish('rejected', 'NON_V100_IN_DL580_TRACK')
        if any(g["architecture"] not in route["architectures"] for g in host["gpus"]):
            return finish("rejected", "BUNDLE_HARDWARE_ROUTE_MISMATCH")
        if host["observation"] != "current":
            return finish("unknown", "HISTORICAL_OBSERVATION_NOT_LIVE_ACCEPTANCE")
        # Accepted rows live in the reviewed release matrix, never in a workload
        # supplied boolean. Hashes protect identity, not evidence authenticity.
        for entry in matrix["acceptances"]:
            if (entry["bundle_id"] == workload["bundle_id"]
                    and entry["track"] == workload["track"]
                    and entry['bundle_digest'] == workload['bundle_digest']
                    and entry["source_commit"] == workload["source_commit"]
                    and entry["configuration_digest"] == result["configuration_digest"]
                    and entry["status"] == "passed"
                    and entry["evidence_kind"] == "real_hardware_smoke_and_restart"
                    and re.fullmatch(r"[0-9a-f]{40}", entry["source_commit"])
                    and entry["evidence_ref"]):
                verify_acceptance_receipt(entry, MATRIX.parent)
                result["evidence_ref"] = entry["evidence_ref"]
                return finish("admitted", "EXACT_REVIEWED_HARDWARE_ACCEPTANCE")
        return finish("unknown", "NO_EXACT_HARDWARE_ACCEPTANCE")
    except (ValueError, KeyError, TypeError, AttributeError, OSError) as exc:
        return finish("unknown", "INVALID_OR_INCOMPLETE_MANIFEST: " + str(exc))


def require_admission(host: dict, workload: dict, artifact_root: Path, artifact_paths: dict) -> dict:
    """Block execution unless admission is explicitly granted."""
    result = evaluate(host, workload, artifact_root, artifact_paths)
    if not result["allowed"]:
        raise AdmissionError(json.dumps(result, ensure_ascii=False))
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", required=True, type=Path)
    parser.add_argument("--workload", required=True, type=Path)
    parser.add_argument("--artifact-root", required=True, type=Path)
    parser.add_argument("--artifact-paths", required=True, type=Path)
    args = parser.parse_args(argv)
    try:
        result = evaluate(json.loads(args.host.read_text(encoding="utf-8")),
                          json.loads(args.workload.read_text(encoding="utf-8")),
                          args.artifact_root,
                          json.loads(args.artifact_paths.read_text(encoding="utf-8")))
    except (OSError, ValueError) as exc:
        result = {"status": "unknown", "allowed": False, "error": str(exc), "origin_signature": ORIGIN}
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return {"admitted": 0, "rejected": 1, "unknown": 2}[result["status"]]


if __name__ == "__main__":
    raise SystemExit(main())
