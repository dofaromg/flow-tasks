# Terminal System Seed — Formal closed-loop system + Metacode integration
# origin_signature: MrLiouWord
#
# ⊢ TERMINAL ≡ ⟨Σ, Φo, Φa, Φr⟩
# C = { closed, no_return, no_goal, no_semantic }

from .terminal import Terminal, InvariantError, Step
from .dimension_traversal import DimensionTraversal, DimensionMatrix
from .metacode_system import (
    MetacodeSystem, Certificate, CertificateMapping,
    Role, CertType, SourceMode,
)
from .integration import (
    PreParticleIntegration, QuantumBridge, DualBrain,
    TerminalParticleBridge,
)

__all__ = [
    "Terminal", "InvariantError", "Step",
    "DimensionTraversal", "DimensionMatrix",
    "MetacodeSystem", "Certificate", "CertificateMapping",
    "Role", "CertType", "SourceMode",
    "PreParticleIntegration", "QuantumBridge", "DualBrain",
    "TerminalParticleBridge",
]
