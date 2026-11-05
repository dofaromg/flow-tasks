"""Synthetic fixtures. No real tailnet, credentials or server configuration."""

import base64
import errno
import json
import tempfile
import threading
import unittest
import uuid
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import MRL_tailnet_cross_device_receipt_v1 as receipt


class BridgeFixture(BaseHTTPRequestHandler):
    health_status = 200
    identity = "MRL_Bridge_API"
    canary = str(uuid.uuid4()).encode()

    def send_json(self, status, body):
        payload = json.dumps(body).encode()
        self.send_response(status)
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def do_GET(self):
        self.send_json(self.health_status, {
            "service": self.identity, "api": True, "pg": True, "redis": True,
        })

    def do_POST(self):
        body = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
        if self.headers.get("x-api-key") != "synthetic-key":
            self.send_json(403, {})
        elif self.path == "/MRL_file/read" and body["encoding"] == "base64":
            self.send_json(200, {"ok": True, "content": base64.b64encode(self.canary).decode()})
        else:
            self.send_json(404, {})

    def log_message(self, *_):
        pass


class EndpointTest(unittest.TestCase):
    def setUp(self):
        self.server = HTTPServer(("127.0.0.1", 0), BridgeFixture)
        worker = threading.Thread(target=self.server.serve_forever, daemon=True)
        worker.start()
        self.addCleanup(self.server.server_close)
        self.addCleanup(worker.join)
        self.addCleanup(self.server.shutdown)
        port, path, field, identity = receipt.SERVICES[receipt.BRIDGE]
        fixture = (self.server.server_port, path, field, identity)
        self.enterContext(patch.dict(receipt.SERVICES, {receipt.BRIDGE: fixture}))

    def health(self):
        return receipt.endpoint("127.0.0.1", None, receipt.BRIDGE, 1)

    def readback(self, key="synthetic-key", digest=None):
        return receipt.readback(
            "127.0.0.1", None, self.health()["identity"], r"D:\MRL_Tailnet_Canary.txt",
            digest or receipt.sha(BridgeFixture.canary), 1, key,
        )

    def test_normal(self):
        self.assertEqual(self.health()["health"], "PASS")
        self.assertEqual(self.readback()["result"], "PASS")

    def test_403_is_reachable_without_authorization(self):
        with patch.object(BridgeFixture, "health_status", 403):
            result = self.health()
        self.assertEqual((result["tcp"], result["http"], result["status"]),
                         ("PASS", "RESPONSE", 403))
        self.assertEqual(result["authorization"], "REJECTED")
        self.assertEqual(self.readback("wrong-key")["result"], "AUTH_REJECTED")

    def test_wrong_content(self):
        self.assertEqual(self.readback(digest="0" * 64)["result"], "READBACK_MISMATCH")

    def test_scanner_identity_does_not_pass_as_bridge(self):
        with patch.object(BridgeFixture, "identity", "MRL_3DScanner_ProductBridge"):
            self.assertEqual(self.health()["identity"], "IDENTITY_MISMATCH")
            self.assertEqual(self.readback()["result"], "BRIDGE_IDENTITY_UNVERIFIED")

    def test_tcp_timeout(self):
        with patch.object(receipt.socket, "create_connection", side_effect=TimeoutError):
            result = self.health()
        self.assertEqual((result["tcp"], result["http"]), ("TIMEOUT", "UNRUN"))

    def test_connection_refused(self):
        with patch.object(receipt.socket, "create_connection",
                          side_effect=ConnectionRefusedError(errno.ECONNREFUSED, "fixture")):
            self.assertEqual(self.health()["tcp"], "CONNECTION_REFUSED")

    def test_no_redirect(self):
        with patch.object(BridgeFixture, "health_status", 302):
            self.assertEqual(self.health()["status"], 302)


class PingTest(unittest.TestCase):
    def test_routes_and_wrong_peer(self):
        peer = "100.64.1.2"
        raw = {"stdout": (
            "pong from other (100.64.1.9) via 192.0.2.8:555 in 1ms\n"
            "pong from node (100.64.1.2) via DERP(tok) in 13ms\n"
            "pong from node (100.64.1.2) via [2001:db8::1]:555 in 4ms\n"
            "pong from node (100.64.1.2) via peer-relay(peer) in 5ms\n"
        ), "stderr": "", "result": "PASS"}
        self.assertEqual(receipt.ping_result(raw, peer), {
            "result": "PASS", "observed_routes": ["DERP", "DIRECT", "PEER_RELAY"],
        })
        self.assertEqual(receipt.ping_result(raw, "100.64.1.3")["result"], "NO_MATCHING_PONG")

    def test_offline_is_peer_report_not_http_inference(self):
        peer = "100.64.1.2"
        status = {"BackendState": "Running",
                  "Peer": {"fixture": {"Online": False, "TailscaleIPs": [peer]}}}
        self.assertEqual(receipt.peer_state(status, peer), "PEER_REPORTED_OFFLINE")
        raw = {"stdout": "ping timed out\n", "stderr": "", "result": "COMMAND_FAILED"}
        self.assertEqual(receipt.ping_result(raw, peer)["result"], "TIMEOUT")

    def test_backend_stopped(self):
        self.assertEqual(receipt.peer_state({"BackendState": "Stopped"}, "100.64.1.2"),
                         "BACKEND_NOT_RUNNING")

    def test_http_probe_requires_a_recognized_peer(self):
        raw = {"result": "PASS", "stdout": "", "stderr": ""}
        status = {"BackendState": "Running", "Self": {"TailscaleIPs": ["100.64.1.1"]}}
        with tempfile.TemporaryDirectory() as temp, patch.object(
            receipt.platform, "system", return_value="Darwin"
        ), patch.object(receipt, "command", side_effect=[
            dict(raw, stdout=json.dumps(status)), dict(raw, stdout="100.64.1.1"), raw, raw,
        ]), patch.object(receipt, "endpoint") as probe:
            result = receipt.collect(SimpleNamespace(
                role="mac", tailscale="fixture", peer_ip="100.64.1.2", run_id=uuid.uuid4(),
                bridge_canary=None, canary_sha256=None, timeout=1, out_dir=Path(temp),
            ))
            parsed = receipt.verified_json(Path(result["file"]), result["sha256"])
        probe.assert_not_called()
        self.assertEqual(parsed["peer_state"], "PEER_NOT_IDENTIFIED")


class ReconcileTest(unittest.TestCase):
    def setUp(self):
        self.directory = Path(self.enterContext(tempfile.TemporaryDirectory()))
        self.timestamp = receipt.utc()
        self.common = {
            "schema": receipt.SCHEMA, "origin_signature": receipt.ORIGIN,
            "collector_sha256": "a" * 64, "run_id": str(uuid.uuid4()),
            "observed_at_utc": self.timestamp, "started_at_utc": self.timestamp,
            "ping": {"result": "PASS", "observed_routes": ["DERP"],
                     "extra": "must-not-export"},
            "bridge_readback": {"result": "PASS", "authorization": "ACCEPTED", "status": 200},
            "services": {}, "canary_sha256": receipt.sha(BridgeFixture.canary),
            "raw": {"stdout": "must-not-export"},
        }
        self.canary = self.directory / "canary.txt"
        self.canary.write_bytes(BridgeFixture.canary)
        self.windows = {
            "schema": "MRL_Tailnet_Bridge_Receipt_v1", "origin_signature": receipt.ORIGIN,
            "observed_at_utc": self.timestamp, "host_match": True,
            "tailscale": {"self_ips": ["100.64.1.2"]}, "services": [], "ports": [],
        }

    def args(self, **overrides):
        def make(name, value):
            index = receipt.write_receipt(self.directory, name, value)
            return Path(index["file"]), index["sha256"]

        mac, mac_hash = make("mac", dict(
            self.common, role="mac", self_ip="100.64.1.1", peer_ip="100.64.1.2",
        ))
        dl, dl_hash = make("dl", dict(
            self.common, role="dl580", self_ip="100.64.1.2", peer_ip="100.64.1.1",
        ))
        win, win_hash = make("windows", self.windows)
        fields = dict(mac=mac, mac_sha256=mac_hash, dl580=dl, dl580_sha256=dl_hash,
                      windows_receipt=win, windows_sha256=win_hash, canary=self.canary,
                      passport=None, out_dir=self.directory)
        return SimpleNamespace(**(fields | overrides))

    def test_paired_redacted_and_replay_safe(self):
        args = self.args()
        index = receipt.reconcile(args)
        result = receipt.verified_json(Path(index["file"]), index["sha256"])
        self.assertEqual(result["bidirectional_tailnet_ping"], "PASS")
        self.assertEqual(result["bridge_readback"]["result"], "PASS")
        self.assertEqual(result["iphone_to_dl580"], "UNRUN")
        self.assertNotIn("must-not-export", json.dumps(result))
        self.assertNotIn("100.64.", json.dumps(result))
        with self.assertRaises(FileExistsError):
            receipt.reconcile(args)

    def test_wrong_host_cannot_pass(self):
        self.windows["host_match"] = False
        index = receipt.reconcile(self.args())
        result = receipt.verified_json(Path(index["file"]), index["sha256"])
        self.assertEqual(result["bidirectional_tailnet_ping"], "UNKNOWN")
        self.assertEqual(result["bridge_readback"]["result"], "UNVERIFIED")

    def test_stale_or_tampered_input(self):
        self.windows["observed_at_utc"] = "2000-01-01T00:00:00+00:00"
        args = self.args()
        with self.assertRaisesRegex(ValueError, "time mismatch"):
            receipt.reconcile(args)
        args.mac.write_text("{}")
        with self.assertRaisesRegex(ValueError, "SHA-256 mismatch"):
            receipt.reconcile(args)

    def test_port_mixup_fails_reconciliation(self):
        self.common["services"][receipt.BRIDGE] = {"port": 3050, "path": "/health"}
        with self.assertRaisesRegex(ValueError, "port or health route mismatch"):
            receipt.reconcile(self.args())

    def test_canary_not_available_locally(self):
        index = receipt.reconcile(self.args(canary=None))
        result = receipt.verified_json(Path(index["file"]), index["sha256"])
        self.assertEqual(result["bridge_readback"]["result"], "LOCAL_CANARY_NOT_VERIFIED")


if __name__ == "__main__":
    unittest.main()
