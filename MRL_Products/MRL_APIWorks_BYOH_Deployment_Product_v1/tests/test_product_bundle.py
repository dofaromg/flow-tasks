#!/usr/bin/env python3
"""Product packaging acceptance tests."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
BUNDLE_ROOT_NAME = "MRL_APIWorks_BYOH_Deployment_Product_v1"
RUNTIME_RELATIVE = Path(
    "MRL_Mother/MRL_MotherModel/MRL_AI_Mother_Autonomous_Runtime_Baseline_v1"
)
PRODUCT_RELATIVE = Path("MRL_Products/MRL_APIWorks_BYOH_Deployment_Product_v1")
MUTABLE_CONFIG = Path("customer_config/MRL_runtime.local.json")


class ProductBundleTests(unittest.TestCase):
    def test_rejects_corrupted_zip_output(self) -> None:
        """A write that changes payload bytes must fail the final readback."""
        spec = importlib.util.spec_from_file_location(
            "product_builder", ROOT / "scripts/MRL_build_product_bundle_v1.py"
        )
        builder = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(builder)

        class CorruptingZipFile(zipfile.ZipFile):
            def writestr(self, zinfo_or_arcname, data, *args, **kwargs):
                name = getattr(zinfo_or_arcname, "filename", zinfo_or_arcname)
                if name.endswith("docs/MRL_SUPPORT_SCOPE_v1.md"):
                    data = b"CORRUPTED_ZIP_PAYLOAD\n"
                return super().writestr(zinfo_or_arcname, data, *args, **kwargs)

        with tempfile.TemporaryDirectory() as temporary:
            with mock.patch.object(builder, "DIST", Path(temporary)), mock.patch.object(
                builder.zipfile, "ZipFile", CorruptingZipFile
            ):
                with self.assertRaisesRegex(ValueError, "customer ZIP content mismatch"):
                    builder.main()

    def test_bundle_is_reproducible_across_source_mtimes(self) -> None:
        """A new checkout's filesystem timestamps must not change delivery SHA."""
        with tempfile.TemporaryDirectory() as temporary:
            repository = Path(temporary)
            for relative in (PRODUCT_RELATIVE, RUNTIME_RELATIVE):
                shutil.copytree(ROOT.parents[1] / relative, repository / relative,
                                ignore=shutil.ignore_patterns("dist", "__pycache__"))
            product = repository / PRODUCT_RELATIVE
            bundle = product / "dist" / f"{BUNDLE_ROOT_NAME}.zip"
            hashes = []
            for timestamp in (946684800, 1735689600):
                for relative in (PRODUCT_RELATIVE, RUNTIME_RELATIVE):
                    for path in (repository / relative).rglob("*"):
                        if path.is_file() and "dist" not in path.parts:
                            os.utime(path, (timestamp, timestamp))
                subprocess.run([sys.executable, "scripts/MRL_build_product_bundle_v1.py"],
                               cwd=product, capture_output=True, text=True, check=True)
                hashes.append(hashlib.sha256(bundle.read_bytes()).hexdigest())
                self.assertEqual(bundle.with_suffix(".zip.sha256").read_text(),
                                 f"{hashes[-1]}  {bundle.name}\n")
            self.assertEqual(hashes[0], hashes[1])

    def test_rejects_invalid_product_source_before_build(self) -> None:
        """Tampered, extra, missing and empty product files must never earn PASS."""
        for case in ("tampered", "extra", "missing", "empty"):
            with self.subTest(case=case), tempfile.TemporaryDirectory() as temporary:
                repository = Path(temporary)
                product = repository / PRODUCT_RELATIVE
                for relative in (PRODUCT_RELATIVE, RUNTIME_RELATIVE):
                    shutil.copytree(
                        ROOT.parents[1] / relative, repository / relative,
                        ignore=shutil.ignore_patterns("dist", "__pycache__"),
                    )
                target = product / "docs/MRL_SUPPORT_SCOPE_v1.md"
                if case == "tampered":
                    target.write_text("CORRUPTION_REPRODUCTION_ONLY\n", encoding="utf-8")
                elif case == "extra":
                    (product / "unexpected.txt").write_text("unexpected file\n", encoding="utf-8")
                elif case == "missing":
                    target.unlink()
                else:
                    target.write_bytes(b"")
                result = subprocess.run(
                    [sys.executable, "scripts/MRL_build_product_bundle_v1.py"],
                    cwd=product, capture_output=True, text=True, check=False,
                )
                self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
                self.assertNotIn("PRODUCT_BUNDLE_DELIVERY_PASS", result.stdout)
                self.assertFalse((product / "dist" / f"{BUNDLE_ROOT_NAME}.zip").exists())

    def test_builds_runnable_customer_zip(self) -> None:
        """Exercise extraction, mutable configuration, and both package verifiers."""
        subprocess.run(["python", "scripts/MRL_build_product_bundle_v1.py"], cwd=ROOT, check=True)
        bundle = ROOT / "dist" / f"{BUNDLE_ROOT_NAME}.zip"
        self.assertTrue(bundle.is_file())
        with tempfile.TemporaryDirectory() as temporary:
            extraction_root = Path(temporary)
            with zipfile.ZipFile(bundle) as archive:
                names = set(archive.namelist())
                self.assertEqual(len(names), len(archive.namelist()))
                prefix = f"{BUNDLE_ROOT_NAME}/"
                self.assertTrue(names)
                self.assertTrue(all(name.startswith(prefix) for name in names))
                manifest = json.loads(archive.read(prefix + "MRL_PRODUCT_BUNDLE_MANIFEST.json"))
                for item in manifest["files"]:
                    data = archive.read(prefix + item["path"])
                    self.assertTrue(data)
                    self.assertEqual(len(data), item["size"])
                    self.assertEqual(hashlib.sha256(data).hexdigest(), item["sha256"])
                archive.extractall(extraction_root)

            delivery_root = extraction_root / BUNDLE_ROOT_NAME
            manifest = json.loads((delivery_root / "MRL_PRODUCT_BUNDLE_MANIFEST.json").read_text(encoding="utf-8"))
            expected = {f"{prefix}{item['path']}" for item in manifest["files"]}
            self.assertEqual(names - {f"{prefix}MRL_PRODUCT_BUNDLE_MANIFEST.json"}, expected)
            self.assertEqual(manifest["archive_root"], BUNDLE_ROOT_NAME)
            self.assertEqual(manifest["mutable_after_extraction"], [MUTABLE_CONFIG.as_posix()])
            mutable_entry = next(item for item in manifest["files"] if item["path"] == MUTABLE_CONFIG.as_posix())
            self.assertTrue(mutable_entry["mutable_after_extraction"])

            runtime_root = delivery_root / RUNTIME_RELATIVE
            product_root = delivery_root / PRODUCT_RELATIVE
            self.assertTrue((runtime_root / "runtime" / "MRL_apiworks_gateway_v1.py").is_file())
            self.assertTrue((product_root / "scripts" / "MRL_build_product_bundle_v1.py").is_file())

            customer_config = delivery_root / MUTABLE_CONFIG
            config = json.loads(customer_config.read_text(encoding="utf-8"))
            config["local_model"]["model"] = "customer-owned-model"
            customer_config.write_text(json.dumps(config, indent=2) + "\n", encoding="utf-8")

            subprocess.run(["python", "scripts/MRL_verify_package_v1.py"], cwd=runtime_root, check=True)
            subprocess.run(["python", "scripts/MRL_verify_product_source_v1.py"], cwd=product_root, check=True)

            config_from_start_script = (
                runtime_root / "scripts" / ".." / ".." / ".." / ".." / MUTABLE_CONFIG
            ).resolve()
            self.assertEqual(config_from_start_script, customer_config.resolve())

            acceptance = (product_root / "docs" / "MRL_DELIVERY_ACCEPTANCE_v1.md").read_text(encoding="utf-8")
            self.assertIn("-ConfigPath", acceptance)
            self.assertIn(r"..\..\..\..\customer_config\MRL_runtime.local.json", acceptance)
            self.assertEqual(manifest["origin_signature"], "MrLiouWord")


if __name__ == "__main__":
    unittest.main()
