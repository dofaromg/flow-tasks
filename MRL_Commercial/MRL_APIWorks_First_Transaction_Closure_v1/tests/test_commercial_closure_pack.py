from __future__ import annotations

import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

class CommercialClosurePackTests(unittest.TestCase):
    def test_package_integrity(self) -> None:
        completed = subprocess.run(
            [sys.executable, "scripts/MRL_verify_commercial_closure_pack_v1.py"],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)

if __name__ == "__main__":
    unittest.main()