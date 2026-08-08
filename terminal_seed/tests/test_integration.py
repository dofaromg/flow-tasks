"""Tests for Integration Layer — PreParticle, QuantumBridge, DualBrain. origin_signature: MrLiouWord"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

import pytest
from terminal_seed.terminal import InvariantError, ORIGIN_SIGNATURE
from terminal_seed.integration import (
    PreParticle, SystemParticle, PreParticleIntegration,
    QuantumBridge, QuantumWorld, QuantumState,
    DualBrain,
    TerminalParticleBridge,
)


# ── PreParticle Integration ──

def test_pre_particle_creation():
    pp = PreParticle(N_k=2.5, eta_k=0.8)
    assert pp.origin_signature == ORIGIN_SIGNATURE
    assert pp.N_k == 2.5
    assert pp.eta_k == 0.8
    assert len(pp.id) == 12


def test_integrate_pre_particle():
    ppi = PreParticleIntegration()
    pp = PreParticle(N_k=1.5, eta_k=0.9)
    sp = ppi.integrate(pp)
    assert isinstance(sp, SystemParticle)
    assert sp.derived_from == pp.id
    assert sp.structure_factor == 1.5
    assert sp.environment_factor == 0.9
    assert sp.origin_signature == ORIGIN_SIGNATURE


def test_integrate_batch():
    ppi = PreParticleIntegration()
    pps = [PreParticle(N_k=float(i), eta_k=0.5) for i in range(5)]
    results = ppi.integrate_batch(pps)
    assert len(results) == 5
    assert len(ppi.integrated) == 5


def test_integrate_law0_violation():
    ppi = PreParticleIntegration()
    pp = PreParticle()
    pp.origin_signature = "WRONG"
    with pytest.raises(InvariantError, match="LAW-0"):
        ppi.integrate(pp)


# ── QuantumBridge ──

def test_quantum_bridge_creation():
    qb = QuantumBridge()
    assert qb.origin_signature == ORIGIN_SIGNATURE
    assert qb.terminal is not None


def test_quantum_bridge_map_algorithm():
    qb = QuantumBridge()
    result = qb.map_algorithm("test_algo", complexity=3, steps=10)
    assert result["algorithm_id"] == "test_algo"
    assert result["steps_run"] == 10
    assert result["final_coherence"] > 0
    assert result["origin_signature"] == ORIGIN_SIGNATURE


def test_quantum_bridge_coherence_decays():
    qb = QuantumBridge()
    short = qb.map_algorithm("short", complexity=3, steps=5)
    long = qb.map_algorithm("long", complexity=3, steps=50)
    # Coherence should decay more with more steps
    assert long["final_coherence"] <= short["final_coherence"]


def test_quantum_bridge_high_complexity():
    qb = QuantumBridge()
    result = qb.map_algorithm("complex", complexity=8, steps=10)
    assert result["final_dimensionality"] == 8  # complexity > 5 → dim=8


def test_quantum_world_to_dict():
    qw = QuantumWorld(algorithm_id="test", entanglement=0.7)
    d = qw.to_dict()
    assert d["algorithm_id"] == "test"
    assert d["entanglement"] == 0.7
    assert d["origin_signature"] == ORIGIN_SIGNATURE


def test_quantum_state_to_dict():
    qs = QuantumState(coherence=0.9, collapsed=False)
    d = qs.to_dict()
    assert d["coherence"] == 0.9
    assert d["collapsed"] is False


# ── DualBrain ──

def test_dual_brain_creation():
    db = DualBrain()
    assert db.origin_signature == ORIGIN_SIGNATURE


def test_dual_brain_process_string():
    db = DualBrain()
    result = db.process("hello world", steps=3)
    assert result["origin_signature"] == ORIGIN_SIGNATURE
    assert result["confidence"] >= 0.5
    assert result["steps"] == 3
    assert result["cerebrum_analysis"] is not None


def test_dual_brain_process_none():
    db = DualBrain()
    result = db.process(None, steps=2)
    assert result["steps"] == 2
    assert result["origin_signature"] == ORIGIN_SIGNATURE


def test_dual_brain_confidence_increases():
    db = DualBrain()
    r1 = db.process("data", steps=1)
    r2 = db.process("data", steps=5)
    assert r2["confidence"] >= r1["confidence"]


def test_dual_brain_cerebellum_integration():
    """DualBrain observe resets cerebellum_result each cycle.
    The cerebrum_analysis should always be present after processing."""
    db = DualBrain()
    result = db.process("test data", steps=3)
    cerebrum = result["cerebrum_analysis"]
    assert cerebrum is not None
    assert "patterns" in cerebrum
    assert "complexity" in cerebrum


# ── TerminalParticleBridge ──

def test_bridge_creation():
    bridge = TerminalParticleBridge()
    assert bridge.origin_signature == ORIGIN_SIGNATURE


def test_bridge_pre_particle_to_system():
    bridge = TerminalParticleBridge()
    sp = bridge.pre_particle_to_system(N_k=2.0, eta_k=0.7)
    assert isinstance(sp, SystemParticle)
    assert sp.structure_factor == 2.0
    assert sp.environment_factor == 0.7
    assert len(bridge.event_log) == 1


def test_bridge_terminal_evolve():
    bridge = TerminalParticleBridge()
    trajectory = bridge.terminal_evolve(1.0, steps=5)
    assert len(trajectory) == 5
    assert trajectory[0]["t"] == 0
    assert trajectory[4]["t"] == 4
    # Values should evolve
    assert trajectory[4]["state_value"] != trajectory[0]["state_value"]


def test_bridge_quantum_analyze():
    bridge = TerminalParticleBridge()
    result = bridge.quantum_analyze("algo1", complexity=4)
    assert result["algorithm_id"] == "algo1"
    assert result["origin_signature"] == ORIGIN_SIGNATURE


def test_bridge_dual_brain_analyze():
    bridge = TerminalParticleBridge()
    result = bridge.dual_brain_analyze("test input")
    assert result["origin_signature"] == ORIGIN_SIGNATURE
    assert result["confidence"] > 0


def test_bridge_stats():
    bridge = TerminalParticleBridge()
    bridge.pre_particle_to_system(1.0, 1.0)
    bridge.pre_particle_to_system(2.0, 2.0)
    s = bridge.stats()
    assert s["pre_particles_integrated"] == 2
    assert s["events"] == 2
    assert s["origin_signature"] == ORIGIN_SIGNATURE


def test_bridge_full_pipeline():
    """End-to-end: pre-particle → terminal evolve → quantum → dual brain."""
    bridge = TerminalParticleBridge()

    # Step 1: Integrate pre-particle
    sp = bridge.pre_particle_to_system(1.5, 0.8)
    assert sp.state == "initialized"

    # Step 2: Terminal evolution
    traj = bridge.terminal_evolve(sp.structure_factor, steps=5)
    assert len(traj) == 5

    # Step 3: Quantum analysis
    qa = bridge.quantum_analyze("pipeline_test", complexity=4)
    assert qa["final_coherence"] > 0

    # Step 4: Dual brain analysis
    db = bridge.dual_brain_analyze(traj[-1])
    assert db["confidence"] > 0

    # All events logged
    assert len(bridge.event_log) == 4
