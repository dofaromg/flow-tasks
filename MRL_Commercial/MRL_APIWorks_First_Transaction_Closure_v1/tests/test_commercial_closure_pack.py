from __future__ import annotations

import json
import hashlib
import subprocess
import sys
import tempfile
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class _RouteHandler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:  # noqa: N802
        body = b"MRL route evidence fixture"
        if self.path == "/large":
            body = b"X" * (2 * 1024 * 1024 + 1)
        self.send_response(500 if self.path == "/failure" else 200)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *_args: object) -> None:
        return


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
                "revenue_ledger_reference",
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
                self.assertEqual(
                    rules[state]["properties"]["product_commit"],
                    {"type": "string", "pattern": "^[0-9a-f]{40}$"},
                )
                self.assertEqual(
                    rules[state]["properties"]["customer_bundle_sha256"],
                    {"type": "string", "pattern": "^[0-9a-f]{64}$"},
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
        self.assertIn("printf -- '- Order reference: `%s`", workflow)
        self.assertNotIn('echo "- Order reference: `', workflow)

    def test_browser_acceptance_is_built_and_retained_by_ci(self) -> None:
        """The closure workflow must render both viewports and retain evidence."""
        workflow_path = (
            ROOT.parents[1] / ".github/workflows/mrl-apiworks-commercial-closure.yml"
        )
        workflow = workflow_path.read_text(encoding="utf-8")
        browser_script = "scripts/Mrliou_MRL_browser_acceptance_v1.mjs"
        self.assertIn("Mrliou_MRL_build_evidence_entry_v1.py", workflow)
        self.assertEqual(workflow.count(browser_script), 2)
        self.assertIn("--verify-only", workflow)
        self.assertIn("actions/upload-artifact@v4", workflow)
        self.assertIn("Mrliou_MRL_APIWorks_Browser_Evidence", workflow)
        self.assertIn("fonts-noto-cjk", workflow)
        self.assertNotIn("workflow_dispatch", workflow)

    def test_public_route_receipt_capture_and_offline_verification(self) -> None:
        server = ThreadingHTTPServer(("127.0.0.1", 0), _RouteHandler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            with tempfile.TemporaryDirectory() as temporary:
                temp = Path(temporary)
                route_map = temp / "route-map.json"
                route_map.write_text(json.dumps({
                    "schema": "MRL_APIWorks_Public_Route_Map_v1",
                    "origin_signature": "MrLiouWord",
                    "canonical_route_decision": "UNRESOLVED",
                    "routes": [{
                        "route_id": "MRL_test_route",
                        "service": "MRL_test_service",
                        "url": f"http://127.0.0.1:{server.server_port}/health",
                        "expected_status": 200,
                        "cloudflare_version_id": None,
                        "observed_git_head": "a" * 40,
                        "traffic_scope": "TEST_LOOPBACK",
                        "production_traffic_asserted": False,
                    }],
                }), encoding="utf-8")
                output = temp / "evidence"
                script = ROOT / "scripts" / "Mrliou_MRL_public_route_receipt_v1.py"
                captured = subprocess.run([
                    sys.executable, str(script),
                    "--route-map", str(route_map),
                    "--output", str(output),
                    "--git-head", "b" * 40,
                    "--allow-loopback-http",
                ], text=True, capture_output=True, check=False)
                self.assertEqual(captured.returncode, 0, captured.stdout + captured.stderr)
                verified = subprocess.run([
                    sys.executable, str(script), "--verify-only", str(output)
                ], text=True, capture_output=True, check=False)
                self.assertEqual(verified.returncode, 0, verified.stdout + verified.stderr)
                receipt = json.loads((output / "PUBLIC_ROUTE_RECEIPT.json").read_text(encoding="utf-8"))
                self.assertEqual(receipt["public_route_gate"], "PUBLIC_ROUTE_TEST_PASS")
                self.assertFalse(receipt["routes"][0]["production_traffic_asserted"])
                # A re-sealed forged PASS must still fail semantic verification.
                receipt["routes"][0]["http_status"] = 500
                (output / "PUBLIC_ROUTE_RECEIPT.json").write_text(json.dumps(receipt), encoding="utf-8")
                (output / "SHA256SUMS.txt").write_text("\n".join(
                    f"{hashlib.sha256((output / name).read_bytes()).hexdigest()}  {name}"
                    for name in ("Expected_File_List.txt", "PUBLIC_ROUTE_RECEIPT.json")
                ) + "\n", encoding="utf-8")
                forged = subprocess.run([sys.executable, str(script), "--verify-only", str(output)],
                                        capture_output=True, text=True)
                self.assertNotEqual(forged.returncode, 0)
                self.assertIn("status_match", forged.stdout)
                # Failed HTTP observations remain valid evidence artifacts.
                mapping = json.loads(route_map.read_text())
                mapping["routes"][0]["url"] = f"http://127.0.0.1:{server.server_port}/failure"
                route_map.write_text(json.dumps(mapping))
                failed_output = temp / "failure-evidence"
                failed = subprocess.run([
                    sys.executable, str(script), "--route-map", str(route_map),
                    "--output", str(failed_output), "--git-head", "b" * 40,
                    "--allow-loopback-http",
                ], capture_output=True, text=True)
                self.assertEqual(failed.returncode, 1, failed.stdout + failed.stderr)
                report = json.loads(failed.stdout)
                self.assertEqual(report["artifact_integrity_gate"], "PASS")
                self.assertEqual(report["http_result_gate"], "PUBLIC_ROUTE_TEST_FAIL")
                (failed_output / "nested").mkdir()
                (failed_output / "nested/extra.txt").write_text("unexpected")
                extra = subprocess.run([sys.executable, str(script), "--verify-only", str(failed_output)],
                                       capture_output=True, text=True)
                self.assertEqual(json.loads(extra.stdout)["extra"], ["nested/extra.txt"])
                # An oversized body still produces an auditable bounded FAIL receipt.
                mapping["routes"][0]["url"] = f"http://127.0.0.1:{server.server_port}/large"
                route_map.write_text(json.dumps(mapping))
                large_output = temp / "large-evidence"
                large = subprocess.run([
                    sys.executable, str(script), "--route-map", str(route_map),
                    "--output", str(large_output), "--git-head", "b" * 40,
                    "--allow-loopback-http",
                ], capture_output=True, text=True)
                self.assertEqual(large.returncode, 1, large.stdout + large.stderr)
                self.assertEqual(json.loads(large.stdout)["artifact_integrity_gate"], "PASS")
                large_receipt = json.loads((large_output / "PUBLIC_ROUTE_RECEIPT.json").read_text())
                self.assertFalse(large_receipt["routes"][0]["response_complete"])
                self.assertEqual(large_receipt["routes"][0]["response_size_bytes"], 2 * 1024 * 1024)
                self.assertIn("RESPONSE_TOO_LARGE", large_receipt["routes"][0]["error"])
        finally:
            server.shutdown()
            thread.join(timeout=5)
            server.server_close()

    def test_public_route_workflow_is_manual_read_only_and_retains_evidence(self) -> None:
        workflow = (
            ROOT.parents[1] / ".github/workflows/mrl-apiworks-public-route-evidence.yml"
        ).read_text(encoding="utf-8")
        self.assertIn("workflow_dispatch", workflow)
        self.assertIn("CONFIRM_READ_ONLY_PUBLIC_ROUTE_PROBE", workflow)
        self.assertIn('test "$GITHUB_REF" = "refs/heads/main"', workflow)
        self.assertEqual(workflow.count("Mrliou_MRL_public_route_receipt_v1.py"), 2)
        self.assertIn("actions/upload-artifact@v4", workflow)
        self.assertGreaterEqual(workflow.count("continue-on-error: true"), 2)
        self.assertGreaterEqual(workflow.count("if: always()"), 2)
        self.assertIn("Enforce route evidence gate after retention", workflow)
        self.assertNotIn("wrangler deploy", workflow.lower())

if __name__ == "__main__":
    unittest.main()
