"""
Particle Types — 5 core particle types from the MRLiou Particle Dictionary
origin_signature: MrLiouWord

Types:
  Anchor (Ⓟ 0x01) — positional anchor in the semantic field
  Seed   (Ⓘ 0x02) — carries base semantic information
  Jump   (↯ 0x04) — cross-Reality-layer connection
  Memory (⧫ 0x08) — stores system state and semantic memory
  Fusion (⨁ 0x10) — triggers fusion/transformation of other particles
"""

import time
import uuid
import hashlib
from enum import IntFlag
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set


class ParticleType(IntFlag):
    ANCHOR = 0x01
    SEED   = 0x02
    JUMP   = 0x04
    MEMORY = 0x08
    FUSION = 0x10

# Convenience aliases
ANCHOR = ParticleType.ANCHOR
SEED   = ParticleType.SEED
JUMP   = ParticleType.JUMP
MEMORY = ParticleType.MEMORY
FUSION = ParticleType.FUSION

# Symbol table
SYMBOLS = {
    ANCHOR: "Ⓟ",
    SEED:   "Ⓘ",
    JUMP:   "↯",
    MEMORY: "⧫",
    FUSION: "⨁",
}

# Jump mask: only JUMP and FUSION can initiate cross-layer jumps
JUMP_MASK = JUMP | FUSION


@dataclass
class Particle:
    """A single particle in the MRLiou system."""
    id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])
    ptype: ParticleType = SEED
    energy: float = 1.0
    position: List[float] = field(default_factory=lambda: [0.0, 0.0, 0.0])
    properties: Dict[str, Any] = field(default_factory=dict)
    reality_layer: int = 0          # R0-R4
    gravity: float = 1.0
    timestamp: float = field(default_factory=time.time)
    origin_signature: str = "MrLiouWord"

    @property
    def symbol(self) -> str:
        return SYMBOLS.get(self.ptype, "?")

    @property
    def bit_id(self) -> str:
        return f"0x{self.ptype.value:02x}"

    @property
    def can_jump(self) -> bool:
        return bool(self.ptype & JUMP_MASK)

    def hash(self) -> str:
        data = f"{self.id}:{self.ptype.value}:{self.energy}:{self.reality_layer}:{self.timestamp}"
        return hashlib.sha256(data.encode()).hexdigest()

    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "type": self.ptype.name,
            "symbol": self.symbol,
            "bit_id": self.bit_id,
            "energy": self.energy,
            "position": self.position,
            "reality_layer": self.reality_layer,
            "gravity": self.gravity,
            "properties": self.properties,
            "hash": self.hash(),
            "origin_signature": self.origin_signature,
        }

    def __repr__(self):
        return f"Particle({self.symbol} {self.ptype.name} E={self.energy:.2f} R{self.reality_layer})"


class ParticleField:
    """
    A semantic field containing particles.
    Supports creation, lookup, combination, and fusion operations.
    """

    def __init__(self, name: str = "default"):
        self.name = name
        self.particles: Dict[str, Particle] = {}
        self.history: List[Dict] = []
        self.origin_signature = "MrLiouWord"

    def create(self, ptype: ParticleType, energy: float = 1.0,
               position: Optional[List[float]] = None,
               reality_layer: int = 0,
               properties: Optional[Dict] = None) -> Particle:
        p = Particle(
            ptype=ptype,
            energy=energy,
            position=position or [0.0, 0.0, 0.0],
            reality_layer=reality_layer,
            properties=properties or {},
        )
        self.particles[p.id] = p
        self._log("create", p)
        return p

    def get(self, pid: str) -> Optional[Particle]:
        return self.particles.get(pid)

    def remove(self, pid: str) -> bool:
        p = self.particles.pop(pid, None)
        if p:
            self._log("remove", p)
            return True
        return False

    def combine(self, a_id: str, b_id: str) -> Optional[Particle]:
        """Combine two particles using the ⊕ operator."""
        a, b = self.particles.get(a_id), self.particles.get(b_id)
        if not a or not b:
            return None

        # Fusion result: combined energy, merged properties, higher reality layer
        combined = Particle(
            ptype=FUSION,
            energy=a.energy + b.energy,
            position=[(a.position[i] + b.position[i]) / 2 for i in range(3)],
            reality_layer=max(a.reality_layer, b.reality_layer),
            properties={**a.properties, **b.properties,
                        "fused_from": [a.id, b.id]},
        )
        self.particles[combined.id] = combined
        self._log("combine", combined, detail=f"{a.id}⊕{b.id}")
        return combined

    def fuse_all(self, pids: List[str]) -> Optional[Particle]:
        """Fuse multiple particles into one."""
        particles = [self.particles[pid] for pid in pids if pid in self.particles]
        if len(particles) < 2:
            return None

        total_energy = sum(p.energy for p in particles)
        avg_pos = [sum(p.position[i] for p in particles) / len(particles) for i in range(3)]
        max_layer = max(p.reality_layer for p in particles)

        fused = Particle(
            ptype=FUSION,
            energy=total_energy,
            position=avg_pos,
            reality_layer=max_layer,
            properties={"fused_from": [p.id for p in particles], "count": len(particles)},
        )
        self.particles[fused.id] = fused
        self._log("fuse_all", fused, detail=f"{len(particles)} particles")
        return fused

    def filter_by_type(self, ptype: ParticleType) -> List[Particle]:
        return [p for p in self.particles.values() if p.ptype == ptype]

    def filter_by_layer(self, layer: int) -> List[Particle]:
        return [p for p in self.particles.values() if p.reality_layer == layer]

    def total_energy(self) -> float:
        return sum(p.energy for p in self.particles.values())

    def stats(self) -> Dict:
        type_counts = {}
        for p in self.particles.values():
            name = p.ptype.name
            type_counts[name] = type_counts.get(name, 0) + 1
        return {
            "name": self.name,
            "total_particles": len(self.particles),
            "total_energy": round(self.total_energy(), 4),
            "type_counts": type_counts,
            "history_length": len(self.history),
            "origin_signature": self.origin_signature,
        }

    def _log(self, action: str, particle: Particle, detail: str = ""):
        self.history.append({
            "action": action,
            "particle_id": particle.id,
            "type": particle.ptype.name,
            "detail": detail,
            "ts": time.time(),
        })
