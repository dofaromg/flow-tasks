#!/usr/bin/env python3
"""Build the audited customer delivery ZIP for the MRL APIWorks BYOH product."""

from __future__ import annotations

import hashlib
import json
import shutil
import subprocess
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
        ["python", str(RUNTIME_ROOT / "scripts" / "MRL_verify_package_v1.py")],
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
                archive.write(path, path.relative_to(stage.parent).as_posix())
    print(json.dumps({"delivery_gate": "PRODUCT_BUNDLE_DELIVERY_PASS", "path": str(output), "sha256": sha256(output)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
