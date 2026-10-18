"""Real loopback connector boundary. origin_signature: MrLiouWord"""
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from threading import Thread
import unittest

from .base_connector import ConnectorConfig
from .github_connector import GitHubConnector
from MRL_Bridge.translation_center import TranslationCenter


class ConnectorBoundaryTests(unittest.TestCase):
    def test_request_and_response_tagged_without_modifying_payload(self):
        observed = []
        class Receiver(BaseHTTPRequestHandler):
            def do_POST(self):
                observed.append((dict(self.headers), self.rfile.read(int(self.headers["Content-Length"]))))
                self.send_response(403)
                self.end_headers()
                self.wfile.write(b'{"origin_signature":"external"}')
            def log_message(self, *args):
                pass
        server = ThreadingHTTPServer(("127.0.0.1", 0), Receiver)
        thread = Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            connector = GitHubConnector(ConnectorConfig())
            connector.mrl_bridge_center = TranslationCenter()
            payload = {"original_name": "MRL_module.py"}
            response = connector._make_request("POST", f"http://127.0.0.1:{server.server_port}", json_data=payload)
            self.assertEqual(response.status_code, 403)
            headers, raw = observed[0]
            self.assertEqual(headers["X-MRL-Affiliation"], "MRL")
            self.assertEqual(payload, {"original_name": "MRL_module.py"})
            self.assertIn(b"MRL_module.py", raw)
            receipt = connector.last_mrl_bridge_receipt
            self.assertEqual(receipt["trace_id"], headers["X-MRL-Trace-Id"])
            self.assertEqual(receipt["status"], "received")
            self.assertEqual(receipt["http_status"], 403)
            self.assertEqual(response.json()["origin_signature"], "external")
        finally:
            server.shutdown()
            server.server_close()
            thread.join()
