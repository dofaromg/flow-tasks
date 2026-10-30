#!/usr/bin/env python3
"""Build the audited customer delivery ZIP for the MRL APIWorks BYOH product."""

from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

PRODUCT_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = PRODUCT_ROOT.parents[1]
RUNTIME_RELATIVE = Path(
    "MRL_Mother/MRL_MotherModel/MRL_AI_Mother_Autonomous_Runtime_Baseline_v1"
)
PRODUCT_RELATIVE = Path("MRL_Products/MRL_APIWorks_BYOH_Deployment_Product_v1")
RUNTIME_ROOT = REPO_ROOT / RUNTIME_RELATIVE
DIST = PRODUCT_ROOT / "dist"
BUNDLE_ROOT_NAME = "MRL_APIWorks_BYOH_Deployment_Product_v1"
MANIFEST_NAME = "MRL_PRODUCT_BUNDLE_MANIFEST.json"
MUTABLE_CONFIG = Path("customer_config/MRL_runtime.local.json")


def sha256(path: Path) -> str:
    """Return the lowercase SHA-256 digest for a file."""
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def files_under(root: Path) -> list[Path]:
    """List reproducible bundle inputs while excluding generated output."""
    return sorted(
        path for path in root.rglob("*")
        if path.is_file() and "__pycache__" not in path.parts and "dist" not in path.parts
    )


def main() -> int:
    """Verify source packages and create a repository-shaped customer bundle."""
    subprocess.run(
        [sys.executable, str(PRODUCT_ROOT / "scripts" / "MRL_verify_product_source_v1.py")],
        cwd=PRODUCT_ROOT,
        check=True,
    )
    subprocess.run(
        [sys.executable, str(RUNTIME_ROOT / "scripts" / "MRL_verify_package_v1.py")],
        cwd=RUNTIME_ROOT,
        check=True,
    )
    DIST.mkdir(parents=True, exist_ok=True)
    output = DIST / f"{BUNDLE_ROOT_NAME}.zip"
    with tempfile.TemporaryDirectory() as temporary:
        stage = Path(temporary) / BUNDLE_ROOT_NAME
        runtime_target = stage / RUNTIME_RELATIVE
        product_target = stage / PRODUCT_RELATIVE
        shutil.copytree(RUNTIME_ROOT, runtime_target, ignore=shutil.ignore_patterns("__pycache__"))
        shutil.copytree(PRODUCT_ROOT, product_target, ignore=shutil.ignore_patterns("dist", "__pycache__"))

        mutable_config_target = stage / MUTABLE_CONFIG
        mutable_config_target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(
            runtime_target / "config" / "MRL_runtime.local.example.json",
            mutable_config_target,
        )

        entries = []
        for path in files_under(stage):
            name = path.relative_to(stage).as_posix()
            entries.append({
                "path": name,
                "size": path.stat().st_size,
                "sha256": sha256(path),
                "mutable_after_extraction": name == MUTABLE_CONFIG.as_posix(),
            })
        manifest = {
            "schema": "MRL_Product_Bundle_Manifest_v1",
            "canonical_id": "MRL_APIWorks_BYOH_Deployment_Product_v1",
            "sku": "MRL-APIWORKS-BYOH-DEPLOY-V1",
            "origin_signature": "MrLiouWord",
            "archive_root": BUNDLE_ROOT_NAME,
            "mutable_after_extraction": [MUTABLE_CONFIG.as_posix()],
            "files": entries,
        }
        (stage / MANIFEST_NAME).write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
        with zipfile.ZipFile(output, "w", zipfile.ZIP_DEFLATED) as archive:
            for path in files_under(stage):
                # Filesystem mtimes and host permissions are not product identity.
                # Keep source timestamps in Git; normalize only ZIP metadata.
                info = zipfile.ZipInfo(path.relative_to(stage.parent).as_posix(),
                                       date_time=(1980, 1, 1, 0, 0, 0))
                info.create_system = 3
                info.external_attr = 0o100644 << 16
                info.compress_type = zipfile.ZIP_DEFLATED
                archive.writestr(info, path.read_bytes())
        # Read the persisted ZIP before asserting PASS, including the manifest.
        prefix = f"{BUNDLE_ROOT_NAME}/"
        expected_names = {prefix + item["path"] for item in entries} | {prefix + MANIFEST_NAME}
        with zipfile.ZipFile(output) as archive:
            names = archive.namelist()
            if len(names) != len(set(names)) or set(names) != expected_names:
                raise ValueError("customer ZIP file coverage mismatch")
            if archive.read(prefix + MANIFEST_NAME) != (stage / MANIFEST_NAME).read_bytes():
                raise ValueError("customer ZIP manifest mismatch")
            for item in entries:
                data = archive.read(prefix + item["path"])
                if len(data) != item["size"] or hashlib.sha256(data).hexdigest() != item["sha256"]:
                    raise ValueError("customer ZIP content mismatch: " + item["path"])
    checksum = sha256(output)
    checksum_path = output.with_suffix(".zip.sha256")
    checksum_path.write_text(f"{checksum}  {output.name}\n", encoding="utf-8")
    if checksum_path.read_text(encoding="utf-8") != f"{checksum}  {output.name}\n":
        raise ValueError("customer ZIP checksum sidecar readback mismatch")
    print(json.dumps({"delivery_gate": "PRODUCT_BUNDLE_DELIVERY_PASS", "path": str(output),
                      "sha256": checksum, "checksum_path": str(checksum_path)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
