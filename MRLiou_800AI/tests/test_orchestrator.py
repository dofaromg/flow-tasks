import json, tempfile, unittest
from pathlib import Path
from mrliou_800ai.registry import AgentRegistry
from mrliou_800ai.audit import EngineeringGate
from mrliou_800ai.trace import TraceChain
from mrliou_800ai.orchestrator import Orchestrator

class OrchestratorTests(unittest.TestCase):
    def test_physics_routing(self):
        root=Path(__file__).resolve().parents[1]
        o=Orchestrator(AgentRegistry(root/"config"), EngineeringGate(), TraceChain(root/"logs"))
        result=o.dispatch("audit CFD mass conservation performance")
        self.assertIn("physics_auditor", result["assigned_roles"])
        self.assertIn("optimizer", result["assigned_roles"])

if __name__ == "__main__": unittest.main()
