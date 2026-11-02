"""Pure static fixtures; never download/install the malicious package."""
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
import subprocess
import sys

spec = importlib.util.spec_from_file_location("mrl_scan", Path(__file__).with_name("scan.py"))
scanner = importlib.util.module_from_spec(spec)
spec.loader.exec_module(scanner)


class ScannerTests(unittest.TestCase):
    def check(self, text, state):
        results = scanner.inspect_text(text)
        states = [s for s, _ in results]
        actual = "HIT" if "HIT" in states else "UNKNOWN" if "UNKNOWN" in states else "NO_HIT"
        self.assertEqual(actual, state, results)

    def test_pins(self):
        for text in ["litellm==1.107.0", 'litellm[proxy]===1.107.0', 'LiteLLM==v1.107.0+vendor', 'litellm==1.107.0.0']:
            with self.subTest(text=text):
                self.check(text, "HIT")

    def test_clean_pin(self):
        self.check("litellm==1.106.2", "NO_HIT")

    def test_prerelease_not_incident_release(self):
        self.check("litellm==1.107.0rc2", "NO_HIT")

    def test_ranges_and_bare(self):
        for text in ["litellm", "litellm>=1.0", "litellm~=1.106", "litellm @ https://example.test/pkg.whl"]:
            self.check(text, "UNKNOWN")

    def test_mutable_and_missing_image_tag(self):
        for tag in [":latest", ":main-stable", ":main-latest", "", ":${VERSION}"]:
            self.check("image: ghcr.io/berriai/litellm" + tag, "UNKNOWN")

    def test_bad_image_tag(self):
        self.check("FROM docker.io/litellm/litellm:v1.107.0", "HIT")

    def test_digest_beats_tag(self):
        digest = scanner.POLICY["bad_digest_prefixes"][0]
        self.check("mirror.test/relabelled@sha256:" + digest, "HIT")

    def test_published_prefix(self):
        self.check("sha256:" + "c00f9d92c427" + "0" * 52, "HIT")

    def test_unknown_digest_never_proves_trust(self):
        self.check("ghcr.io/berriai/litellm:v1.106.3@sha256:" + "a" * 64, "UNKNOWN")

    def test_lockfiles(self):
        for text in ['[[package]]\nname = "litellm"\nversion = "1.107.0"', '{"default":{"litellm":{"version":"==1.107.0"}}}', '{"components":[{"name":"litellm","version":"1.107.0"}]}']:
            self.check(text, "HIT")

    def test_clean_lock(self):
        self.check('[[package]]\nname = "litellm"\nversion = "1.106.2"', "NO_HIT")

    def test_installed_metadata(self):
        self.check("Metadata-Version: 2.4\nName: litellm\nVersion: 1.107.0\n", "HIT")

    def test_wheel_hashes(self):
        for digest in scanner.POLICY["bad_file_sha256"]:
            self.check(digest, "HIT")

    def test_two_references(self):
        self.check("litellm==1.106.2\nlitellm>=1.0", "UNKNOWN")

    def test_constraint_next_to_structured_lock(self):
        self.check('[[package]]\nname = "litellm"\nversion = "1.106.2"\n# section\n[deps]\nlitellm = ">=1"', "UNKNOWN")

    def test_startup_file_has_no_execution_proof(self):
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / "cook.pth").write_text("import cook")
            report = scanner.scan(tmp, runtime=True)
            self.assertEqual(report["state"], "UNKNOWN")
            self.assertFalse(report["runtime_verified"])

    def test_symlink_is_unknown(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "external").symlink_to("/nonexistent/mrl", target_is_directory=True)
            self.assertEqual(scanner.scan(root)["state"], "UNKNOWN")

    def test_renamed_binary_hash(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "renamed.bin"
            path.write_bytes(b"harmless fixture")
            scanner.POLICY["bad_file_sha256"].append(scanner.sha(path.read_bytes()))
            try:
                self.assertEqual(scanner.scan(tmp, runtime=True)["state"], "HIT")
            finally:
                scanner.POLICY["bad_file_sha256"].pop()

    def test_filesystem(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "requirements.txt").write_text("litellm==1.106.2")
            self.assertEqual(scanner.scan(root)["state"], "NO_HIT")
            (root / "litellm-1.107.0.dist-info").mkdir()
            self.assertEqual(scanner.scan(root)["state"], "HIT")

    def test_missing_root(self):
        self.assertEqual(scanner.scan("/nonexistent/mrl-32")["state"], "UNKNOWN")

    def test_hook_not_executed(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "sitecustomize.py").write_text("raise RuntimeError('must never execute')")
            self.assertEqual(scanner.scan(root)["state"], "UNKNOWN")

    def test_archives_remain_unknown(self):
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / "cached.zip").write_bytes(b"not an executable fixture")
            self.assertEqual(scanner.scan(tmp)["state"], "UNKNOWN")

    def test_no_secret_lines(self):
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / "requirements.txt").write_text("litellm>=1.0 # fake-secret-never-publish")
            self.assertNotIn("fake-secret", json.dumps(scanner.scan(tmp)))

    def test_cli_exit_contract(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "input"
            root.mkdir()
            for index, (text, code) in enumerate([("litellm==1.106.2", 0), ("litellm==1.107.0", 1), ("litellm>=1", 2)]):
                (root / "requirements.txt").write_text(text)
                out = Path(tmp) / (str(index) + ".json")
                result = subprocess.run([sys.executable, "-I", "-S", "-B", str(Path(scanner.__file__)), str(root), "--output", str(out)], capture_output=True, text=True)
                self.assertEqual(result.returncode, code, result.stderr)
                self.assertTrue(out.is_file())

    def test_cli_preserves_prior_evidence(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "input"
            root.mkdir()
            out = Path(tmp) / "evidence.json"
            out.write_text("prior evidence")
            result = subprocess.run([sys.executable, "-I", "-S", "-B", str(Path(scanner.__file__)), str(root), "--output", str(out)], capture_output=True)
            self.assertNotEqual(result.returncode, 0)
            self.assertEqual(out.read_text(), "prior evidence")


if __name__ == "__main__":
    unittest.main()
