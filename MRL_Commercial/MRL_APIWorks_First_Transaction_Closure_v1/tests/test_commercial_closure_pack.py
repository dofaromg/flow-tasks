from __future__ import annotations

import json
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class CommercialClosurePackTests(unittest.TestCase):
    """Verify the closure pack and production-delivery evidence contract."""

    def test_package_integrity(self) -> None:
        """The complete expected package must pass its structural verifier."""
        completed = subprocess.run(
            [sys.executable, "scripts/MRL_verify_commercial_closure_pack_v1.py"],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)

    def test_schema_has_cumulative_transaction_evidence_gates(self) -> None:
        """Every reached transaction state must require accumulated evidence."""
        schema = json.loads(
            (ROOT / "schemas/MRL_APIWorks_Transaction_Evidence_Record_v1.schema.json").read_text(
                encoding="utf-8"
            )
        )
        rules = {
            rule["if"]["properties"]["transaction_state"]["const"]: rule["then"]
            for rule in schema["allOf"]
        }
        expected = {
            "ORDER_SIGNED": {"order_reference"},
            "PAYMENT_CONFIRMED": {"order_reference", "payment_reference"},
            "DEPLOYMENT_COMPLETED": {
                "order_reference",
                "payment_reference",
                "deployment_receipt_reference",
            },
            "CUSTOMER_ACCEPTANCE_PASS": {
                "order_reference",
                "payment_reference",
                "deployment_receipt_reference",
                "acceptance_reference",
            },
            "PAYOUT_RECONCILED": {
                "order_reference",
                "payment_reference",
                "deployment_receipt_reference",
                "acceptance_reference",
                "payout_reference",
            },
            "FIRST_REALIZED_REVENUE_PASS": {
                "order_reference",
                "payment_reference",
                "deployment_receipt_reference",
                "acceptance_reference",
                "payout_reference",
            },
        }
        for state, references in expected.items():
            configured = rules[state]["properties"]["evidence_references"]["properties"]
            self.assertEqual(set(configured), references)
            for reference in references:
                self.assertEqual(configured[reference]["type"], "string")
            if state not in {"ORDER_SIGNED", "PAYMENT_CONFIRMED"}:
                self.assertEqual(
                    rules[state]["required"],
                    ["product_commit", "customer_bundle_sha256"],
                )

    def test_delivery_workflow_binds_main_and_checked_out_commit(self) -> None:
        """Production delivery must reject non-main refs and receipt the built tree."""
        workflow_path = (
            ROOT.parents[1] / ".github/workflows/mrl-apiworks-production-delivery.yml"
        )
        workflow = workflow_path.read_text(encoding="utf-8")
        self.assertIn('test "$GITHUB_REF" = "refs/heads/main"', workflow)
        self.assertIn("needs: authorize-production-reference", workflow)
        self.assertIn('PRODUCT_COMMIT="$(git rev-parse HEAD)"', workflow)
        self.assertIn('os.environ["PRODUCT_COMMIT"]', workflow)
        self.assertNotIn('os.environ["GITHUB_SHA"]', workflow)

if __name__ == "__main__":
    unittest.main()
