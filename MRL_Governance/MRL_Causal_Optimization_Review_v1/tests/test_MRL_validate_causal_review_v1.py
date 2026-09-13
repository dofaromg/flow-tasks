import copy
import importlib.util
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "MRL_validate_causal_review_v1.py"
EXAMPLE = ROOT / "examples" / "MRL_Causal_Review_Record_example.json"

spec = importlib.util.spec_from_file_location("mrl_validate_causal_review", SCRIPT)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


class TestCausalReviewValidator(unittest.TestCase):
    """Regression tests for schema enforcement and verified consensus votes."""

    def setUp(self):
        self.record = json.loads(EXAMPLE.read_text(encoding="utf-8"))

    def assert_fails(self, record):
        """Assert that an invalid record fails closed."""
        with self.assertRaises(SystemExit):
            mod.validate(record)

    def test_valid_example_passes(self):
        """Accept the published schema-conformant example."""
        self.assertEqual(mod.validate(self.record)["computed_consensus"], "CONSENSUS")

    def test_unsigned_attestation_fails(self):
        """Reject a null receipt before its decision can be counted."""
        record = copy.deepcopy(self.record)
        record["node_attestations"][1]["signature"] = None
        self.assert_fails(record)

    def test_tampered_attestation_fails(self):
        """Reject a receipt when a signed decision is changed."""
        record = copy.deepcopy(self.record)
        record["node_attestations"][1]["decision"] = "FACT"
        self.assert_fails(record)

    def test_empty_event_id_fails(self):
        """Enforce the schema minimum length."""
        record = copy.deepcopy(self.record)
        record["event_id"] = ""
        self.assert_fails(record)

    def test_wrong_original_request_type_fails(self):
        """Enforce the schema string type."""
        record = copy.deepcopy(self.record)
        record["original_request"] = 7
        self.assert_fails(record)

    def test_non_string_evidence_reference_fails(self):
        """Enforce the schema item type."""
        record = copy.deepcopy(self.record)
        record["evidence_references"] = [7]
        self.assert_fails(record)

    def test_unknown_property_fails(self):
        """Enforce the schema additionalProperties boundary."""
        record = copy.deepcopy(self.record)
        record["unexpected_field"] = "must-fail"
        self.assert_fails(record)


if __name__ == "__main__":
    unittest.main()
