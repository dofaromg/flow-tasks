import importlib.util
from pathlib import Path
import unittest
from unittest.mock import patch, Mock

SPEC = importlib.util.spec_from_file_location("bridge", Path(__file__).parents[1] / "adapters/mrl_github_notion_bridge.py")
bridge = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(bridge)
CONFIG = {
    "origin_signature": "MrLiouWord", "canonical_authority": "Mr.liou",
    "repository": "dofaromg/flow-tasks", "pull_requests": [677],
    "notion_authority_page": "3ede7f4e-6c55-8064-a840-e3a531cb2aef",
    "notion_receipt_page": "3e9e7f4e-6c55-80e4-9f3d-c8292dda835a",
}


class Fake:
    def __init__(self):
        self.texts = []
        self.writes = 0
        self.hide_write = False
        self.fail_write = False

    def call(self, service, method, path, payload=None):
        if service == "github":
            return {"head": {"sha": "a" * 40}, "base": {"sha": "b" * 40},
                    "state": "open", "merged": False, "updated_at": "2026-10-20T00:00:00Z"}
        if method == "PATCH":
            self.writes += 1
            if self.fail_write:
                raise bridge.BridgeError("Notion HTTP 403")
            if not self.hide_write:
                self.texts.append(payload["children"][0]["paragraph"]["rich_text"][0]["text"]["content"])
            return {"results": []}
        if path.startswith("/pages/"):
            return {"object": "page", "id": path.split("/")[-1], "last_edited_time": "2026-10-19T00:00:00Z"}
        return {"results": [{"type": "paragraph", "paragraph": {"rich_text": [{"plain_text": t}]}} for t in self.texts],
                "has_more": False}


class Tests(unittest.TestCase):
    def test_plan_has_no_write(self):
        api = Fake()
        report = bridge.sync(CONFIG, api)
        self.assertEqual(api.writes, 0)
        self.assertEqual(report["receipts"][0]["status"], "PLANNED")

    def test_append_readback_and_repeat(self):
        api = Fake()
        first = bridge.sync(CONFIG, api, True)
        second = bridge.sync(CONFIG, api, True)
        self.assertEqual(first["receipts"][0]["status"], "APPEND_READBACK_PASS")
        self.assertEqual(second["receipts"][0]["status"], "ALREADY_VERIFIED")
        self.assertEqual(api.writes, 1)

    def test_readback_failure_is_not_pass(self):
        api = Fake()
        api.hide_write = True
        with self.assertRaises(bridge.BridgeError):
            bridge.sync(CONFIG, api, True)

    def test_denied_write_is_not_retried(self):
        api = Fake()
        api.fail_write = True
        with self.assertRaises(bridge.BridgeError):
            bridge.sync(CONFIG, api, True)
        self.assertEqual(api.writes, 1)

    def test_conflicting_receipt_refused(self):
        api = Fake()
        bridge.sync(CONFIG, api, True)
        api.texts[0] += " altered"
        with self.assertRaises(bridge.BridgeError):
            bridge.sync(CONFIG, api, True)
        self.assertEqual(api.writes, 1)

    def test_duplicate_receipt_refused(self):
        api = Fake()
        bridge.sync(CONFIG, api, True)
        api.texts *= 2
        with self.assertRaises(bridge.BridgeError):
            bridge.sync(CONFIG, api, True)

    def test_page_pagination(self):
        api = Mock()
        api.call.side_effect = [
            {"results": [], "has_more": True, "next_cursor": "cursor/2"},
            {"results": [{"type": "paragraph", "paragraph": {"rich_text": [{"plain_text": "last"}]}}], "has_more": False}]
        self.assertEqual(list(bridge.paragraphs(api, CONFIG["notion_receipt_page"])), ["last"])
        self.assertIn("cursor%2F2", api.call.call_args.args[2])

    def test_incomplete_pagination_fails(self):
        api = Mock()
        api.call.return_value = {"results": [], "has_more": True, "next_cursor": None}
        with self.assertRaises(bridge.BridgeError):
            list(bridge.paragraphs(api, CONFIG["notion_receipt_page"]))

    def test_authority_mismatch_refused_before_requests(self):
        api = Mock()
        with self.assertRaises(bridge.BridgeError):
            bridge.sync(dict(CONFIG, canonical_authority="external"), api, True)
        api.call.assert_not_called()

    def test_missing_credentials(self):
        with self.assertRaises(bridge.BridgeError):
            bridge.Client("", "")

    @patch.object(bridge.urllib.request, "build_opener")
    def test_redirect_and_error_body_not_exposed(self, opener):
        opener.return_value.open.side_effect = bridge.urllib.error.HTTPError(
            "https://api.notion.com/v1/users/me", 302, "SECRET", {}, None)
        with self.assertRaises(bridge.BridgeError) as result:
            bridge.Client("gh-value", "nt-value").call("notion", "GET", "/users/me")
        self.assertNotIn("SECRET", str(result.exception))
        self.assertIsInstance(opener.call_args.args[0], bridge.NoRedirect)
        self.assertIsNone(bridge.NoRedirect().redirect_request(None, None, 302, "", {}, "https://example.com"))


if __name__ == "__main__":
    unittest.main()
