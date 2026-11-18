"""Package-integrity regressions. Fixture wheels are never release artifacts."""

import hashlib
import json
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch
import zipfile

from .bootstrap import runtime_match, verify
from .build_package import SOURCE_FILES, build


class DeliveryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.source = Path(__file__).resolve().parents[4]
        self.wheels = self.root / "wheels"
        self.wheels.mkdir()
        # Only metadata/CRC fixture wheels for format tests. Integration CI uses
        # pip-downloaded real wheels and installs the resulting archive offline.
        for name, version in (("cryptography", "50.0.2"), ("eth_account", "0.14.0")):
            path = self.wheels / f"{name}-{version}-py3-none-any.whl"
            with zipfile.ZipFile(path, "w") as wheel:
                wheel.writestr(f"{name}-{version}.dist-info/METADATA",
                               f"Metadata-Version: 2.1\nName: {name}\nVersion: {version}\n")
        self.output = self.root / "MRL_fixture_only.zip"

    def package(self, source=None):
        return build(source or self.source, self.wheels, self.output, "Linux", "a" * 40,
                     "WORKSPACE_SNAPSHOT")

    def extract(self):
        self.package()
        directory = self.root / "unpacked"
        with zipfile.ZipFile(self.output) as archive:
            archive.extractall(directory)
        return directory

    def test_archive_crc_count_hashes_and_source_paths(self):
        result = self.package()
        with zipfile.ZipFile(self.output) as archive:
            self.assertIsNone(archive.testzip())
            manifest = json.loads(archive.read("PACKAGE_MANIFEST.json"))
            self.assertEqual(len(archive.namelist()), manifest["expected_file_count"])
            self.assertEqual(set(SOURCE_FILES) - set(archive.namelist()), set())
            for item in manifest["files"]:
                self.assertEqual(hashlib.sha256(archive.read(item["path"])).hexdigest(), item["sha256"])
        self.assertEqual(result["sha256"], hashlib.sha256(self.output.read_bytes()).hexdigest())
        self.assertEqual(result["coverage"], 100)

    def test_changed_source_is_rejected(self):
        directory = self.extract()
        (directory / SOURCE_FILES[1]).write_bytes(b"changed source")
        with self.assertRaisesRegex(ValueError, "HASH_OR_SIZE"):
            verify(directory)

    def test_missing_dependency_is_rejected(self):
        directory = self.extract()
        next((directory / "wheelhouse").glob("*.whl")).unlink()
        with self.assertRaisesRegex(ValueError, "MISSING"):
            verify(directory)

    def test_unexpected_private_file_is_rejected(self):
        directory = self.extract()
        (directory / "operator-private.json").write_text('{"fixture":true}', encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "FILE_SET"):
            verify(directory)

    def test_case_colliding_paths_are_rejected(self):
        directory = self.extract()
        path = directory / "PACKAGE_MANIFEST.json"
        manifest = json.loads(path.read_text(encoding="utf-8"))
        entry = dict(manifest["files"][0])
        entry["path"] = entry["path"].upper()
        manifest["files"].append(entry)
        path.write_text(json.dumps(manifest), encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "DUPLICATE"):
            verify(directory)

    def test_parent_escape_path_is_rejected(self):
        directory = self.extract()
        path = directory / "PACKAGE_MANIFEST.json"
        manifest = json.loads(path.read_text(encoding="utf-8"))
        manifest["files"][0]["path"] = "../outside"
        path.write_text(json.dumps(manifest), encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "UNSAFE"):
            verify(directory)

    def test_builder_requires_actual_source_dependencies(self):
        source = self.root / "source"
        for name in SOURCE_FILES:
            target = source / name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(self.source / name, target)
        (source / SOURCE_FILES[1]).unlink()
        with self.assertRaisesRegex(ValueError, "SOURCE_FILE_MISSING"):
            self.package(source)

    def test_lock_covers_every_bundled_wheel(self):
        self.package()
        with zipfile.ZipFile(self.output) as archive:
            lock = archive.read("requirements.lock").decode("utf-8")
            self.assertIn("cryptography==50.0.2 --hash=sha256:", lock)
            self.assertIn("eth-account==0.14.0 --hash=sha256:", lock)
            self.assertEqual(len(lock.splitlines()), 2)

    def test_existing_output_is_preserved(self):
        self.output.write_bytes(b"original archive")
        with self.assertRaises(FileExistsError):
            self.package()
        self.assertEqual(self.output.read_bytes(), b"original archive")

    def test_wrong_platform_is_rejected(self):
        with patch("platform.system", return_value="Windows"):
            with self.assertRaisesRegex(ValueError, "PLATFORM_MISMATCH"):
                runtime_match({"python": "3.12", "target_os": "Linux"})


if __name__ == "__main__":
    unittest.main()
