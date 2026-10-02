import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "MRL_aggregate_attestations_v1.py"
HASH = "a" * 64


def att(node, decision):
    return {
        "attestation_id": f"att-{node}",
        "event_id": "evt-1",
        "node_id": node,
        "node_class": "OTHER_PRIVATE_NODE",
        "observed_record_hash": HASH,
        "decision": decision,
        "evidence_refs": ["ref"],
        "created_at": "2026-09-13T00:00:00Z",
        "origin_signature": "MrLiouWord"
    }


class TestAggregator(unittest.TestCase):
    def run_case(self, decisions):
        with tempfile.TemporaryDirectory() as d:
            paths = []
            for i, decision in enumerate(decisions):
                p = Path(d) / f"{i}.json"
                p.write_text(json.dumps(att(f"n{i}", decision)), encoding="utf-8")
                paths.append(str(p))
            cp = subprocess.run([sys.executable, str(SCRIPT), *paths], capture_output=True, text=True, check=True)
            return json.loads(cp.stdout)

    def test_consensus(self):
        self.assertEqual(self.run_case(["CONFIRM","CONFIRM"])["consensus_state"], "CONSENSUS")

    def test_partial(self):
        self.assertEqual(self.run_case(["CONFIRM","PARTIAL"])["consensus_state"], "PARTIAL_CONSENSUS")

    def test_dissent_preserved(self):
        self.assertEqual(self.run_case(["CONFIRM","DISSENT"])["consensus_state"], "DISSENT_PRESERVED")

    def test_unresolved(self):
        self.assertEqual(self.run_case(["UNRESOLVED","UNRESOLVED"])["consensus_state"], "UNRESOLVED")


if __name__ == "__main__":
    unittest.main()
