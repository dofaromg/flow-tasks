#!/usr/bin/env python3
"""Acceptance-focused tests using a loopback fake local model server."""

from __future__ import annotations

import json
import sys
import tempfile
import threading
import unittest
import urllib.request
import warnings
import zipfile
from concurrent.futures import ThreadPoolExecutor
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
from runtime.MRL_return_bundle_v1 import (
    MRLReturnBundleError,
    build_return_bundle,
    verify_return_bundle,
)


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

    def test_health_rejects_missing_configured_model(self) -> None:
        missing = MRLMotherRuntime(
            {
                "local_model": {
                    "backend": "ollama",
                    "endpoint": f"http://127.0.0.1:{self.server.server_port}",
                    "model": "MRL_missing_model",
                }
            },
            self.data_dir / "missing-model",
        )
        self.assertFalse(missing.health()["ready"])

    def test_rejects_disabled_autonomy_policy(self) -> None:
        with self.assertRaises(ValueError):
            MRLMotherRuntime(
                {
                    "autonomy_policy": {
                        "local_model_required": True,
                        "external_model_endpoints_allowed": True,
                        "stub_counts_as_inference": False,
                        "loopback_gateway_only": True,
                    },
                    "local_model": {
                        "backend": "ollama",
                        "endpoint": f"http://127.0.0.1:{self.server.server_port}",
                        "model": "MRL_test_model",
                    },
                },
                self.data_dir / "bad-policy",
            )

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

    def test_passport_storage_keys_do_not_collide(self) -> None:
        registry = MRLPassportRegistry(self.data_dir)
        for canonical_id in ("MRL_asset_a/b", "MRL_asset_a_b"):
            registry.issue(
                canonical_id=canonical_id,
                source_identity=canonical_id,
                world_state="source",
                capabilities=[],
                evidence_refs=[],
                return_anchor="origin",
                environment={},
            )
        self.assertEqual(registry.latest("MRL_asset_a/b")["canonical_id"], "MRL_asset_a/b")
        self.assertEqual(registry.latest("MRL_asset_a_b")["canonical_id"], "MRL_asset_a_b")
        self.assertEqual(len(list((self.data_dir / "passports").glob("*.jsonl"))), 2)

    def test_passport_version_allocation_is_thread_safe(self) -> None:
        registry = MRLPassportRegistry(self.data_dir)

        def issue(index: int) -> int:
            passport = registry.issue(
                canonical_id="MRL_asset_concurrent",
                source_identity="source/concurrent",
                world_state="candidate",
                capabilities=[f"MRL_CAP_{index}"],
                evidence_refs=[str(index)],
                return_anchor="origin",
                environment={},
            )
            return int(passport["version"])

        with ThreadPoolExecutor(max_workers=8) as executor:
            versions = list(executor.map(issue, range(20)))
        self.assertEqual(sorted(versions), list(range(1, 21)))
        self.assertTrue(registry.verify("MRL_asset_concurrent")["ok"])

    def test_invalid_session_is_rejected_before_persistence(self) -> None:
        with self.assertRaises(ValueError):
            self.runtime.run(
                prompt="must not persist",
                world_id="MRL_test_world",
                session_id="invalid/session",
            )
        self.assertEqual(self.runtime.memory.chain.read_all(), [])
        self.assertEqual(self.runtime.evidence.chain.read_all(), [])

    def test_blank_session_is_rejected_before_persistence(self) -> None:
        """An explicit blank identity must not be replaced with a generated ID."""
        with self.assertRaises(ValueError):
            self.runtime.run(
                prompt="must not persist",
                world_id="MRL_test_world",
                session_id="",
            )
        self.assertEqual(self.runtime.memory.chain.read_all(), [])
        self.assertEqual(self.runtime.evidence.chain.read_all(), [])

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

    def test_return_bundle_requires_explicit_consent(self) -> None:
        source = self.data_dir / "evidence.json"
        source.write_text('{"ok": true}', encoding="utf-8")
        with self.assertRaises(MRLReturnBundleError):
            build_return_bundle(
                files=[source],
                output_path=self.data_dir / "return.zip",
                policy={
                    "automatic_upload_allowed": False,
                    "allowed_extensions": [".json"],
                    "max_bundle_bytes": 1024,
                },
                consent=False,
                purpose="support",
                hardware_id="MRL_hardware_test",
                model_release_id="MRL_model_test",
            )

    def test_return_bundle_is_complete_and_verifiable(self) -> None:
        source = self.data_dir / "evidence.jsonl"
        source.write_text('{"state":"PASS"}\n', encoding="utf-8")
        output = self.data_dir / "return.zip"
        result = build_return_bundle(
            files=[source],
            output_path=output,
            policy={
                "automatic_upload_allowed": False,
                "allowed_extensions": [".jsonl"],
                "blocked_filenames": [".env"],
                "max_bundle_bytes": 1024,
            },
            consent=True,
            purpose="support evidence",
            hardware_id="MRL_hardware_test",
            model_release_id="MRL_model_test",
        )
        self.assertTrue(output.is_file())
        self.assertEqual(result["manifest"]["consent"]["automatic_upload"], False)
        self.assertEqual(result["manifest"]["files"][0]["name"], "evidence.jsonl")
        verified = verify_return_bundle(output)
        self.assertTrue(verified["ok"])
        self.assertEqual(verified["files"], 1)

    def test_return_bundle_rejects_disallowed_file_type(self) -> None:
        source = self.data_dir / "secret.key"
        source.write_text("not-for-return", encoding="utf-8")
        with self.assertRaises(MRLReturnBundleError):
            build_return_bundle(
                files=[source],
                output_path=self.data_dir / "return.zip",
                policy={
                    "automatic_upload_allowed": False,
                    "allowed_extensions": [".json"],
                    "max_bundle_bytes": 1024,
                },
                consent=True,
                purpose="support",
                hardware_id="MRL_hardware_test",
                model_release_id="MRL_model_test",
            )

    def test_return_bundle_rejects_output_aliasing_source(self) -> None:
        """Opening the output must never truncate a selected source file."""
        source = self.data_dir / "evidence.jsonl"
        original = b'{"state":"PASS"}\n'
        source.write_bytes(original)
        with self.assertRaises(MRLReturnBundleError):
            build_return_bundle(
                files=[source],
                output_path=source,
                policy={
                    "automatic_upload_allowed": False,
                    "allowed_extensions": [".jsonl"],
                    "max_bundle_bytes": 1024,
                },
                consent=True,
                purpose="support",
                hardware_id="MRL_hardware_test",
                model_release_id="MRL_model_test",
            )
        self.assertEqual(source.read_bytes(), original)

    def test_return_bundle_rejects_invalid_manifest_semantics(self) -> None:
        """Consent and total byte claims must match the verified payload."""
        source = self.data_dir / "evidence.jsonl"
        source.write_text('{"state":"PASS"}\n', encoding="utf-8")
        output = self.data_dir / "return.zip"
        build_return_bundle(
            files=[source],
            output_path=output,
            policy={
                "automatic_upload_allowed": False,
                "allowed_extensions": [".jsonl"],
                "max_bundle_bytes": 1024,
            },
            consent=True,
            purpose="support",
            hardware_id="MRL_hardware_test",
            model_release_id="MRL_model_test",
        )
        with zipfile.ZipFile(output, "r") as archive:
            payload = archive.read("payload/evidence.jsonl")
            manifest = json.loads(archive.read("MRL_RETURN_MANIFEST.json"))
        manifest["consent"]["explicit"] = False
        with zipfile.ZipFile(output, "w") as archive:
            archive.writestr("MRL_RETURN_MANIFEST.json", json.dumps(manifest))
            archive.writestr("payload/evidence.jsonl", payload)
        self.assertEqual(
            verify_return_bundle(output)["reason"], "manifest_consent_invalid"
        )

        manifest["consent"]["explicit"] = True
        manifest["total_bytes"] += 1
        with zipfile.ZipFile(output, "w") as archive:
            archive.writestr("MRL_RETURN_MANIFEST.json", json.dumps(manifest))
            archive.writestr("payload/evidence.jsonl", payload)
        self.assertEqual(
            verify_return_bundle(output)["reason"], "manifest_total_bytes_mismatch"
        )

    def test_return_bundle_rejects_duplicate_archive_members(self) -> None:
        """Duplicate ZIP members cannot be hidden by set-based coverage checks."""
        output = self.data_dir / "duplicate.zip"
        manifest = {
            "schema": "MRL_Return_Bundle_v1",
            "bundle_id": "MRL_return_duplicate",
            "created_at": "2026-08-28T00:00:00+00:00",
            "origin_signature": "MrLiouWord",
            "hardware_id": "MRL_hardware_test",
            "model_release_id": "MRL_model_test",
            "purpose": "support",
            "consent": {"explicit": True, "automatic_upload": False},
            "files": [],
            "total_bytes": 0,
        }
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", UserWarning)
            with zipfile.ZipFile(output, "w") as archive:
                encoded = json.dumps(manifest)
                archive.writestr("MRL_RETURN_MANIFEST.json", encoded)
                archive.writestr("MRL_RETURN_MANIFEST.json", encoded)
        self.assertEqual(
            verify_return_bundle(output)["reason"], "payload_coverage_mismatch"
        )


if __name__ == "__main__":
    unittest.main()
