"""
Integration Layer — Bridges Terminal System to particle_unified_system
origin_signature: MrLiouWord

5 integration layers from the spec:
  1. Math formalization (Terminal itself)
  2. PreParticle integration (δP₀ → P₀)
  3. Quantum bridge (algorithm → quantum representation)
  4. Dual brain (cerebrum + cerebellum analysis)
  5. Dimension traversal (handled by dimension_traversal.py)

Also provides TerminalParticleBridge connecting Terminal ↔ particle_unified_system.
"""

import time
import uuid
import hashlib
import math
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Tuple

from .terminal import Terminal, InvariantError, make_law0_terminal, ORIGIN_SIGNATURE

ORIGIN = ORIGIN_SIGNATURE


# ── Layer 2: PreParticle Integration ──

@dataclass
class PreParticle:
    """Pre-particle δP₀ before integration into the system."""
    id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])
    N_k: float = 1.0              # structure factor
    eta_k: float = 1.0            # environment factor
    origin_signature: str = ORIGIN


@dataclass
class SystemParticle:
    """System particle P₀ after integration."""
    id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])
    derived_from: str = ""
    structure_factor: float = 1.0
    environment_factor: float = 1.0
    dimensionality: int = 4
    state: str = "initialized"
    created_at: float = field(default_factory=time.time)
    origin_signature: str = ORIGIN


class PreParticleIntegration:
    """
    Integrates pre-particles (δP₀) into system particles (P₀).
    Enforces LAW-0 signature check.
    """

    def __init__(self):
        self.integrated: List[SystemParticle] = []
        self.origin_signature = ORIGIN

    def integrate(self, delta_p0: PreParticle) -> SystemParticle:
        if delta_p0.origin_signature != ORIGIN:
            raise InvariantError(f"LAW-0 violation: origin_signature={delta_p0.origin_signature}")

        particle = SystemParticle(
            derived_from=delta_p0.id,
            structure_factor=delta_p0.N_k,
            environment_factor=delta_p0.eta_k,
        )
        self.integrated.append(particle)
        return particle

    def integrate_batch(self, pre_particles: List[PreParticle]) -> List[SystemParticle]:
        return [self.integrate(pp) for pp in pre_particles]


# ── Layer 3: Quantum Bridge ──

@dataclass
class QuantumWorld:
    """World state for quantum bridge terminal."""
    algorithm_id: str = ""
    components: List[str] = field(default_factory=list)
    entanglement: float = 0.5
    dimensionality: int = 5
    tick: int = 0
    origin_signature: str = ORIGIN

    def to_dict(self) -> Dict:
        return {
            "algorithm_id": self.algorithm_id,
            "components": self.components,
            "entanglement": self.entanglement,
            "dimensionality": self.dimensionality,
            "tick": self.tick,
            "origin_signature": self.origin_signature,
        }


@dataclass
class QuantumState:
    """State for quantum bridge terminal."""
    coherence: float = 1.0
    superposition: List[float] = field(default_factory=lambda: [0.5, 0.5])
    collapsed: bool = False
    tick: int = 0
    origin_signature: str = ORIGIN

    def to_dict(self) -> Dict:
        return {
            "coherence": self.coherence,
            "superposition": self.superposition,
            "collapsed": self.collapsed,
            "tick": self.tick,
            "origin_signature": self.origin_signature,
        }


class QuantumBridge:
    """
    Maps algorithms to quantum representations via Terminal run.
    Uses a Terminal<QuantumWorld, QuantumState> internally.
    """

    def __init__(self):
        self.terminal = Terminal(
            Phi_o=self._observe,
            Phi_a=self._advance,
            Phi_r=self._reify,
        )
        self.origin_signature = ORIGIN

    def _observe(self, w: Dict) -> Dict:
        """Ω → Σ: world to quantum state."""
        entanglement = w.get("entanglement", 0.5)
        dim = w.get("dimensionality", 5)
        tick = w.get("tick", 0)
        n = max(dim, 2)
        superposition = [round(math.sin(i * entanglement + tick * 0.1), 4) for i in range(n)]
        coherence = round(1.0 - tick * 0.005, 4)
        return {
            "coherence": max(coherence, 0.01),
            "superposition": superposition,
            "collapsed": coherence < 0.1,
            "tick": tick,
            "origin_signature": ORIGIN,
        }

    def _advance(self, s: Dict) -> Dict:
        """Σ → Σ: evolve quantum state."""
        s2 = dict(s)
        s2["tick"] = s.get("tick", 0) + 1
        s2["coherence"] = round(max(s["coherence"] * 0.995, 0.01), 4)
        sp = s.get("superposition", [0.5])
        s2["superposition"] = [round(v * 0.99 + 0.01 * math.cos(i), 4) for i, v in enumerate(sp)]
        s2["origin_signature"] = ORIGIN
        return s2

    def _reify(self, s: Dict) -> Dict:
        """Σ → Ω: state back to world."""
        return {
            "algorithm_id": "quantum_evolved",
            "components": [f"q{i}" for i in range(len(s.get("superposition", [])))],
            "entanglement": s.get("coherence", 0.5),
            "dimensionality": len(s.get("superposition", [])),
            "tick": s.get("tick", 0),
            "origin_signature": ORIGIN,
        }

    def map_algorithm(self, algorithm_id: str, complexity: int = 5,
                      steps: int = 100) -> Dict:
        """Run terminal for N steps and return quantum representation."""
        dim = 8 if complexity > 5 else 5
        w0 = {
            "algorithm_id": algorithm_id,
            "components": [f"c{i}" for i in range(complexity)],
            "entanglement": 0.5,
            "dimensionality": dim,
            "tick": 0,
            "origin_signature": ORIGIN,
        }

        result = None
        for t, w, s in self.terminal.run(w0, max_steps=steps):
            result = (t, w, s)

        if not result:
            return {"error": "no result"}

        t, w, s = result
        return {
            "algorithm_id": algorithm_id,
            "steps_run": t + 1,
            "final_coherence": s.get("coherence"),
            "final_dimensionality": len(s.get("superposition", [])),
            "collapsed": s.get("collapsed", False),
            "origin_signature": ORIGIN,
        }


# ── Layer 4: Dual Brain ──

class DualBrain:
    """
    Analyst dual-brain: cerebrum (analysis) + cerebellum (processing).
    Uses Terminal<BrainWorld, BrainState> internally.
    """

    def __init__(self):
        self.terminal = Terminal(
            Phi_o=self._observe,
            Phi_a=self._advance,
            Phi_r=self._reify,
        )
        self.origin_signature = ORIGIN

    def _observe(self, w: Dict) -> Dict:
        """Observe: extract analysis state from brain world."""
        return {
            "cerebrum_result": self._cerebrum_analyze(w.get("input_data")),
            "cerebellum_result": None,
            "confidence": 0.5,
            "tick": w.get("tick", 0),
            "origin_signature": ORIGIN,
        }

    def _advance(self, s: Dict) -> Dict:
        """Advance: cerebellum processes cerebrum's output."""
        s2 = dict(s)
        cerebrum = s.get("cerebrum_result", {})
        s2["cerebellum_result"] = self._cerebellum_process(cerebrum)
        # Confidence increases with processing
        s2["confidence"] = round(min(s.get("confidence", 0.5) + 0.1, 0.99), 4)
        s2["tick"] = s.get("tick", 0) + 1
        s2["origin_signature"] = ORIGIN
        return s2

    def _reify(self, s: Dict) -> Dict:
        """Reify: produce updated brain world."""
        return {
            "input_data": s.get("cerebellum_result"),
            "cerebrum_state": "processed",
            "cerebellum_state": "processed",
            "tick": s.get("tick", 0),
            "origin_signature": ORIGIN,
        }

    def _cerebrum_analyze(self, data) -> Dict:
        """Cerebrum: pattern recognition and analysis."""
        if data is None:
            return {"patterns": [], "complexity": 0}
        h = hashlib.sha256(str(data).encode()).hexdigest()[:8]
        return {
            "patterns": [h[i:i+2] for i in range(0, 8, 2)],
            "complexity": len(str(data)),
            "hash": h,
        }

    def _cerebellum_process(self, cerebrum_result: Dict) -> Dict:
        """Cerebellum: coordination and integration."""
        if not cerebrum_result:
            return {"integrated": False}
        patterns = cerebrum_result.get("patterns", [])
        return {
            "integrated": True,
            "pattern_count": len(patterns),
            "synthesis": hashlib.sha256(str(patterns).encode()).hexdigest()[:8],
        }

    def process(self, input_data, steps: int = 3) -> Dict:
        """Run dual-brain processing for N steps."""
        w0 = {
            "input_data": input_data,
            "cerebrum_state": "ready",
            "cerebellum_state": "ready",
            "tick": 0,
            "origin_signature": ORIGIN,
        }

        result = None
        for t, w, s in self.terminal.run(w0, max_steps=steps):
            result = (t, w, s)

        if not result:
            return {"error": "no result"}

        t, w, s = result
        return {
            "cerebrum_analysis": s.get("cerebrum_result"),
            "cerebellum_processing": s.get("cerebellum_result"),
            "confidence": s.get("confidence"),
            "steps": t + 1,
            "origin_signature": ORIGIN,
        }


# ── Bridge to particle_unified_system ──

class TerminalParticleBridge:
    """
    Connects Terminal System Seed to particle_unified_system.

    - PreParticle → Particle (via evolve formula)
    - Terminal step → particle state evolution
    - Metacode certificates → existence proof anchoring
    """

    def __init__(self):
        self.pre_particle_integration = PreParticleIntegration()
        self.quantum_bridge = QuantumBridge()
        self.dual_brain = DualBrain()
        self.event_log: List[Dict] = []
        self.origin_signature = ORIGIN

    def pre_particle_to_system(self, N_k: float, eta_k: float) -> SystemParticle:
        """Convert pre-particle factors to a system particle."""
        pp = PreParticle(N_k=N_k, eta_k=eta_k)
        sp = self.pre_particle_integration.integrate(pp)
        self._log("pre_particle_integrate", f"δP₀({pp.id}) → P₀({sp.id})")
        return sp

    def terminal_evolve(self, initial_value: float, steps: int = 10) -> List[Dict]:
        """
        Run a Terminal that evolves a numeric value.
        Demonstrates the observe→advance→reify cycle.
        """
        terminal = make_law0_terminal(
            transform_w_to_s=lambda w: {"value": w.get("value", 0) * 1.1, "tick": w.get("tick", 0)},
            advance_s=lambda s: {"value": s["value"] + 0.01, "tick": s["tick"] + 1},
            reify_s_to_w=lambda s: {"value": s["value"], "tick": s["tick"]},
        )
        trajectory = []
        for t, w, s in terminal.run(
            {"value": initial_value, "tick": 0, "origin_signature": ORIGIN},
            max_steps=steps,
        ):
            trajectory.append({"t": t, "world_value": w.get("value"), "state_value": s.get("value")})

        self._log("terminal_evolve", f"steps={steps} final={trajectory[-1]['state_value']:.4f}")
        return trajectory

    def quantum_analyze(self, algorithm_id: str, complexity: int = 5) -> Dict:
        """Run quantum bridge analysis."""
        result = self.quantum_bridge.map_algorithm(algorithm_id, complexity)
        self._log("quantum_analyze", f"algo={algorithm_id} coherence={result.get('final_coherence')}")
        return result

    def dual_brain_analyze(self, data) -> Dict:
        """Run dual-brain analysis."""
        result = self.dual_brain.process(data)
        self._log("dual_brain", f"confidence={result.get('confidence')}")
        return result

    def _log(self, event_type: str, detail: str):
        self.event_log.append({"type": event_type, "detail": detail, "ts": time.time()})

    def stats(self) -> Dict:
        return {
            "pre_particles_integrated": len(self.pre_particle_integration.integrated),
            "events": len(self.event_log),
            "origin_signature": self.origin_signature,
        }
