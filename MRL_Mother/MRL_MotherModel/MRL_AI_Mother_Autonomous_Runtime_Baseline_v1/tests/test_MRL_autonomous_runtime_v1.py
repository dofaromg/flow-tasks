#!/usr/bin/env python3
"""Acceptance-focused tests using a loopback fake local model server."""

from __future__ import annotations

import json
import sys
import tempfile
import threading
import unittest
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

PACKAGE_ROOT = Path(__file__).resolve().parents[1]
if str(PACKAGE_ROOT) not in sys.path:
    sys.path.insert(0, str(PACKAGE_ROOT))

from runtime.MRL_hash_chain_v1 import MRLHashChain
from runtime.MRL_apiworks_gateway_v1 import build_handler
from runtime.MRL_local_model_adapter_v1 import MRLModelGateError, require_loopback_endpoint
from runtime.MRL_mother_runtime_v1 import MRLMotherRuntime
from runtime.MRL_passport_registry_v1 import MRLPassportRegistry


class _FakeOllamaHandler(BaseHTTPRequestHandler):
    def _write(self, value: dict) -> None:
        body = json.dumps(value).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:  # noqa: N802
        self._write({"models": [{"name": "MRL_test_model"}]})

    def do_POST(self) -> None:  # noqa: N802
        length = int(self.headers.get("Content-Length", "0"))
        request = json.loads(self.rfile.read(length).decode("utf-8"))
        prompt = request["messages"][-1]["content"]
        self._write(
            {
                "message": {"role": "assistant", "content": f"MRL_LOCAL:{prompt}"},
                "prompt_eval_count": 3,
                "eval_count": 2,
            }
        )

    def log_message(self, format_string: str, *args: object) -> None:
        return


class MRLAutonomousRuntimeTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.data_dir = Path(self.temp.name)
        self.server = ThreadingHTTPServer(("127.0.0.1", 0), _FakeOllamaHandler)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        endpoint = f"http://127.0.0.1:{self.server.server_port}"
        self.runtime = MRLMotherRuntime(
            {
                "local_model": {
                    "backend": "ollama",
                    "endpoint": endpoint,
                    "model": "MRL_test_model",
                }
            },
            self.data_dir,
        )

    def tearDown(self) -> None:
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=2)
        self.temp.cleanup()

    def test_rejects_external_model_endpoint(self) -> None:
        with self.assertRaises(MRLModelGateError):
            require_loopback_endpoint("https://example.com/v1")

    def test_health_passes_with_loopback_model(self) -> None:
        health = self.runtime.health()
        self.assertTrue(health["ready"])
        self.assertEqual(health["autonomy_gate"], "PASS")
        self.assertFalse(health["external_model_required"])

    def test_full_runtime_loop_persists_memory_evidence_and_passport(self) -> None:
        result = self.runtime.run(
            prompt="remember this particle",
            world_id="MRL_test_world",
            session_id="MRL_session_test",
        )
        self.assertEqual(result["text"], "MRL_LOCAL:remember this particle")
        self.assertEqual(result["passport"]["source_identity"], "MRL_session_test")
        self.assertEqual(result["passport"]["world_state"], "candidate")
        self.assertTrue(self.runtime.memory.verify()["ok"])
        self.assertTrue(self.runtime.evidence.verify()["ok"])
        self.assertTrue(
            self.runtime.passports.verify(result["passport"]["canonical_id"])["ok"]
        )
        recalled = self.runtime.recall(
            world_id="MRL_test_world", session_id="MRL_session_test"
        )
        self.assertEqual(len(recalled["records"]), 2)

    def test_hash_chain_detects_tampering(self) -> None:
        chain = MRLHashChain(self.data_dir / "tamper.jsonl", "MRL_TEST")
        chain.append({"value": 1})
        path = self.data_dir / "tamper.jsonl"
        path.write_text(path.read_text(encoding="utf-8").replace('"value": 1', '"value": 2'), encoding="utf-8")
        self.assertFalse(chain.verify()["ok"])

    def test_passport_versions_are_additive(self) -> None:
        registry = MRLPassportRegistry(self.data_dir)
        first = registry.issue(
            canonical_id="MRL_asset_1",
            source_identity="source/1",
            world_state="source",
            capabilities=[],
            evidence_refs=[],
            return_anchor="origin",
            environment={},
        )
        second = registry.issue(
            canonical_id="MRL_asset_1",
            source_identity="source/1",
            world_state="candidate",
            capabilities=["MRL_TRANSLATE"],
            evidence_refs=["evidence-1"],
            return_anchor="origin",
            environment={"runtime": "test"},
        )
        self.assertEqual(second["version"], 2)
        self.assertEqual(second["previous_passport_hash"], first["passport_hash"])
        self.assertTrue(registry.verify("MRL_asset_1")["ok"])

    def test_apiworks_gateway_exposes_complete_audited_loop(self) -> None:
        gateway = ThreadingHTTPServer(("127.0.0.1", 0), build_handler(self.runtime))
        thread = threading.Thread(target=gateway.serve_forever, daemon=True)
        thread.start()
        base = f"http://127.0.0.1:{gateway.server_port}"
        try:
            with urllib.request.urlopen(f"{base}/health", timeout=3) as response:
                health = json.loads(response.read().decode("utf-8"))
            self.assertTrue(health["ready"])
            request = urllib.request.Request(
                f"{base}/v1/mother/run",
                data=json.dumps(
                    {
                        "prompt": "gateway particle",
                        "world_id": "MRL_gateway_world",
                        "session_id": "MRL_session_gateway",
                    }
                ).encode("utf-8"),
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(request, timeout=3) as response:
                result = json.loads(response.read().decode("utf-8"))
            self.assertTrue(result["ok"])
            self.assertTrue(result["evidence_ref"])
            self.assertTrue(result["passport"]["passport_hash"])
            with urllib.request.urlopen(
                f"{base}/v1/memory/recall?world_id=MRL_gateway_world&session_id=MRL_session_gateway",
                timeout=3,
            ) as response:
                recalled = json.loads(response.read().decode("utf-8"))
            self.assertEqual(len(recalled["records"]), 2)
        finally:
            gateway.shutdown()
            gateway.server_close()
            thread.join(timeout=2)

    def test_failed_local_inference_is_sealed_as_evidence(self) -> None:
        broken = MRLMotherRuntime(
            {
                "local_model": {
                    "backend": "ollama",
                    "endpoint": "http://127.0.0.1:1",
                    "model": "MRL_unreachable_model",
                    "timeout_seconds": 1,
                }
            },
            self.data_dir / "broken",
        )
        with self.assertRaises(RuntimeError):
            broken.run(prompt="must fail", world_id="MRL_failure_world")
        records = broken.evidence.chain.read_all()
        self.assertEqual(records[-1]["payload"]["state"], "FAIL")
        self.assertTrue(broken.evidence.verify()["ok"])


if __name__ == "__main__":
    unittest.main()
