"""MRL reversible change receipt and rollback-gate tests."""
import copy
import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import MRL_reversible_change_v1 as reversible


class ReversibleChangeTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        (self.root / "before.bin").write_bytes(b"stable-v1")
        (self.root / "candidate.bin").write_bytes(b"candidate-v2")
        (self.root / "returned.bin").write_bytes(b"stable-v1")
        self.change_id = "MRL-DL580-20261103-R01"
        self.before_state = {"bundle": "stable-v1", "service": "healthy", "driver": "unchanged"}
        self.forward_state = {"bundle": "candidate-v2", "service": "healthy", "driver": "unchanged"}
        self.command = [{"argv": ["MRL_switch", "--to", "candidate-v2"],
                         "expected_exit_codes": [0], "requires_owner_go": True}]
        self.return_command = [{"argv": ["MRL_switch", "--to", "stable-v1"],
                                "expected_exit_codes": [0], "requires_owner_go": True}]

    def tearDown(self):
        self.temporary.cleanup()

    def chain(self):
        before = reversible.build_receipt(
            evidence_root=self.root, change_id=self.change_id, phase="before",
            state=self.before_state, artifacts=["before.bin"], commands=[], status="captured")
        forward = reversible.build_receipt(
            evidence_root=self.root, change_id=self.change_id, phase="forward",
            state=self.forward_state, artifacts=["candidate.bin"], commands=self.command,
            status="passed", previous_receipt_digest=before["receipt_digest"])
        returned = reversible.build_receipt(
            evidence_root=self.root, change_id=self.change_id, phase="return",
            state=self.before_state, artifacts=["returned.bin"], commands=self.return_command,
            status="passed", previous_receipt_digest=forward["receipt_digest"])
        return before, forward, returned

    def test_verified_roundtrip(self):
        result = reversible.verify_roundtrip(*self.chain(), self.root)
        self.assertEqual(result["status"], "roundtrip_verified")
        self.assertTrue(result["allowed_for_owner_review"])

    def test_return_must_reproduce_before_state(self):
        before, forward, returned = self.chain()
        returned = reversible.build_receipt(
            evidence_root=self.root, change_id=self.change_id, phase="return",
            state={"bundle": "wrong"}, artifacts=["returned.bin"], commands=self.return_command,
            status="passed", previous_receipt_digest=forward["receipt_digest"])
        with self.assertRaisesRegex(reversible.ReceiptError, "does not reproduce"):
            reversible.verify_roundtrip(before, forward, returned, self.root)

    def test_tampered_artifact_fails(self):
        receipts = self.chain()
        (self.root / "candidate.bin").write_bytes(b"replaced-after-check")
        with self.assertRaisesRegex(reversible.ReceiptError, "artifact changed"):
            reversible.verify_roundtrip(*receipts, self.root)

    def test_broken_receipt_link_fails(self):
        before, forward, returned = self.chain()
        returned["previous_receipt_digest"] = "sha256:" + "0" * 64
        returned["receipt_digest"] = reversible.canonical_digest({key: value for key, value in returned.items()
                                                                   if key != "receipt_digest"})
        with self.assertRaisesRegex(reversible.ReceiptError, "not linked"):
            reversible.verify_roundtrip(before, forward, returned, self.root)

    def test_failed_phase_never_completes(self):
        before, forward, _ = self.chain()
        returned = reversible.build_receipt(
            evidence_root=self.root, change_id=self.change_id, phase="return",
            state=self.before_state, artifacts=["returned.bin"], commands=self.return_command,
            status="failed", previous_receipt_digest=forward["receipt_digest"])
        with self.assertRaisesRegex(reversible.ReceiptError, "non-passing"):
            reversible.verify_roundtrip(before, forward, returned, self.root)

    def test_forward_and_return_require_owner_gate(self):
        command = copy.deepcopy(self.command)
        command[0]["requires_owner_go"] = False
        with self.assertRaisesRegex(reversible.ReceiptError, "owner Go"):
            reversible.build_receipt(
                evidence_root=self.root, change_id=self.change_id, phase="forward",
                state=self.forward_state, artifacts=["candidate.bin"], commands=command,
                status="prepared", previous_receipt_digest="sha256:" + "1" * 64)

    def test_artifact_path_cannot_escape_root(self):
        with self.assertRaisesRegex(reversible.ReceiptError, "root-relative"):
            reversible.build_receipt(
                evidence_root=self.root, change_id=self.change_id, phase="before",
                state=self.before_state, artifacts=["../secret"], commands=[], status="captured")

    def test_receipt_is_create_only(self):
        receipt = self.chain()[0]
        destination = self.root / "receipts" / "before.json"
        reversible.write_new(destination, receipt)
        self.assertEqual(json.loads(destination.read_text())["receipt_digest"], receipt["receipt_digest"])
        with self.assertRaises(FileExistsError):
            reversible.write_new(destination, receipt)

    def test_return_same_state_with_wrong_bytes_is_rejected(self):
        before, forward, returned = self.chain()
        returned = reversible.build_receipt(
            evidence_root=self.root, change_id=self.change_id, phase='return',
            state=self.before_state, artifacts=['candidate.bin'], commands=self.return_command,
            status='passed', previous_receipt_digest=forward['receipt_digest'])
        with self.assertRaisesRegex(reversible.ReceiptError, 'return artifact bytes'):
            reversible.verify_roundtrip(before, forward, returned, self.root)

    def test_symlinked_before_artifact_is_rejected(self):
        try:
            (self.root / 'linked.bin').symlink_to(self.root / 'before.bin')
        except OSError:
            self.skipTest('symlink privilege unavailable')
        with self.assertRaisesRegex(reversible.ReceiptError, 'symlink'):
            reversible.build_receipt(
                evidence_root=self.root, change_id=self.change_id, phase='before',
                state=self.before_state, artifacts=['linked.bin'], commands=[], status='captured')


if __name__ == "__main__":
    unittest.main()
