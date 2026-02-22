"""
Fluin Language — High-level DSL for particle operations
origin_signature: MrLiouWord

Syntax:
  ⏤particle.anchor⏤ := { type: "anchor", position: [0,0,0], energy: 1.0 }
  ⏤transform⏤ := EXPAND(particle.seed, level=2) ⊕ COMBINE(particle.jump, particle.fusion)
  ⏤jump⏤ := JUMP(particle.memory, FROM: R2, TO: R4) ∙ CHECK(energy > threshold)

Also handles .flpkg package loading.
"""

import json
import re
import time
from typing import Any, Dict, List, Optional, Tuple

from .particle_types import Particle, ParticleType, ParticleField, ANCHOR, SEED, JUMP, MEMORY, FUSION


# Token types
TOK_DEFINE = "DEFINE"       # ⏤name⏤ :=
TOK_EXPAND = "EXPAND"
TOK_COMPRESS = "COMPRESS"
TOK_COMBINE = "COMBINE"     # ⊕
TOK_JUMP = "JUMP"
TOK_CHECK = "CHECK"
TOK_CREATE = "CREATE"
TOK_LITERAL = "LITERAL"
TOK_REF = "REF"             # particle.name reference
TOK_EOF = "EOF"

TYPE_MAP = {
    "anchor": ANCHOR,
    "seed": SEED,
    "jump": JUMP,
    "memory": MEMORY,
    "fusion": FUSION,
}


class FluinToken:
    def __init__(self, ttype: str, value: Any = None, params: Optional[Dict] = None):
        self.ttype = ttype
        self.value = value
        self.params = params or {}

    def __repr__(self):
        return f"Token({self.ttype}, {self.value})"


class FluinInterpreter:
    """
    Interprets Fluin DSL statements.

    Supports:
      - Particle creation: ⏤name⏤ := { type: "anchor", ... }
      - EXPAND(ref, level=N)
      - COMPRESS(ref, level=N)
      - COMBINE(ref1, ref2) or ref1 ⊕ ref2
      - JUMP(ref, FROM: RX, TO: RY)
      - CHECK(energy > threshold)
    """

    def __init__(self):
        self.field = ParticleField("fluin")
        self.variables: Dict[str, Particle] = {}
        self.results: List[Dict] = []
        self.origin_signature = "MrLiouWord"

    def execute(self, source: str) -> List[Dict]:
        """Execute a multi-line Fluin program."""
        self.results = []
        lines = source.strip().split("\n")
        for line in lines:
            line = line.strip()
            if not line or line.startswith("//"):
                continue
            result = self._execute_line(line)
            if result:
                self.results.append(result)
        return self.results

    def _execute_line(self, line: str) -> Optional[Dict]:
        # Definition: ⏤name⏤ := { ... }
        m = re.match(r'⏤(\w[\w.]*)⏤\s*:=\s*(.+)', line)
        if m:
            name = m.group(1)
            expr = m.group(2).strip()
            return self._handle_definition(name, expr)

        # Standalone operation
        return self._handle_expression(line)

    def _handle_definition(self, name: str, expr: str) -> Dict:
        # Object literal: { type: "anchor", ... }
        if expr.startswith("{"):
            particle = self._parse_particle_literal(expr)
            self.variables[name] = particle
            return {"action": "define", "name": name, "particle": particle.to_dict()}

        # Expression (EXPAND, COMBINE, JUMP, etc.)
        result = self._handle_expression(expr)
        if result and "particle" in result:
            # Reconstruct particle from result
            p = result.get("_particle")
            if p:
                self.variables[name] = p
        return {"action": "define", "name": name, "result": result}

    def _handle_expression(self, expr: str) -> Optional[Dict]:
        # EXPAND(ref, level=N)
        m = re.match(r'EXPAND\((\w[\w.]*),\s*level=(\d+)\)', expr)
        if m:
            ref, level = m.group(1), int(m.group(2))
            return self._do_expand(ref, level)

        # COMPRESS(ref, level=N)
        m = re.match(r'COMPRESS\((\w[\w.]*),\s*level=(\d+)\)', expr)
        if m:
            ref, level = m.group(1), int(m.group(2))
            return self._do_compress(ref, level)

        # COMBINE(ref1, ref2) or ref1 ⊕ ref2
        m = re.match(r'COMBINE\((\w[\w.]*),\s*(\w[\w.]*)\)', expr)
        if not m:
            m = re.match(r'(\w[\w.]*)\s*⊕\s*(\w[\w.]*)', expr)
        if m:
            return self._do_combine(m.group(1), m.group(2))

        # JUMP(ref, FROM: RX, TO: RY)
        m = re.match(r'JUMP\((\w[\w.]*),\s*FROM:\s*R(\d+),\s*TO:\s*R(\d+)\)', expr)
        if m:
            ref, from_r, to_r = m.group(1), int(m.group(2)), int(m.group(3))
            return self._do_jump(ref, from_r, to_r)

        # CHECK(energy > threshold)
        m = re.match(r'CHECK\(energy\s*>\s*([\d.]+)\)', expr)
        if m:
            threshold = float(m.group(1))
            return self._do_check(threshold)

        # Chained with ⊕ or ∙
        if "⊕" in expr:
            parts = expr.split("⊕")
            results = []
            for part in parts:
                r = self._handle_expression(part.strip())
                if r:
                    results.append(r)
            return {"action": "chain_combine", "results": results}

        if "∙" in expr:
            parts = expr.split("∙")
            results = []
            for part in parts:
                r = self._handle_expression(part.strip())
                if r:
                    results.append(r)
            return {"action": "chain_sequence", "results": results}

        return {"action": "unknown", "expr": expr}

    def _resolve_ref(self, ref: str) -> Optional[Particle]:
        # Direct variable lookup
        if ref in self.variables:
            return self.variables[ref]
        # Dotted: particle.name
        parts = ref.split(".")
        if len(parts) == 2 and parts[0] == "particle":
            name = parts[1]
            if name in self.variables:
                return self.variables[name]
            # Auto-create from type name
            ptype = TYPE_MAP.get(name)
            if ptype:
                p = self.field.create(ptype)
                self.variables[name] = p
                return p
        return None

    def _parse_particle_literal(self, expr: str) -> Particle:
        """Parse { type: "anchor", position: [0,0,0], energy: 1.0 }"""
        # Normalize to valid JSON
        normalized = expr.replace("'", '"')
        # Add quotes around bare keys
        normalized = re.sub(r'(\w+)\s*:', r'"\1":', normalized)
        try:
            data = json.loads(normalized)
        except json.JSONDecodeError:
            data = {}

        ptype = TYPE_MAP.get(data.get("type", "seed"), SEED)
        energy = float(data.get("energy", 1.0))
        position = data.get("position", [0.0, 0.0, 0.0])

        return self.field.create(ptype, energy=energy, position=position)

    def _do_expand(self, ref: str, level: int) -> Dict:
        from .particle_math import ParticleMath
        p = self._resolve_ref(ref)
        if not p:
            return {"action": "expand", "error": f"ref '{ref}' not found"}
        pm = ParticleMath()
        expanded = pm.expand_particle(p, level)
        self.field.particles[expanded.id] = expanded
        return {"action": "expand", "ref": ref, "level": level,
                "original_energy": p.energy, "expanded_energy": expanded.energy,
                "particle": expanded.to_dict(), "_particle": expanded}

    def _do_compress(self, ref: str, level: int) -> Dict:
        from .particle_math import ParticleMath
        p = self._resolve_ref(ref)
        if not p:
            return {"action": "compress", "error": f"ref '{ref}' not found"}
        pm = ParticleMath()
        compressed = pm.compress_particle(p, level)
        self.field.particles[compressed.id] = compressed
        return {"action": "compress", "ref": ref, "level": level,
                "original_energy": p.energy, "compressed_energy": compressed.energy,
                "particle": compressed.to_dict(), "_particle": compressed}

    def _do_combine(self, ref1: str, ref2: str) -> Dict:
        p1 = self._resolve_ref(ref1)
        p2 = self._resolve_ref(ref2)
        if not p1 or not p2:
            return {"action": "combine", "error": "one or both refs not found"}
        combined = self.field.combine(p1.id, p2.id)
        if not combined:
            return {"action": "combine", "error": "combine failed"}
        return {"action": "combine", "ref1": ref1, "ref2": ref2,
                "combined_energy": combined.energy,
                "particle": combined.to_dict(), "_particle": combined}

    def _do_jump(self, ref: str, from_r: int, to_r: int) -> Dict:
        from .reality_layers import JumpNetwork
        p = self._resolve_ref(ref)
        if not p:
            return {"action": "jump", "error": f"ref '{ref}' not found"}
        p.reality_layer = from_r
        network = JumpNetwork()
        result = network.jump(p, to_r)
        return {"action": "jump", "ref": ref, "from": f"R{from_r}", "to": f"R{to_r}",
                "success": result.success, "energy_cost": result.energy_cost,
                "reason": result.reason}

    def _do_check(self, threshold: float) -> Dict:
        checks = []
        for name, p in self.variables.items():
            checks.append({
                "name": name,
                "energy": p.energy,
                "passes": p.energy > threshold,
            })
        return {"action": "check", "threshold": threshold, "results": checks}


class FlpkgLoader:
    """Load and validate .flpkg package files."""

    def __init__(self):
        self.origin_signature = "MrLiouWord"

    def load(self, data: Dict) -> Dict:
        """Load a .flpkg package from a dict."""
        metadata = data.get("metadata", {})
        particles = data.get("particleDefinitions", [])
        transforms = data.get("transformRules", [])
        jumps = data.get("jumpNodes", [])
        fusions = data.get("fusionPatterns", [])

        return {
            "metadata": metadata,
            "particle_count": len(particles),
            "transform_count": len(transforms),
            "jump_count": len(jumps),
            "fusion_count": len(fusions),
            "valid": self.validate(data),
            "origin_signature": self.origin_signature,
        }

    def validate(self, data: Dict) -> bool:
        """Validate .flpkg structure."""
        if "metadata" not in data:
            return False
        meta = data["metadata"]
        if "name" not in meta or "version" not in meta:
            return False
        if "particleDefinitions" not in data:
            return False
        return True

    def load_json(self, json_str: str) -> Dict:
        """Load from JSON string."""
        data = json.loads(json_str)
        return self.load(data)

    def create_package(self, name: str, version: str,
                       particles: List[Dict],
                       transforms: Optional[List[Dict]] = None,
                       jumps: Optional[List[Dict]] = None,
                       fusions: Optional[List[Dict]] = None) -> Dict:
        """Create a new .flpkg package."""
        return {
            "metadata": {
                "name": name,
                "version": version,
                "description": f"Particle module: {name}",
                "origin_signature": self.origin_signature,
            },
            "particleDefinitions": particles,
            "transformRules": transforms or [],
            "jumpNodes": jumps or [],
            "fusionPatterns": fusions or [],
        }
