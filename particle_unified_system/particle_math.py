"""
Particle Math — Expand, Compress, and State Evolution formulas
origin_signature: MrLiouWord

From the MRLiou Particle Dictionary:

Expand:   P_expanded(n) = α · ∫₀ⁿ P_base(λ) · e^(λ·t) dλ
Compress: P_compressed(n) = β · Σᵢ₌₀ⁿ P_expanded(i) · ω^(-i)
Evolve:   P(k+1) = N(k) · P(k) · η(k)

Version conversion:
  upgrade   → expand formula
  downgrade → compress formula
"""

import math
from typing import Dict, List, Optional, Tuple

from .particle_types import Particle


class ParticleMath:
    """
    Implements the three core particle formulas.
    All operations work on particle energy as the scalar value.
    """

    def __init__(self, alpha: float = 1.0, beta: float = 1.0, omega: float = 2.0):
        self.alpha = alpha   # expand coefficient
        self.beta = beta     # compress coefficient
        self.omega = omega   # compress decay factor
        self.origin_signature = "MrLiouWord"

    # ── Expand ──

    def expand(self, particle: Particle, n: int, t: float = 1.0,
               steps: int = 100) -> float:
        """
        P_expanded(n) = α · ∫₀ⁿ P_base(λ) · e^(λ·t) dλ

        Closed-form solution (P_base is constant = particle.energy):
          t ≠ 0: α · P_base · (e^(n·t) − 1) / t
          t = 0: α · P_base · n

        Returns the expanded energy value.
        """
        if n <= 0:
            return particle.energy

        p_base = particle.energy
        if abs(t) < 1e-12:
            result = self.alpha * p_base * n
        else:
            result = self.alpha * p_base * (math.exp(n * t) - 1.0) / t
        return round(result, 8)

    def expand_particle(self, particle: Particle, n: int, t: float = 1.0) -> Particle:
        """Create a new particle with expanded energy."""
        new_energy = self.expand(particle, n, t)
        return Particle(
            ptype=particle.ptype,
            energy=new_energy,
            position=particle.position.copy(),
            reality_layer=min(particle.reality_layer + n, 4),
            properties={**particle.properties, "expanded_from": particle.id, "expand_level": n},
            gravity=particle.gravity,
        )

    # ── Compress ──

    def compress(self, expanded_values: List[float], n: int) -> float:
        """
        P_compressed(n) = β · Σᵢ₌₀ⁿ P_expanded(i) · ω^(-i)

        expanded_values: list of P_expanded(i) for i=0..n
        """
        if n < 0 or not expanded_values:
            return 0.0

        total = 0.0
        for i in range(min(n + 1, len(expanded_values))):
            total += expanded_values[i] * math.pow(self.omega, -i)

        return round(self.beta * total, 8)

    def compress_particle(self, particle: Particle, n: int) -> Particle:
        """
        Compress a particle by generating expanded values at each level
        then applying the compress formula.
        """
        expanded_values = []
        for i in range(n + 1):
            expanded_values.append(self.expand(particle, i))

        compressed_energy = self.compress(expanded_values, n)
        return Particle(
            ptype=particle.ptype,
            energy=compressed_energy,
            position=particle.position.copy(),
            reality_layer=max(particle.reality_layer - n, 0),
            properties={**particle.properties, "compressed_from": particle.id, "compress_level": n},
            gravity=particle.gravity,
        )

    # ── State Evolution ──

    def evolve(self, particle: Particle, env_factor: float = 1.0,
               internal_factor: float = 1.0) -> Particle:
        """
        P(k+1) = N(k) · P(k) · η(k)

        env_factor:      N(k) — environment factor
        internal_factor: η(k) — internal evolution factor
        """
        new_energy = env_factor * particle.energy * internal_factor
        return Particle(
            ptype=particle.ptype,
            energy=round(new_energy, 8),
            position=particle.position.copy(),
            reality_layer=particle.reality_layer,
            properties={**particle.properties,
                        "evolved_from": particle.id,
                        "env_factor": env_factor,
                        "internal_factor": internal_factor},
            gravity=particle.gravity,
        )

    def evolve_steps(self, particle: Particle, steps: int,
                     env_factors: Optional[List[float]] = None,
                     internal_factors: Optional[List[float]] = None) -> List[Particle]:
        """Run multiple evolution steps, returning the trajectory."""
        trajectory = [particle]
        for k in range(steps):
            env = env_factors[k] if env_factors and k < len(env_factors) else 1.0
            internal = internal_factors[k] if internal_factors and k < len(internal_factors) else 1.0
            next_p = self.evolve(trajectory[-1], env, internal)
            trajectory.append(next_p)
        return trajectory

    # ── Version Conversion ──

    def convert_version(self, particle: Particle, from_version: float,
                        to_version: float) -> Particle:
        """
        Convert particle between versions using expand (upgrade) or compress (downgrade).
        """
        diff = to_version - from_version
        if diff > 0:
            level = int(math.ceil(diff * 2))  # scale version diff to expand level
            return self.expand_particle(particle, level)
        elif diff < 0:
            level = int(math.ceil(abs(diff) * 2))
            return self.compress_particle(particle, level)
        else:
            return particle
