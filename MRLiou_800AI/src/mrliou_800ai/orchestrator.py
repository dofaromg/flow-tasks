from __future__ import annotations
import re
from .registry import AgentRegistry
from .audit import EngineeringGate
from .trace import TraceChain

class Orchestrator:
    def __init__(self, registry: AgentRegistry, gate: EngineeringGate, trace: TraceChain):
        self.registry, self.gate, self.trace = registry, gate, trace

    def route(self, task: str) -> list[str]:
        t = task.lower()
        roles = ["architect", "engineer", "reviewer"]
        if re.search(r"bug|debug|錯誤|除錯|故障", t): roles.append("debugger")
        if re.search(r"performance|optimi|效能|速度|memory", t): roles.append("optimizer")
        if re.search(r"refactor|clean architecture|重構", t): roles.append("refactorer")
        if re.search(r"ui|frontend|component|介面|元件", t): roles.append("ui_builder")
        if re.search(r"cfd|physics|mass|momentum|energy|守恆|物理", t): roles.append("physics_auditor")
        return list(dict.fromkeys(roles))

    def dispatch(self, task: str, evidence: dict | None = None) -> dict:
        gate = self.gate.evaluate(task, evidence)
        roles = self.route(task)
        rec = self.trace.emit("task_dispatch", {"task": task, "roles": roles})
        return {"task": task, "assigned_roles": roles, "gate": gate, "trace_anchor": rec["merkle_root"]}
