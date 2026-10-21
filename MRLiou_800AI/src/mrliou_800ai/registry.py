from __future__ import annotations
import json
from pathlib import Path

class AgentRegistry:
    def __init__(self, config_dir: Path):
        self.agents = json.loads((config_dir / "agents.json").read_text(encoding="utf-8"))
        self.organization = json.loads((config_dir / "organization.json").read_text(encoding="utf-8"))

    def list_agents(self) -> list[dict]:
        allocation = self.organization["allocation"]
        return [{**role, "logical_instances": allocation.get(role["id"], 0)}
                for role in self.agents["role_families"]]
