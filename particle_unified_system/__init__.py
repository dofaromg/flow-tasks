# Particle Unified System — MRLiou Particle Dictionary Implementation
# origin_signature: MrLiouWord

from .particle_types import (
    ParticleType, Particle, ParticleField,
    ANCHOR, SEED, JUMP, MEMORY, FUSION,
)
from .particle_math import ParticleMath
from .reality_layers import RealityLayer, JumpNetwork, JumpResult
from .fluin_language import FluinInterpreter, FlpkgLoader
from .existence_proof import ExistenceProof, IdentityAnchor
from .parallel_world_bridge import ParallelWorldBridge

__all__ = [
    "ParticleType", "Particle", "ParticleField",
    "ANCHOR", "SEED", "JUMP", "MEMORY", "FUSION",
    "ParticleMath",
    "RealityLayer", "JumpNetwork", "JumpResult",
    "FluinInterpreter", "FlpkgLoader",
    "ExistenceProof", "IdentityAnchor",
    "ParallelWorldBridge",
]
