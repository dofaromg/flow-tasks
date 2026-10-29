"""Evidence capture integration tests; model responses are explicitly synthetic."""

import importlib.util
import json
import subprocess
import sys
import tempfile
import threading
import unittest
from http.server import ThreadingHTTPServer
from pathlib import Path

PRODUCT_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = PRODUCT_ROOT.parents[1]
RUNTIME_ROOT = REPO_ROOT / "MRL_Mother/MRL_MotherModel/MRL_AI_Mother_Autonomous_Runtime_Baseline_v1"


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


capture_module = load("mrl_node_evidence", PRODUCT_ROOT / "scripts/MRL_capture_node_evidence_v1.py")
fixture = load("mrl_runtime_test_fixture", RUNTIME_ROOT / "tests/test_MRL_autonomous_runtime_v1.py")


class NodeEvidenceTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.data_dir = self.root / "data"
        self.model = ThreadingHTTPServer(("127.0.0.1", 0), fixture._FakeOllamaHandler)
        self.model_thread = threading.Thread(target=self.model.serve_forever, daemon=True)
        self.model_thread.start()
        self.config = {"local_model": {"backend": "ollama", "model": "MRL_test_model",
                        "endpoint": f"http://127.0.0.1:{self.model.server_port}"}}
        self.start_gateway()

    def start_gateway(self, port=0):
        runtime = fixture.MRLMotherRuntime(self.config, self.data_dir)
        self.gateway = ThreadingHTTPServer(("127.0.0.1", port), fixture.build_handler(runtime))
        self.gateway_thread = threading.Thread(target=self.gateway.serve_forever, daemon=True)
        self.gateway_thread.start()
        self.url = f"http://127.0.0.1:{self.gateway.server_port}"

    def stop_gateway(self):
        self.gateway.shutdown()
        self.gateway.server_close()
        self.gateway_thread.join(timeout=2)

    def tearDown(self):
        self.stop_gateway()
        self.model.shutdown()
        self.model.server_close()
        self.model_thread.join(timeout=2)
        self.temporary.cleanup()

    def run_cli(self, name, prior=None):
        output = self.root / name
        command = [sys.executable, str(PRODUCT_ROOT / "scripts/MRL_capture_node_evidence_v1.py"),
                   "--gateway", self.url, "--data-dir", str(self.data_dir), "--output", str(output)]
        if prior:
            command += ["--replay-receipt", str(prior)]
        process = subprocess.run(command, capture_output=True, text=True, timeout=30)
        return process, output

    def test_capture_and_replay_after_gateway_restart(self):
        process, before = self.run_cli("before.json")
        self.assertEqual(process.returncode, 0, process.stderr)
        first = json.loads(before.read_text())
        self.assertEqual(first["customer_node_acceptance"], "PENDING_REAL_MODEL_AND_RESTART_REVIEW")
        port = self.gateway.server_port
        self.stop_gateway()
        self.start_gateway(port)
        process, after = self.run_cli("after.json", before)
        self.assertEqual(process.returncode, 0, process.stdout + process.stderr)
        second = json.loads(after.read_text())
        self.assertEqual(second["status"], "PERSISTED_REPLAY_EVIDENCE_PASS")
        self.assertEqual(second["prior_receipt_hash"], first["receipt_hash"])
        self.assertEqual(second["verified"]["session_id"], first["verified"]["session_id"])
        self.assertFalse(second["restart_observed"])
        self.assertNotIn("CUSTOMER_NODE_ACCEPTANCE_PASS", after.read_text())

    def test_tampered_disk_evidence_fails_with_failure_receipt(self):
        process, before = self.run_cli("before.json")
        self.assertEqual(process.returncode, 0, process.stderr)
        ledger = self.data_dir / "MRL_evidence_events.jsonl"
        records = ledger.read_text().replace('"PASS"', '"FAIL"')
        ledger.write_text(records)
        process, after = self.run_cli("after.json", before)
        self.assertEqual(process.returncode, 1)
        self.assertEqual(json.loads(after.read_text())["status"], "NODE_EVIDENCE_FAIL")

    def test_tampered_prior_receipt_is_rejected(self):
        process, before = self.run_cli("before.json")
        self.assertEqual(process.returncode, 0)
        receipt = json.loads(before.read_text())
        receipt["host"] = "another-node"
        before.write_text(json.dumps(receipt))
        process, after = self.run_cli("after.json", before)
        self.assertEqual(process.returncode, 1)
        self.assertIn("prior receipt hash mismatch", json.loads(after.read_text())["error"])

    def test_existing_receipts_are_never_overwritten(self):
        process, before = self.run_cli("before.json")
        self.assertEqual(process.returncode, 0)
        original = before.read_bytes()
        process, _ = self.run_cli("before.json")
        self.assertNotEqual(process.returncode, 0)
        self.assertEqual(before.read_bytes(), original)

    def test_jsonl_preserves_unicode_separators(self):
        """Valid JSON strings retain Unicode separators / 保留字串分隔字元。"""
        for separator in ("\u0085", "\u2028", "\u2029"):
            with self.subTest(separator=repr(separator)):
                record = {"sequence": 1, "previous_hash": "GENESIS",
                          "origin_signature": "MrLiouWord",
                          "payload": {"content": "before" + separator + "after"}}
                record["record_hash"] = capture_module.digest(record)
                ledger = self.root / "unicode.jsonl"
                ledger.write_text(json.dumps(record, ensure_ascii=False) + "\n\n", encoding="utf-8")
                self.assertEqual(capture_module.read_chain(ledger), [record])

    def test_external_gateway_is_rejected(self):
        self.url = "https://example.com"
        process, output = self.run_cli("failed.json")
        self.assertEqual(process.returncode, 1)
        self.assertIn("loopback", json.loads(output.read_text())["error"])


class UnicodeLedgerTests(unittest.TestCase):
    def test_hash_chain_recall_preserves_unicode_separators(self):
        """Valid model text must survive disk recall and hash verification."""
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "memory.jsonl"
            chain = fixture.MRLHashChain(path, "MRL_TEST")
            text = "before\u0085middle\u2028next\u2029after"
            record = chain.append({"content": text})
            self.assertEqual(chain.read_all(), [record])
            self.assertTrue(chain.verify()["ok"])
            self.assertEqual(capture_module.read_chain(path), [record])

    def test_passport_latest_and_versions_preserve_unicode_separators(self):
        """Unicode metadata must not split a Passport JSONL record."""
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            registry = fixture.MRLPassportRegistry(root)
            arguments = dict(canonical_id="MRL_unicode", source_identity="MRL_test",
                             world_state="candidate", capabilities=[], evidence_refs=[],
                             return_anchor="GENESIS", environment={"text": "a\u0085b\u2028c\u2029d"})
            first = registry.issue(**arguments)
            self.assertEqual(registry.latest("MRL_unicode"), first)
            second = registry.issue(**arguments)
            self.assertTrue(registry.verify("MRL_unicode")["ok"])
            self.assertEqual(capture_module.read_chain(registry._path("MRL_unicode"), passport=True),
                             [first, second])


if __name__ == "__main__":
    unittest.main()
