import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "MRL_validate_existing_mother_preflight_v1.py"
BASE = json.loads((ROOT / "MRL_Existing_Mother_Preflight_v1.json").read_text(encoding="utf-8"))


class TestExistingMotherPreflight(unittest.TestCase):
    def run_case(self, patch, should_pass):
        data = dict(BASE)
        data.update(patch)
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "preflight.json"
            p.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
            cp = subprocess.run([sys.executable, str(SCRIPT), str(p)], capture_output=True, text=True)
        if should_pass:
            self.assertEqual(cp.returncode, 0, cp.stderr + cp.stdout)
            self.assertIn("MRL_EXISTING_MOTHER_PREFLIGHT_PASS", cp.stdout)
        else:
            self.assertNotEqual(cp.returncode, 0)
        return cp

    def test_existing_definition_maps_without_rebuild(self):
        cp = self.run_case({
            "operation": "MAP_EXISTING",
            "existing_node_found": True,
            "parallel_mother_created": False,
            "existing_mother_position": "origin_registry/existing_definition"
        }, True)
        self.assertIn("operation=MAP_EXISTING", cp.stdout)

    def test_existing_definition_can_be_supplemented(self):
        self.run_case({
            "operation": "SUPPLEMENT_EXISTING",
            "existing_node_found": True,
            "parallel_mother_created": False
        }, True)

    def test_existing_definition_cannot_create_new(self):
        self.run_case({
            "operation": "CREATE_NEW",
            "existing_node_found": True
        }, False)

    def test_missing_definition_cannot_map_existing(self):
        self.run_case({
            "operation": "MAP_EXISTING",
            "existing_node_found": False
        }, False)

    def test_create_new_allowed_only_when_absent_and_backfilled(self):
        self.run_case({
            "operation": "CREATE_NEW",
            "existing_node_found": False,
            "existing_mother_position": None,
            "parallel_mother_created": False,
            "create_new_requires_no_existing_node": True,
            "backfill_required_after_create": True
        }, True)

    def test_missing_wake_memory_fails(self):
        chain = [x for x in BASE["required_lookup_chain"] if x != "Wake Memory"]
        self.run_case({"required_lookup_chain": chain}, False)


if __name__ == "__main__":
    unittest.main()
