"""Synthetic smoke/replay tests; no device or model is claimed as accepted."""

import copy
import hashlib
import platform
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from MRL_Products.MRL_APIWorks_BYOH_Deployment_Product_v1.scripts import (
    MRL_hardware_admission_v1 as gate,
    MRL_hardware_smoke_v1 as smoke,
)


class HardwareSmokeTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.artifacts = self.root / "artifacts"
        self.artifacts.mkdir()
        (self.artifacts / "bundle").mkdir()
        (self.artifacts / "bundle" / "manifest.json").write_text("bundle")
        (self.artifacts / "model").mkdir()
        (self.artifacts / "model" / "shard-1.bin").write_bytes(b"model")
        (self.artifacts / "runner.bin").write_bytes(b"runner")
        (self.artifacts / "runtime.bin").write_bytes(b"runtime")
        self.paths = {"bundle": "bundle", "model": "model",
                      "runner": "runner.bin", "runtime": "runtime.bin"}
        osinfo = {"family": platform.system().lower(), "version": platform.version(),
                  "arch": platform.machine()}
        self.workload = {
            "schema": "MRL_Workload_Manifest_v1", "origin_signature": "MrLiouWord",
            "source_commit": "a" * 40, "track": "dl580-v100", "gpu_ids": [0],
            "bundle_id": "MRL_APIWorks_BYOH_DL580_V100_CUDA12_v1",
            "bundle_digest": gate.artifact_digest(self.artifacts, self.paths["bundle"]),
            "os": copy.deepcopy(osinfo), "cuda_runtime": "12.2", "runtime_abi": "cuda-12",
            "toolkit": "12.2", "quantization": "fp16",
            "runner": {"id": "test-runner", "version": "1.0.0",
                       "digest": gate.artifact_digest(self.artifacts, self.paths["runner"])},
            "runtime_binary": {"id": "cuda-runtime", "version": "12.2",
                               "digest": gate.artifact_digest(self.artifacts, self.paths["runtime"])},
            "model": {"id": "test-model", "version": "1.0.0",
                      "digest": gate.artifact_digest(self.artifacts, self.paths["model"])},
            "image": {"id": "native", "cuda_major": 0},
        }
        self.host = {
            "schema": "MRL_Hardware_Manifest_v1", "origin_signature": "MrLiouWord",
            "observation": "current", "os": osinfo,
            "driver": {"vendor": "NVIDIA", "version": "539.56"},
            "loaded_runner": copy.deepcopy(self.workload["runner"]),
            "loaded_runtime": copy.deepcopy(self.workload["runtime_binary"]),
            "loaded_image": "native",
            "gpus": [{"id": 0, "uuid": "GPU-test-only", "vendor": "NVIDIA",
                      "architecture": "Volta", "sku": "Tesla V100-SXM2-32GB",
                      "compute_capability": "7.0", "vram_mib": 32768}],
        }
        self.commands = {
            "runtime_smoke": {"argv": ["runtime-smoke"], "expected_stdout_sha256": "a" * 64},
            "model_smoke": {"argv": ["model-smoke"], "expected_stdout_sha256": "b" * 64},
        }

    def test_pass_is_only_a_local_smoke_candidate(self):
        with patch.object(smoke, "_device_query", return_value={"ok": True, "inventory_digest": "test"}), \
                patch.object(smoke, "_run_smoke", return_value={
                    "ok": True, "exit_code": 0, "stdout_sha256": "a" * 64, "stderr_sha256": "c" * 64,
                }):
            record = smoke.build_record(
                self.host, self.workload, self.artifacts, self.paths, self.commands,
            )
        self.assertEqual(record["status"], "smoke_passed_pending_restart_and_owner_review")
        self.assertNotEqual(record["status"], "hardware_verified")
        self.assertEqual(set(record["checks"]), {"device_query", "runtime_smoke", "model_smoke"})

    def test_replay_binds_same_configuration_and_receipt(self):
        with patch.object(smoke, "_device_query", return_value={"ok": True, "inventory_digest": "test"}), \
                patch.object(smoke, "_run_smoke", return_value={
                    "ok": True, "exit_code": 0, "stdout_sha256": "a" * 64, "stderr_sha256": "c" * 64,
                }):
            first = smoke.build_record(
                self.host, self.workload, self.artifacts, self.paths, self.commands,
            )
            replay = smoke.build_record(
                self.host, self.workload, self.artifacts, self.paths, self.commands, first,
            )
        self.assertEqual(replay["replay_of_digest"], first["record_digest"])

    def test_changed_artifact_or_configuration_blocks_replay(self):
        with patch.object(smoke, "_device_query", return_value={"ok": True, "inventory_digest": "test"}), \
                patch.object(smoke, "_run_smoke", return_value={
                    "ok": True, "exit_code": 0, "stdout_sha256": "a" * 64, "stderr_sha256": "c" * 64,
                }):
            first = smoke.build_record(
                self.host, self.workload, self.artifacts, self.paths, self.commands,
            )
            (self.artifacts / "model" / "shard-1.bin").write_bytes(b"changed")
            with self.assertRaises(ValueError):
                smoke.build_record(
                    self.host, self.workload, self.artifacts, self.paths, self.commands, first,
                )

    def test_smoke_command_hash_mismatch_fails(self):
        output = b"unexpected"
        with patch.object(smoke.subprocess, "run", return_value=type("Completed", (), {
            "returncode": 0, "stdout": output, "stderr": b"",
        })()):
            result = smoke._run_smoke("runtime_smoke", self.commands["runtime_smoke"])
        self.assertFalse(result["ok"])
        self.assertEqual(result["stdout_sha256"], hashlib.sha256(output).hexdigest())

    def test_device_query_checks_live_uuid_and_compute_capability(self):
        response = type("Completed", (), {
            "stdout": "0, GPU-test-only, Tesla V100-SXM2-32GB, 539.56, 32768 MiB\n",
        })()
        torch = type("Torch", (), {
            "cuda": type("Cuda", (), {
                "is_available": staticmethod(lambda: True),
                "device_count": staticmethod(lambda: 1),
                "get_device_capability": staticmethod(lambda gpu_id: (7, 0)),
            })(),
        })()
        with patch.object(smoke.subprocess, "run", return_value=response), \
                patch.dict(sys.modules, {"torch": torch}):
            self.assertTrue(smoke._device_query(self.host)["ok"])
            self.host["gpus"][0]["uuid"] = "GPU-other"
            with self.assertRaisesRegex(ValueError, "differs from the current Passport"):
                smoke._device_query(self.host)

    def test_tampered_replay_record_is_rejected(self):
        with patch.object(smoke, "_device_query", return_value={"ok": True, "inventory_digest": "test"}), \
                patch.object(smoke, "_run_smoke", return_value={
                    "ok": True, "exit_code": 0, "stdout_sha256": "a" * 64, "stderr_sha256": "c" * 64,
                }):
            first = smoke.build_record(
                self.host, self.workload, self.artifacts, self.paths, self.commands,
            )
            first["checks"]["model_smoke"]["ok"] = False
            with self.assertRaisesRegex(ValueError, "replay record"):
                smoke.build_record(
                    self.host, self.workload, self.artifacts, self.paths, self.commands, first,
                )

    def test_nonzero_smoke_command_fails_even_with_expected_stdout(self):
        output = b"expected"
        command = {
            "argv": ["runtime-smoke"],
            "expected_stdout_sha256": hashlib.sha256(output).hexdigest(),
        }
        with patch.object(smoke.subprocess, "run", return_value=type("Completed", (), {
            "returncode": 1, "stdout": output, "stderr": b"failed",
        })()):
            result = smoke._run_smoke("runtime_smoke", command)
        self.assertFalse(result["ok"])
        self.assertEqual(result["exit_code"], 1)


if __name__ == "__main__":
    unittest.main()
