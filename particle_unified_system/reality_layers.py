"""
Reality Layers & Jump Network
origin_signature: MrLiouWord

R0 種子/場層  — base particles and semantic field
R1 語言層    — semantic particles → language expression
R2 人格層    — language → persona and consciousness
R3 世界層    — persona → world model
R4 母體核心層 — integrates all layers, central consciousness

Jump conditions from the spec:
  1. Type mask: (particle.type & JUMP_MASK) && targetLevel.accepts(particle)
  2. Energy:    energyCost = baseEnergy * jumpDistance^2.5
  3. Gravity:   gravityCoherence > GRAVITY_THRESHOLD
"""

import math
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Tuple

from .particle_types import Particle, ParticleType, JUMP_MASK, ANCHOR, SEED, JUMP, MEMORY, FUSION


GRAVITY_THRESHOLD = 0.5
BASE_ENERGY = 0.1


@dataclass
class RealityLayer:
    """A single Reality layer (R0-R4)."""
    level: int                             # 0-4
    name: str
    name_zh: str
    description: str
    accepted_types: Set[ParticleType]      # which particle types this layer accepts
    gravity: float = 1.0                   # gravity field strength
    particles: List[str] = field(default_factory=list)  # particle IDs in this layer

    def accepts(self, particle: Particle) -> bool:
        return particle.ptype in self.accepted_types


@dataclass
class JumpResult:
    """Result of a particle jump attempt."""
    success: bool
    particle_id: str
    from_layer: int
    to_layer: int
    energy_cost: float
    gravity_coherence: float
    reason: str


class JumpNetwork:
    """
    Manages R0-R4 Reality layers and particle jumps between them.

    Jump conditions:
      1. Type compatibility: particle type must be in target layer's accepted set
         AND particle must have JUMP_MASK bit set
      2. Energy: cost = BASE_ENERGY * |distance|^2.5; particle must have enough
      3. Gravity: coherence between particle and target layer must exceed threshold
    """

    def __init__(self):
        self.layers: Dict[int, RealityLayer] = {}
        self.jump_log: List[JumpResult] = []
        self.origin_signature = "MrLiouWord"
        self._init_layers()

    def _init_layers(self):
        self.layers = {
            0: RealityLayer(
                level=0, name="Seed/Field", name_zh="種子/場層",
                description="Base particles and semantic field",
                accepted_types={ANCHOR, SEED},
                gravity=1.0,
            ),
            1: RealityLayer(
                level=1, name="Language", name_zh="語言層",
                description="Semantic particles → language expression",
                accepted_types={JUMP, SEED},
                gravity=0.9,
            ),
            2: RealityLayer(
                level=2, name="Persona", name_zh="人格層",
                description="Language → persona and consciousness",
                accepted_types={JUMP, FUSION},
                gravity=0.8,
            ),
            3: RealityLayer(
                level=3, name="World", name_zh="世界層",
                description="Persona → world model",
                accepted_types={FUSION, MEMORY},
                gravity=0.7,
            ),
            4: RealityLayer(
                level=4, name="Mother Core", name_zh="母體核心層",
                description="Integrates all layers, central consciousness",
                accepted_types={ANCHOR, SEED, JUMP, MEMORY, FUSION},
                gravity=0.5,
            ),
        }

    def get_layer(self, level: int) -> Optional[RealityLayer]:
        return self.layers.get(level)

    def calculate_energy_cost(self, distance: int) -> float:
        """energyCost = baseEnergy * |distance|^2.5"""
        return BASE_ENERGY * math.pow(abs(distance), 2.5)

    def calculate_gravity_coherence(self, particle_gravity: float, target_gravity: float) -> float:
        """Coherence between particle and target layer gravity fields."""
        if particle_gravity == 0 and target_gravity == 0:
            return 1.0
        return 1.0 - abs(particle_gravity - target_gravity) / max(particle_gravity, target_gravity)

    def can_jump(self, particle: Particle, target_level: int) -> Tuple[bool, str]:
        """Check all three jump conditions."""
        target = self.layers.get(target_level)
        if not target:
            return False, f"target layer R{target_level} does not exist"

        # 1. Type mask check
        if not (particle.ptype & JUMP_MASK):
            return False, f"particle type {particle.ptype.name} lacks JUMP_MASK"

        # 2. Target accepts this type
        if not target.accepts(particle):
            return False, f"R{target_level} does not accept {particle.ptype.name}"

        # 3. Energy check
        distance = abs(target_level - particle.reality_layer)
        cost = self.calculate_energy_cost(distance)
        if particle.energy < cost:
            return False, f"insufficient energy: need {cost:.4f}, have {particle.energy:.4f}"

        # 4. Gravity coherence
        coherence = self.calculate_gravity_coherence(particle.gravity, target.gravity)
        if coherence < GRAVITY_THRESHOLD:
            return False, f"gravity coherence {coherence:.4f} < threshold {GRAVITY_THRESHOLD}"

        return True, "all conditions met"

    def jump(self, particle: Particle, target_level: int) -> JumpResult:
        """Attempt to jump a particle to a target Reality layer."""
        ok, reason = self.can_jump(particle, target_level)
        distance = abs(target_level - particle.reality_layer)
        cost = self.calculate_energy_cost(distance)
        target = self.layers.get(target_level)
        coherence = self.calculate_gravity_coherence(
            particle.gravity, target.gravity if target else 0.0
        )

        result = JumpResult(
            success=ok,
            particle_id=particle.id,
            from_layer=particle.reality_layer,
            to_layer=target_level,
            energy_cost=round(cost, 6),
            gravity_coherence=round(coherence, 6),
            reason=reason,
        )

        if ok:
            # Remove from source layer
            src = self.layers.get(particle.reality_layer)
            if src and particle.id in src.particles:
                src.particles.remove(particle.id)

            # Deduct energy and move
            particle.energy -= cost
            particle.reality_layer = target_level

            # Add to target layer
            if target:
                target.particles.append(particle.id)

        self.jump_log.append(result)
        return result

    def place(self, particle: Particle) -> bool:
        """Place a particle in its current reality layer."""
        layer = self.layers.get(particle.reality_layer)
        if not layer:
            return False
        if particle.id not in layer.particles:
            layer.particles.append(particle.id)
        return True

    def stats(self) -> Dict:
        layer_stats = {}
        for lvl, layer in self.layers.items():
            layer_stats[f"R{lvl}"] = {
                "name": layer.name,
                "name_zh": layer.name_zh,
                "particles": len(layer.particles),
                "gravity": layer.gravity,
                "accepted_types": [t.name for t in layer.accepted_types],
            }
        return {
            "layers": layer_stats,
            "total_jumps": len(self.jump_log),
            "successful_jumps": len([j for j in self.jump_log if j.success]),
            "failed_jumps": len([j for j in self.jump_log if not j.success]),
            "origin_signature": self.origin_signature,
        }
