"""Adversarial integrity tests for the private APIWorks evidence entrance."""

from __future__ import annotations

import json
import os
import sys
import tempfile
import unittest
import warnings
import zipfile
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))
from Mrliou_MRL_verify_evidence_entry_v1 import (  # noqa: E402
    BUNDLE, MANIFEST, MUTABLE, PRODUCT, digest, safe_name, verify_directory, verify_zip,
)
from Mrliou_MRL_build_evidence_entry_v1 import build, content_mappings  # noqa: E402


class EvidenceEntryTests(unittest.TestCase):
    """Use temporary synthetic bytes, never customer or private source data."""

    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.data = {"runtime.txt": b"runtime fixture\n", MUTABLE: b"{}\n"}
        self.expected = {
            name: {"size_bytes": len(data), "sha256": digest(data)}
            for name, data in self.data.items()
        }

    def make_zip(self, mutation: str = "") -> Path:
        """Build a controlled valid or corrupted ZIP without extraction."""
        manifest = {
            "archive_root": PRODUCT, "canonical_id": PRODUCT,
            "sku": "MRL-APIWORKS-BYOH-DEPLOY-V1", "origin_signature": "MrLiouWord",
            "mutable_after_extraction": [MUTABLE],
            "files": [{"path": name, "size": len(data), "sha256": digest(data),
                       "mutable_after_extraction": name == MUTABLE}
                      for name, data in self.data.items()],
        }
        if mutation == "identity":
            manifest["canonical_id"] = "other"
        if mutation == "mutable":
            manifest["files"][0]["mutable_after_extraction"] = True
        if mutation == "manifest_duplicate":
            manifest["files"].append(manifest["files"][0])
        if mutation == "lying_manifest":
            manifest["files"][0]["size"] = 7
            manifest["files"][0]["sha256"] = digest(b"changed")
        path = self.root / BUNDLE
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", UserWarning)
            with zipfile.ZipFile(path, "w") as archive:
                archive.writestr(PRODUCT + "/" + MANIFEST, json.dumps(manifest))
                for name, data in self.data.items():
                    if mutation == "missing" and name == "runtime.txt":
                        continue
                    if mutation in {"tamper", "lying_manifest"} and name == "runtime.txt":
                        data = b"changed"
                    archive.writestr(PRODUCT + "/" + name, data)
                if mutation == "extra":
                    archive.writestr(PRODUCT + "/extra.txt", "extra")
                if mutation == "duplicate":
                    archive.writestr(PRODUCT + "/runtime.txt", "duplicate")
                if mutation == "traversal":
                    archive.writestr(PRODUCT + "/../escape.txt", "escape")
                if mutation == "symlink":
                    item = zipfile.ZipInfo(PRODUCT + "/link")
                    item.create_system = 3
                    item.external_attr = 0o120777 << 16
                    archive.writestr(item, "/private/target")
        return path

    def make_entry(self) -> None:
        """Create a minimal internally consistent review fixture."""
        path = self.make_zip()
        (self.root / "SOURCE_INVENTORY.json").write_text("{}\n")
        (self.root / "EXPECTED_PRODUCT_FILES.json").write_text(json.dumps(self.expected))
        blob = path.read_bytes()
        (self.root / "EVIDENCE_LEDGER.json").write_text(json.dumps({
            "artifact": {"path": BUNDLE, "size_bytes": len(blob), "sha256": digest(blob)},
        }))
        names = sorted([p.name for p in self.root.iterdir()] + ["Expected_File_List.txt", "SHA256SUMS.txt"])
        (self.root / "Expected_File_List.txt").write_text("\n".join(names) + "\n")
        self.seal()

    def seal(self) -> None:
        """Refresh fixture checksums to test deeper, independent constraints."""
        names = (self.root / "Expected_File_List.txt").read_text().splitlines()
        (self.root / "SHA256SUMS.txt").write_text("\n".join(
            digest((self.root / name).read_bytes()) + "  " + name
            for name in names if name != "SHA256SUMS.txt") + "\n")

    def test_valid_zip(self) -> None:
        self.assertEqual(verify_zip(self.make_zip(), self.expected), [])

    def test_zip_missing(self) -> None:
        self.assertIn("zip.member_set", verify_zip(self.make_zip("missing"), self.expected))

    def test_zip_extra(self) -> None:
        self.assertIn("zip.member_set", verify_zip(self.make_zip("extra"), self.expected))

    def test_zip_duplicate(self) -> None:
        self.assertIn("zip.duplicate_members", verify_zip(self.make_zip("duplicate"), self.expected))

    def test_zip_traversal(self) -> None:
        self.assertIn("zip.unsafe_path", verify_zip(self.make_zip("traversal"), self.expected))

    def test_zip_symlink(self) -> None:
        self.assertIn("zip.symlink", verify_zip(self.make_zip("symlink"), self.expected))

    def test_zip_tamper(self) -> None:
        self.assertIn("zip.source_mismatch:runtime.txt", verify_zip(self.make_zip("tamper"), self.expected))

    def test_zip_lying_manifest_cannot_override_prebuild_inventory(self) -> None:
        self.assertIn("zip.source_mismatch:runtime.txt", verify_zip(self.make_zip("lying_manifest"), self.expected))

    def test_zip_wrong_identity(self) -> None:
        self.assertIn("zip.manifest_identity", verify_zip(self.make_zip("identity"), self.expected))

    def test_zip_wrong_mutability(self) -> None:
        self.assertIn("zip.mutable_flag:runtime.txt", verify_zip(self.make_zip("mutable"), self.expected))

    def test_zip_duplicate_manifest_entry(self) -> None:
        self.assertIn("zip.manifest_member_set", verify_zip(self.make_zip("manifest_duplicate"), self.expected))

    def test_valid_directory(self) -> None:
        self.make_entry()
        self.assertEqual(verify_directory(self.root)["integrity_gate"], "PASS")

    def test_directory_missing(self) -> None:
        self.make_entry()
        (self.root / BUNDLE).unlink()
        self.assertIn(BUNDLE, verify_directory(self.root)["missing"])

    def test_directory_extra(self) -> None:
        self.make_entry()
        (self.root / "extra").write_text("extra")
        self.assertEqual(verify_directory(self.root)["extra"], ["extra"])

    def test_directory_empty(self) -> None:
        self.make_entry()
        (self.root / "EVIDENCE_LEDGER.json").write_text("")
        self.assertIn("EVIDENCE_LEDGER.json", verify_directory(self.root)["empty"])

    def test_directory_hash_tamper(self) -> None:
        self.make_entry()
        (self.root / "EVIDENCE_LEDGER.json").write_text("changed")
        self.assertIn("EVIDENCE_LEDGER.json", verify_directory(self.root)["mismatch"])

    def test_duplicate_expected_names(self) -> None:
        self.make_entry()
        path = self.root / "Expected_File_List.txt"
        path.write_text(path.read_text() + BUNDLE + "\n")
        self.assertEqual(verify_directory(self.root)["integrity_gate"], "FAIL")

    def test_directory_symlink(self) -> None:
        self.make_entry()
        os.symlink(self.root / BUNDLE, self.root / "linked")
        self.assertIn("entry.symlink", verify_directory(self.root)["failures"])

    def test_ledger_cannot_name_another_artifact(self) -> None:
        self.make_entry()
        (self.root / "EVIDENCE_LEDGER.json").write_text('{"artifact": {"sha256": "wrong"}}')
        self.seal()
        self.assertIn("entry.artifact_identity", verify_directory(self.root)["failures"])

    def test_missing_checksum_coverage(self) -> None:
        self.make_entry()
        checksums = self.root / "SHA256SUMS.txt"
        checksums.write_text(checksums.read_text().splitlines()[0] + "\n")
        self.assertIn("entry.checksum_coverage", verify_directory(self.root)["failures"])

    def test_untrusted_paths(self) -> None:
        for name in ("../a", "/a", "C:/a", "a\\b", "a//b", "a/./b", "a/", "a\nb"):
            with self.subTest(name=name):
                self.assertFalse(safe_name(name))

    def test_existing_output_is_not_overwritten(self) -> None:
        with self.assertRaisesRegex(ValueError, "already exists"):
            build(self.root)

    def test_repository_output_is_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "outside the repository"):
            build(SCRIPTS / "output")

    def test_content_mapping_anchors_exist(self) -> None:
        self.assertEqual(len(content_mappings()), 5)

    def test_generated_entry_declares_traditional_chinese_font(self) -> None:
        """The browser evidence must not silently accept missing CJK glyphs."""
        source = (SCRIPTS / "Mrliou_MRL_build_evidence_entry_v1.py").read_text(
            encoding="utf-8"
        )
        browser = (SCRIPTS / "Mrliou_MRL_browser_acceptance_v1.mjs").read_text(
            encoding="utf-8"
        )
        self.assertIn('"Noto Sans CJK TC"', source)
        self.assertIn("document.fonts.check", browser)
        self.assertIn("cjk_font_ready", browser)


if __name__ == "__main__":
    unittest.main()
