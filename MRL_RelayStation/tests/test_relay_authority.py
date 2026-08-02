import hashlib
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

MODULE_PATH = Path(__file__).parents[1] / "runtime" / "relay_authority.py"
SPEC = importlib.util.spec_from_file_location("relay_authority", MODULE_PATH)
relay_authority = importlib.util.module_from_spec(SPEC)
assert SPEC and SPEC.loader
SPEC.loader.exec_module(relay_authority)


class RelayAuthorityTests(unittest.TestCase):
    def build_record(self, root: Path) -> dict:
        artifact = root / "artifact.txt"
        artifact.write_text("MRL candidate\n", encoding="utf-8")
        digest = hashlib.sha256(artifact.read_bytes()).hexdigest()
        return {
            "source": {"provider": "claude", "session_id": "session-test"},
            "authority_level": "L1",
            "requested_scope": ["artifact.txt"],
            "generated_artifacts": ["artifact.txt"],
            "artifacts": [{"path": "artifact.txt", "sha256": digest}],
            "verification": {"status": "passed"},
            "canonical_status": "not_adopted"
        }

    def test_valid_candidate_passes(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            result = relay_authority.validate_record(self.build_record(root), root)
            self.assertTrue(result.passed)
            self.assertEqual(result.errors, ())

    def test_hash_mismatch_fails(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            record = self.build_record(root)
            record["artifacts"][0]["sha256"] = "0" * 64
            result = relay_authority.validate_record(record, root)
            self.assertFalse(result.passed)
            self.assertIn("sha256 mismatch: artifact.txt", result.errors)

    def test_external_provider_cannot_arrive_as_l3(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            record = self.build_record(root)
            record["authority_level"] = "L3"
            result = relay_authority.validate_record(record, root)
            self.assertFalse(result.passed)

    def test_mrl_approval_promotes_candidate(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            promoted = relay_authority.promote_record(
                self.build_record(root), root, "MRL_Owner", "L3"
            )
            self.assertEqual(promoted["authority_level"], "L3")
            self.assertEqual(promoted["promotion"]["authority"], "MRL")
            self.assertEqual(len(promoted["record_sha256"]), 64)


if __name__ == "__main__":
    unittest.main()
