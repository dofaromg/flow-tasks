from contextlib import redirect_stderr
import hashlib
import io
import json
from pathlib import Path
import re
import runpy
import subprocess
import sys
import tempfile
import time
import unittest
from unittest.mock import patch
from urllib.error import HTTPError
from urllib.request import Request, urlopen
import zipfile

from audit_delivery import MANIFEST, build, verify
from mrl_local import verify_job
from mrl_package import extract_verified, verify_package
from mrl_runtime import Runtime

HOME = Path(__file__).resolve().parent


class DeliveryChecks(unittest.TestCase):
    def test_audit_accepts_intact_zip_and_rejects_modified_zip(self):
        with tempfile.TemporaryDirectory() as temp:
            intact = Path(temp) / "intact.zip"
            built = build(intact)
            self.assertEqual(built["status"], "DELIVERY_PASS")
            self.assertEqual(built["expected"], 15)
            self.assertEqual(built["zip_count"], 15)
            self.assertEqual(built["coverage"], 100)
            with zipfile.ZipFile(intact) as archive:
                members = {name: archive.read(name) for name in archive.namelist()}

            for name, content in (("README.md", b"modified"), (MANIFEST, b"{invalid json")):
                with self.subTest(member=name):
                    tampered = Path(temp) / "tampered.zip"
                    with zipfile.ZipFile(tampered, "w") as archive:
                        for member, data in {**members, name: content}.items():
                            archive.writestr(member, data)
                    failed = verify(tampered)
                    self.assertEqual(failed["status"], "DELIVERY_FAIL")
                    self.assertEqual(failed["coverage"], 100)
                    self.assertIn("package manifest" if name == MANIFEST else name, failed["mismatch"])
                    cli = subprocess.run(
                        [sys.executable, "-X", "utf8", str(HOME / "audit_delivery.py"),
                         "verify", str(tampered)], capture_output=True, timeout=10)
                    self.assertEqual(cli.returncode, 1)
                    self.assertEqual(json.loads(cli.stdout), failed)

    def test_cli_distinguishes_interrupt_from_failure(self):
        for error, code, message in (
            (KeyboardInterrupt(), 130, "Interrupted by operator"),
            (RuntimeError("unexpected error"), 1, "unexpected error"),
        ):
            with self.subTest(error=type(error).__name__):
                stderr = io.StringIO()
                with patch("argparse.ArgumentParser.parse_args", side_effect=error), redirect_stderr(stderr):
                    with self.assertRaises(SystemExit) as exit_status:
                        runpy.run_path(str(HOME / "mrl_local.py"), run_name="__main__")
                self.assertEqual(exit_status.exception.code, code)
                self.assertEqual(stderr.getvalue().strip(), message)


class Deployment(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.data = self.root / "data"
        self.runtime = Runtime(self.data)

    def run_job(self, kind, value, expected="done", **options):
        job = self.runtime.submit(kind, value, **options)
        row = self.runtime.step()
        self.assertEqual(row["id"], job)
        self.assertEqual(row["status"], expected, row)
        return row

    def artifact(self, row):
        return self.data / "artifacts" / row["result"]["file"]

    def test_generation_repackage_and_cache_corruption(self):
        first = self.run_job("generate", "MRL 粒子")
        second = self.run_job("generate", "MRL 粒子")
        self.assertFalse(first["result"]["cache_hit"])
        self.assertTrue(second["result"]["cache_hit"])
        self.assertEqual(first["result"]["sha256"], second["result"]["sha256"])
        third = self.run_job("generate", "MRL 粒子", target="different")
        self.assertFalse(third["result"]["cache_hit"])
        changed = self.run_job("generate", "MRL 粒子", options={"version": 2})
        self.assertFalse(changed["result"]["cache_hit"])
        for label in ("one", "two"):
            pack = self.run_job("package", "", source_job=first["id"], options={"label": label})
            self.assertEqual(pack["parent"], first["id"])
            self.assertEqual(verify_package(self.artifact(pack))["label"], label)
            verify_job(self.runtime, pack["id"])
        cache = self.data / "cache" / first["result"]["cache_key"]
        cache.unlink()
        cache.write_text("broken")
        recovered = self.run_job("generate", "MRL 粒子")
        self.assertFalse(recovered["result"]["cache_hit"])
        self.assertTrue(list(cache.parent.glob("*.invalid.*")))
        self.assertEqual(first["result"]["sha256"], recovered["result"]["sha256"])

    def test_large_roundtrip_and_legacy_compatibility(self):
        source = self.root / "來源"
        source.mkdir()
        payload = bytes(range(256)) * 16000
        (source / "粒子.fltnz").write_bytes(payload)
        row = self.run_job("package", str(source))
        destination = self.root / "還原"
        manifest = extract_verified(self.artifact(row), destination)
        self.assertEqual((destination / "粒子.fltnz").read_bytes(), payload)
        self.assertEqual(manifest["files"][0]["sha256"], hashlib.sha256(payload).hexdigest())
        legacy = self.root / "legacy.zip"
        original = HOME / "下載重建器腳本MRLiou_FLPKG_Rebuilder.py"
        if not original.exists():
            original = HOME.parent / original.name
        # Use text for the legacy tool to avoid a giant first-line preview.
        (source / "粒子.fltnz").write_text("particle", encoding="utf-8")
        subprocess.run([sys.executable, "-X", "utf8", str(original), "build", str(source), "--out", str(legacy)],
                       check=True, capture_output=True)
        self.assertIn("sha1", verify_package(legacy)["files"][0])
        self.run_job("package", str(self.root), expected="failed")

    def test_quota_wait_deny_cancel_and_child(self):
        self.runtime.config(1, "deny", 1024)
        denied = self.run_job("generate", "seed", expected="denied")
        self.assertEqual(self.runtime.status()["quota"]["used_bytes"], 0)
        self.runtime.config(100000, "deny", 1024)
        child = self.runtime.retry(denied["id"])
        row = self.runtime.step()
        self.assertEqual((row["id"], row["parent"], row["status"]), (child, denied["id"], "done"))
        amount = self.runtime.status()["quota"]["used_bytes"]
        self.runtime.config(amount + 1, "queue", 1024)
        waiting = self.run_job("generate", "next", expected="waiting")
        self.runtime.cancel(waiting["id"])
        self.assertEqual(self.runtime.status(waiting["id"])["status"], "cancelled")

    def test_diagnostic_and_malicious_zip(self):
        sample = self.root / "synthetic.ips"
        sample.write_text('{"incident_id":"SYNTHETIC","bug_type":"145"}\n'
                          'Event: disk writes\nAction taken: none\nVM page size: 16384\n'
                          'Writes: 10.00 MB of file backed memory dirtied over 100 seconds '
                          '(100.00 KB per second average), exceeding limit of 10.00 KB per second over 86400 seconds\n'
                          'Powerstats for:   ANECompilerService\nPageins: 2 pages\n'
                          '  1 ??? (ANECompiler + 20)\n', encoding="utf-8")
        raw = sample.read_bytes()
        row = self.run_job("diagnostic", str(sample))
        data = json.loads(self.artifact(row).read_bytes())
        self.assertEqual(data["derived"], {"event_to_reference_rate_ratio": 10,
                                         "pagein_page_size_product_bytes": 32768})
        self.assertEqual(data["source_sha256"], hashlib.sha256(raw).hexdigest())
        self.assertEqual(sample.read_bytes(), raw)
        self.assertFalse(data["hypotheses"])
        path = self.root / "bad.zip"
        with zipfile.ZipFile(path, "w") as archive:
            archive.writestr("../escape", "invalid")
        with self.assertRaises(ValueError):
            extract_verified(path, self.root / "extracted")
        self.assertFalse((self.root / "escape").exists())
        self.assertFalse((self.root / "extracted").exists())

    def test_two_workers_and_restart_after_kill(self):
        self.runtime.config(1, "throttle", 128)
        job = self.runtime.submit("generate", "x" * 65536)
        command = [sys.executable, str(HOME / "mrl_local.py"), "--data", str(self.data),
                   "worker", "--once"]
        first = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        try:
            for _ in range(100):
                if (self.data / "stage" / (job + ".tmp")).exists():
                    break
                time.sleep(0.03)
            self.assertEqual(self.runtime.status(job)["status"], "running")
            other = subprocess.run(command, capture_output=True, timeout=10, check=True)
            self.assertIsNone(json.loads(other.stdout))
        finally:
            if first.poll() is None:
                first.kill()
            first.communicate(timeout=10)
        self.runtime.config(10 * 1024 * 1024, "deny", 1024)
        self.runtime.step()
        self.assertEqual(self.runtime.status(job)["status"], "interrupted")
        self.assertFalse(list((self.data / "stage").iterdir()))
        child = self.runtime.retry(job)
        row = self.runtime.step()
        self.assertEqual((row["id"], row["parent"], row["status"]), (child, job, "done"))

    def test_local_web_flow(self):
        command = [sys.executable, str(HOME / "mrl_local.py"), "--data", str(self.data),
                   "serve", "--port", "0"]
        server = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        try:
            url = server.stdout.readline().strip()
            self.assertTrue(url.startswith("http://127.0.0.1:"))
            with urlopen(url, timeout=5) as page:
                html = page.read().decode()
            self.assertIn("MRL FLPKG 本地工作台", html)
            token = re.search(r"const token = '([^']+)'", html)[1]

            def call(path, data, authorized=True):
                headers = {"Content-Type": "application/json"}
                if authorized:
                    headers["X-MRL-Token"] = token
                request = Request(url + "api/" + path, json.dumps(data).encode(), headers)
                with urlopen(request, timeout=5) as reply:
                    return json.load(reply)

            with self.assertRaises(HTTPError) as failure:
                call("status", {}, authorized=False)
            self.assertEqual(failure.exception.code, 403)
            job = call("submit", {"kind": "generate", "value": "console"})["job"]
            for _ in range(100):
                if call("status", {"job": job})["status"] == "done":
                    break
                time.sleep(0.05)
            self.assertEqual(len(call("verify", {"job": job})["sha256"]), 64)
        finally:
            server.terminate()
            server.communicate(timeout=10)


if __name__ == "__main__":
    unittest.main()
