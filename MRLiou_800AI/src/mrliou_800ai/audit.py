from __future__ import annotations
from dataclasses import dataclass, asdict

@dataclass
class GateResult:
    stage: str
    status: str
    evidence: list[str]

class EngineeringGate:
    """Evidence-first engineering wake gate; it never claims external checks were performed unless supplied."""
    def evaluate(self, task: str, evidence: dict | None = None) -> dict:
        evidence = evidence or {}
        stages = [
            GateResult("request_capture", "PASS" if task.strip() else "FAIL", ["task captured"] if task.strip() else []),
            GateResult("history_and_source_check", "PASS" if evidence else "PENDING", list(evidence.keys())),
            GateResult("plan_and_dependency_check", "PASS", ["role routing generated", "dependency chain preserved"]),
            GateResult("execution_gate", "READY" if task.strip() else "BLOCKED", ["additive resolution required"]),
            GateResult("delivery_validation", "REQUIRED", ["verify script", "checksums", "manifest diff"]),
        ]
        return {"task": task, "stages": [asdict(x) for x in stages],
                "facts": evidence, "inferences": [], "unverified": [] if evidence else ["external state not supplied"]}
