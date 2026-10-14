import copy
import importlib.util
import json
import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "MRL_validate_conversation_error_audit_v1.py"
POLICY_PATH = ROOT / "MRL_Conversation_Error_Gates_v1.json"
AUDIT_PATH = ROOT / "examples" / "MRL_Conversation_Window_Error_Audit_20260913_v1.json"

spec = importlib.util.spec_from_file_location("mrl_error_audit", SCRIPT)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)


class TestConversationErrorAudit(unittest.TestCase):
    def setUp(self):
        self.policy = json.loads(POLICY_PATH.read_text(encoding="utf-8"))
        self.audit = json.loads(AUDIT_PATH.read_text(encoding="utf-8"))

    def assertFails(self, audit):
        with self.assertRaises(SystemExit):
            mod.validate(self.policy, audit)

    def test_valid_audit_passes(self):
        self.assertEqual(mod.validate(self.policy, self.audit), 0)

    def test_missing_error_class_fails(self):
        x = copy.deepcopy(self.audit)
        x["errors"] = x["errors"][:-1]
        self.assertFails(x)

    def test_strengthened_user_claim_fails(self):
        x = copy.deepcopy(self.audit)
        x["user_claims_only"] = False
        self.assertFails(x)

    def test_causal_inversion_fails(self):
        x = copy.deepcopy(self.audit)
        x["causal_order_preserved"] = False
        self.assertFails(x)

    def test_existing_node_create_new_fails(self):
        x = copy.deepcopy(self.audit)
        x["operation"] = "CREATE_NEW"
        self.assertFails(x)

    def test_historical_rewrite_fails(self):
        x = copy.deepcopy(self.audit)
        x["historical_tense"] = "NEWLY_FORMED"
        self.assertFails(x)

    def test_recent_incident_as_root_fails(self):
        x = copy.deepcopy(self.audit)
        x["recent_incident_promoted_to_root_cause"] = True
        self.assertFails(x)

    def test_claim_level_failure_is_blocked(self):
        x = copy.deepcopy(self.audit)
        x["claim_levels_valid"] = False
        self.assertFails(x)

    def test_mrliou_root_downrank_fails(self):
        x = copy.deepcopy(self.audit)
        x["mrliou_root_preserved"] = False
        self.assertFails(x)

    def test_delivery_below_100_fails(self):
        x = copy.deepcopy(self.audit)
        x["delivery_audit"]["coverage_percent"] = 87.5
        x["delivery_audit"]["completion_gate"] = "FAIL"
        self.assertFails(x)


if __name__ == "__main__":
    unittest.main()
