"""
Parallel World Bridge — Maps Reality layers (R0-R4) to Network layers (L-1 to L7)
origin_signature: MrLiouWord

This bridge connects the particle consciousness model (Reality layers)
to the physical/cloud/edge network (Global Parallel Network).

Mapping:
  R0 種子/場   ↔ L-1 Physical (Starlink) — raw field, hardware substrate
  R1 語言      ↔ L0-L1 Cloud — language processing on cloud compute
  R2 人格      ↔ L2-L3 Edge — persona runs at the edge, close to user
  R3 世界      ↔ L4-L5 Application/AI — world model in AI layer
  R4 母體核心  ↔ L6-L7 ASI/Ω — central consciousness at highest layer

The bridge enables:
  - Particle jump → network route (R-layer change triggers L-layer routing)
  - Network event → particle evolution (network state feeds back to particles)
  - Existence proof anchoring across both systems
"""

import time
from typing import Dict, List, Optional, Tuple

from .particle_types import Particle, ParticleField, ANCHOR, SEED, JUMP, MEMORY, FUSION
from .reality_layers import JumpNetwork, JumpResult
from .existence_proof import ExistenceProof


# R-layer to L-layer mapping
R_TO_L_MAP = {
    0: ["L-1"],           # R0 → Starlink/Physical
    1: ["L0", "L1"],      # R1 → Cloud
    2: ["L2", "L3"],      # R2 → Edge
    3: ["L4", "L5"],      # R3 → Application/AI
    4: ["L6", "L7"],      # R4 → ASI/Ω
}

L_TO_R_MAP = {
    "L-1": 0,
    "L0": 1, "L1": 1,
    "L2": 2, "L3": 2,
    "L4": 3, "L5": 3,
    "L6": 4, "L7": 4,
}


class BridgeEvent:
    """An event crossing the Reality↔Network bridge."""
    def __init__(self, direction: str, r_layer: int, l_layers: List[str],
                 particle_id: str, detail: str):
        self.direction = direction  # "r_to_l" or "l_to_r"
        self.r_layer = r_layer
        self.l_layers = l_layers
        self.particle_id = particle_id
        self.detail = detail
        self.timestamp = time.time()

    def to_dict(self) -> Dict:
        return {
            "direction": self.direction,
            "r_layer": f"R{self.r_layer}",
            "l_layers": self.l_layers,
            "particle_id": self.particle_id,
            "detail": self.detail,
            "timestamp": self.timestamp,
        }


class ParallelWorldBridge:
    """
    Bridges the particle Reality system with the Global Parallel Network.

    Provides:
      - R→L mapping: when a particle jumps between R-layers, determine
        which network layers should handle the routing
      - L→R feedback: network events can trigger particle state evolution
      - Unified existence proof anchoring
    """

    def __init__(self):
        self.field = ParticleField("bridge")
        self.jump_network = JumpNetwork()
        self.proof = ExistenceProof("MrLiouWord")
        self.events: List[BridgeEvent] = []
        self.origin_signature = "MrLiouWord"

        # Anchor the bridge creation
        self.proof.anchor("bridge_init", "ParallelWorldBridge initialized")

    def r_to_l(self, r_layer: int) -> List[str]:
        """Map a Reality layer to its corresponding network layers."""
        return R_TO_L_MAP.get(r_layer, [])

    def l_to_r(self, l_layer: str) -> int:
        """Map a network layer to its corresponding Reality layer."""
        return L_TO_R_MAP.get(l_layer, 0)

    def particle_jump_to_network(self, particle: Particle, target_r: int) -> Dict:
        """
        When a particle jumps between R-layers, compute the corresponding
        network route and record the bridge event.
        """
        source_r = particle.reality_layer
        source_l = self.r_to_l(source_r)
        target_l = self.r_to_l(target_r)

        # Attempt the jump
        self.jump_network.place(particle)
        jump_result = self.jump_network.jump(particle, target_r)

        event = BridgeEvent(
            direction="r_to_l",
            r_layer=target_r if jump_result.success else source_r,
            l_layers=target_l if jump_result.success else source_l,
            particle_id=particle.id,
            detail=f"jump R{source_r}→R{target_r}: {jump_result.reason}",
        )
        self.events.append(event)

        # Anchor in existence proof
        if jump_result.success:
            self.proof.anchor(
                f"particle_jump R{source_r}→R{target_r}",
                f"particle={particle.id} energy_cost={jump_result.energy_cost}",
            )

        return {
            "jump": {
                "success": jump_result.success,
                "from_r": source_r,
                "to_r": target_r,
                "energy_cost": jump_result.energy_cost,
                "reason": jump_result.reason,
            },
            "network": {
                "source_layers": source_l,
                "target_layers": target_l,
                "route_needed": source_l != target_l,
            },
            "proof_chain_length": len(self.proof.chain),
        }

    def network_event_to_particle(self, l_layer: str, event_type: str,
                                   data: Optional[Dict] = None) -> Dict:
        """
        A network event triggers particle evolution in the corresponding R-layer.
        """
        r_layer = self.l_to_r(l_layer)

        # Create or find a particle in this R-layer
        particles_in_layer = self.field.filter_by_layer(r_layer)
        if particles_in_layer:
            target_particle = particles_in_layer[0]
        else:
            target_particle = self.field.create(MEMORY, reality_layer=r_layer)

        # Apply evolution based on event type
        from .particle_math import ParticleMath
        pm = ParticleMath()

        env_factor = 1.0
        if event_type == "high_load":
            env_factor = 0.8  # stress reduces energy
        elif event_type == "scale_up":
            env_factor = 1.5  # scaling increases energy
        elif event_type == "failure":
            env_factor = 0.5  # failure halves energy
        elif event_type == "recovery":
            env_factor = 1.2  # recovery boosts energy

        evolved = pm.evolve(target_particle, env_factor=env_factor)
        self.field.particles[evolved.id] = evolved

        event = BridgeEvent(
            direction="l_to_r",
            r_layer=r_layer,
            l_layers=[l_layer],
            particle_id=evolved.id,
            detail=f"network {event_type} on {l_layer} → R{r_layer} evolution",
        )
        self.events.append(event)

        return {
            "network_layer": l_layer,
            "reality_layer": r_layer,
            "event_type": event_type,
            "original_energy": target_particle.energy,
            "evolved_energy": evolved.energy,
            "env_factor": env_factor,
        }

    def full_system_status(self) -> Dict:
        """Get unified status across both Reality and Network layers."""
        layer_status = {}
        for r in range(5):
            l_layers = self.r_to_l(r)
            particles = self.field.filter_by_layer(r)
            layer_status[f"R{r}"] = {
                "network_layers": l_layers,
                "particles": len(particles),
                "total_energy": round(sum(p.energy for p in particles), 4),
            }

        return {
            "layers": layer_status,
            "total_particles": len(self.field.particles),
            "bridge_events": len(self.events),
            "proof_chain": len(self.proof.chain),
            "proof_valid": self.proof.verify_chain(),
            "merkle_root": self.proof.merkle_root()[:16] + "...",
            "origin_signature": self.origin_signature,
        }

    def stats(self) -> Dict:
        return {
            "events": len(self.events),
            "r_to_l_events": len([e for e in self.events if e.direction == "r_to_l"]),
            "l_to_r_events": len([e for e in self.events if e.direction == "l_to_r"]),
            "particles": len(self.field.particles),
            "proof_chain": len(self.proof.chain),
            "origin_signature": self.origin_signature,
        }
