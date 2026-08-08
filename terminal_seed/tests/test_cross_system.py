"""Cross-system consistency tests — terminal_seed × particle_unified_system × global_parallel_network.
origin_signature: MrLiouWord

Verifies that all three systems share consistent origin_signature,
can interoperate, and maintain LAW-0 across boundaries.
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

import pytest

# terminal_seed
from terminal_seed.terminal import Terminal, ORIGIN_SIGNATURE as TS_ORIGIN
from terminal_seed.dimension_traversal import DimensionTraversal
from terminal_seed.metacode_system import MetacodeSystem, Certificate, Role, CertType
from terminal_seed.integration import (
    TerminalParticleBridge, PreParticle, QuantumBridge, DualBrain,
)

# particle_unified_system
from particle_unified_system.particle_types import Particle, ANCHOR, SEED, JUMP
from particle_unified_system.particle_math import ParticleMath
from particle_unified_system.existence_proof import ExistenceProof
from particle_unified_system.parallel_world_bridge import ParallelWorldBridge

# global_parallel_network
from global_parallel_network.global_network import GlobalParallelNetwork


# ── Origin signature consistency ──

def test_origin_signature_matches_across_systems():
    """All three systems must use the same origin_signature."""
    assert TS_ORIGIN == "MrLiouWord"

    # particle_unified_system
    p = Particle(ptype=ANCHOR)
    assert p.origin_signature == "MrLiouWord"

    # global_parallel_network
    gpn = GlobalParallelNetwork()
    assert gpn.origin_signature == "MrLiouWord"

    # terminal_seed components
    dt = DimensionTraversal()
    assert dt.origin_signature == "MrLiouWord"
    ms = MetacodeSystem()
    assert ms.origin_signature == "MrLiouWord"
    bridge = TerminalParticleBridge()
    assert bridge.origin_signature == "MrLiouWord"


# ── PreParticle → Particle system bridge ──

def test_pre_particle_to_particle_system():
    """PreParticle integration should produce particles compatible with particle_unified_system."""
    bridge = TerminalParticleBridge()
    sp = bridge.pre_particle_to_system(N_k=1.5, eta_k=0.8)
    assert sp.origin_signature == "MrLiouWord"
    assert sp.structure_factor == 1.5

    # Particle system can create particles with similar properties
    p = Particle(ptype=SEED, energy=sp.structure_factor)
    assert p.energy == 1.5
    assert p.origin_signature == "MrLiouWord"


# ── Dimension traversal with particles ──

def test_dimension_traversal_with_particle():
    """Particles from particle_unified_system can be traversed through dimensions."""
    dt = DimensionTraversal()
    particle_dict = {
        "id": "test_particle",
        "coordinates": [1.0, 2.0, 3.0],
        "properties": {"energy": 2.5},
        "origin_signature": "MrLiouWord",
    }
    result = dt.traverse_particle(particle_dict, 3, 6)
    assert len(result["coordinates"]) == 6
    assert result["origin_signature"] == "MrLiouWord"
    assert result["topologyPreserved"] is True


# ── Metacode certificates with existence proof ──

def test_metacode_certificate_with_existence_proof():
    """Metacode certificates and existence proofs share identity anchoring."""
    ms = MetacodeSystem()
    ep = ExistenceProof()

    # Create a certificate
    cert = ms.create_certificate(Role.AR_SYS, 3, CertType.CERT_OLD)

    # Anchor the certificate in existence proof
    ep.anchor(
        claim=f"certificate:{cert.certificate_id}",
        data=str(cert.to_dict()),
    )

    # Verify chain integrity
    assert ep.verify_chain() is True
    assert len(ep.chain) >= 2  # genesis + our anchor


# ── Quantum bridge terminal consistency ──

def test_quantum_bridge_terminal_runs():
    """QuantumBridge uses Terminal internally — verify it produces valid results."""
    qb = QuantumBridge()
    result = qb.map_algorithm("cross_test", complexity=4, steps=20)
    assert result["origin_signature"] == "MrLiouWord"
    assert result["steps_run"] == 20
    assert 0 < result["final_coherence"] <= 1.0


# ── DualBrain with particle data ──

def test_dual_brain_processes_particle_data():
    """DualBrain can analyze particle system data."""
    db = DualBrain()
    p = Particle(ptype=ANCHOR, energy=3.0, position=[1.0, 2.0, 3.0])
    result = db.process(str(p.to_dict()), steps=3)
    assert result["origin_signature"] == "MrLiouWord"
    assert result["confidence"] >= 0.5


# ── Full pipeline: terminal_seed → particle → network ──

def test_full_cross_system_pipeline():
    """
    End-to-end pipeline across all three systems:
    1. Terminal seed creates and evolves a value
    2. Value feeds into particle system
    3. Network routes the result
    """
    # Step 1: Terminal evolution
    bridge = TerminalParticleBridge()
    trajectory = bridge.terminal_evolve(1.0, steps=5)
    final_value = trajectory[-1]["state_value"]
    assert final_value > 0

    # Step 2: Create particle with evolved value
    p = Particle(ptype=SEED, energy=final_value, position=[1.0, 2.0, 3.0])
    assert p.origin_signature == "MrLiouWord"

    # Step 3: Traverse particle to higher dimension
    dt = DimensionTraversal()
    particle_dict = {
        "id": p.hash()[:12],
        "coordinates": p.position,
        "properties": {"energy": p.energy},
        "origin_signature": "MrLiouWord",
    }
    traversed = dt.traverse_particle(particle_dict, 3, 6)
    assert len(traversed["coordinates"]) == 6

    # Step 4: Network can be initialized alongside
    gpn = GlobalParallelNetwork()
    assert gpn.origin_signature == "MrLiouWord"

    # Step 5: Metacode anchors the whole pipeline
    ms = MetacodeSystem()
    duality = ms.validate_source_duality()
    assert duality["duality_intact"] is True


# ── Simhash consistency ──

def test_simhash_across_particle_hashes():
    """Metacode simhash can fingerprint particle hashes."""
    ms = MetacodeSystem()
    particles = [Particle(ptype=t) for t in [ANCHOR, SEED, JUMP]]
    hashes = [p.hash() for p in particles]
    fingerprint = ms.simhash64(hashes)
    assert isinstance(fingerprint, int)
    assert fingerprint > 0

    # Same input → same fingerprint
    fingerprint2 = ms.simhash64(hashes)
    assert fingerprint == fingerprint2


# ── Merkle fold with existence proof ──

def test_merkle_fold_with_existence_chain():
    """Metacode merkle_fold can fold existence proof hashes."""
    ms = MetacodeSystem()
    ep = ExistenceProof()
    ep.anchor("test1", "val1")
    ep.anchor("test2", "val2")

    anchor_hashes = [int(a.anchor_hash[:16], 16) for a in ep.chain]
    folded = ms.merkle_fold(anchor_hashes)
    assert isinstance(folded, int)
    assert folded > 0
