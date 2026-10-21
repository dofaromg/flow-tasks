import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from mrliou_800ai.security import authentication_enabled, is_authorized


class SecurityTests(unittest.TestCase):
    def test_no_token_keeps_local_compatibility(self):
        with tempfile.TemporaryDirectory() as td:
            with patch.dict(os.environ, {"MRL_HOME": td, "MRL_API_TOKEN": ""}, clear=False):
                self.assertFalse(authentication_enabled())
                self.assertTrue(is_authorized({}))

    def test_header_token_is_required_when_configured(self):
        with tempfile.TemporaryDirectory() as td:
            token_dir = Path(td) / "secrets"
            token_dir.mkdir()
            (token_dir / "api_token.txt").write_text("secret-value", encoding="utf-8")
            with patch.dict(os.environ, {"MRL_HOME": td, "MRL_API_TOKEN": ""}, clear=False):
                self.assertTrue(authentication_enabled())
                self.assertFalse(is_authorized({}))
                self.assertFalse(is_authorized({"X-MRL-Token": "wrong"}))
                self.assertTrue(is_authorized({"X-MRL-Token": "secret-value"}))
                self.assertTrue(is_authorized({"Authorization": "Bearer secret-value"}))


if __name__ == "__main__":
    unittest.main()
