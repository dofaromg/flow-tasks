"""Tests for Particle Unified System — origin_signature: MrLiouWord"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from particle_unified_system.particle_types import (
    Particle, ParticleField, ParticleType, ANCHOR, SEED, JUMP, MEMORY, FUSION, SYMBOLS, JUMP_MASK,
)
from particle_unified_system.particle_math import ParticleMath
from particle_unified_system.reality_layers import JumpNetwork, RealityLayer, GRAVITY_THRESHOLD
from particle_unified_system.fluin_language import FluinInterpreter, FlpkgLoader
from particle_unified_system.existence_proof import ExistenceProof
from particle_unified_system.parallel_world_bridge import ParallelWorldBridge, R_TO_L_MAP, L_TO_R_MAP


# ── Particle Types ──

def test_particle_types_bit_ids():
    assert ANCHOR.value == 0x01
    assert SEED.value == 0x02
    assert JUMP.value == 0x04
    assert MEMORY.value == 0x08
    assert FUSION.value == 0x10
    print("✓ particle_types_bit_ids")

def test_particle_symbols():
    assert SYMBOLS[ANCHOR] == "Ⓟ"
    assert SYMBOLS[SEED] == "Ⓘ"
    assert SYMBOLS[JUMP] == "↯"
    assert SYMBOLS[MEMORY] == "⧫"
    assert SYMBOLS[FUSION] == "⨁"
    print("✓ particle_symbols")

def test_particle_creation():
    p = Particle(ptype=ANCHOR, energy=2.5, position=[1.0, 2.0, 3.0], reality_layer=0)
    assert p.symbol == "Ⓟ"
    assert p.bit_id == "0x01"
    assert p.energy == 2.5
    assert p.origin_signature == "MrLiouWord"
    assert len(p.hash()) == 64
    print("✓ particle_creation")

def test_particle_can_jump():
    assert Particle(ptype=JUMP).can_jump is True
    assert Particle(ptype=FUSION).can_jump is True
    assert Particle(ptype=ANCHOR).can_jump is False
    assert Particle(ptype=SEED).can_jump is False
    assert Particle(ptype=MEMORY).can_jump is False
    print("✓ particle_can_jump")

def test_particle_to_dict():
    p = Particle(ptype=SEED, energy=1.0)
    d = p.to_dict()
    assert d["type"] == "SEED"
    assert d["symbol"] == "Ⓘ"
    assert d["origin_signature"] == "MrLiouWord"
    print("✓ particle_to_dict")

def test_particle_field_crud():
    f = ParticleField("test")
    p1 = f.create(ANCHOR, energy=1.0)
    p2 = f.create(SEED, energy=2.0)
    assert len(f.particles) == 2
    assert f.get(p1.id) is not None
    assert f.remove(p1.id) is True
    assert f.remove("nonexistent") is False
    assert len(f.particles) == 1
    print("✓ particle_field_crud")

def test_particle_field_combine():
    f = ParticleField("test")
    a = f.create(ANCHOR, energy=1.0)
    b = f.create(SEED, energy=2.0)
    c = f.combine(a.id, b.id)
    assert c is not None
    assert c.energy == 3.0
    assert c.ptype == FUSION
    assert f.combine("x", "y") is None
    print("✓ particle_field_combine")

def test_particle_field_fuse_all():
    f = ParticleField("test")
    ids = [f.create(SEED, energy=1.0).id for _ in range(5)]
    fused = f.fuse_all(ids)
    assert fused is not None
    assert fused.energy == 5.0
    assert f.fuse_all(["single"]) is None
    print("✓ particle_field_fuse_all")

def test_particle_field_filters():
    f = ParticleField("test")
    f.create(ANCHOR, reality_layer=0)
    f.create(ANCHOR, reality_layer=0)
    f.create(SEED, reality_layer=1)
    assert len(f.filter_by_type(ANCHOR)) == 2
    assert len(f.filter_by_layer(0)) == 2
    assert len(f.filter_by_layer(1)) == 1
    print("✓ particle_field_filters")

def test_particle_field_stats():
    f = ParticleField("test")
    f.create(ANCHOR, energy=1.0)
    f.create(SEED, energy=2.0)
    s = f.stats()
    assert s["total_particles"] == 2
    assert s["total_energy"] == 3.0
    assert s["origin_signature"] == "MrLiouWord"
    print("✓ particle_field_stats")


# ── Particle Math ──

def test_math_expand():
    pm = ParticleMath(alpha=1.0)
    p = Particle(ptype=SEED, energy=1.0)
    result = pm.expand(p, n=2, t=1.0)
    assert result > p.energy  # expanded should be larger
    assert result > 3.0       # ∫₀² e^λ dλ ≈ e²-1 ≈ 6.39
    print(f"✓ math_expand result={result}")

def test_math_expand_zero():
    pm = ParticleMath()
    p = Particle(ptype=SEED, energy=5.0)
    assert pm.expand(p, n=0) == 5.0
    print("✓ math_expand_zero")

def test_math_expand_particle():
    pm = ParticleMath()
    p = Particle(ptype=SEED, energy=1.0, reality_layer=1)
    ep = pm.expand_particle(p, n=2)
    assert ep.energy > 1.0
    assert ep.reality_layer == 3
    assert ep.properties["expanded_from"] == p.id
    print(f"✓ math_expand_particle energy={ep.energy}")

def test_math_compress():
    pm = ParticleMath(beta=1.0, omega=2.0)
    values = [1.0, 2.0, 4.0]
    result = pm.compress(values, n=2)
    # 1.0*2^0 + 2.0*2^(-1) + 4.0*2^(-2) = 1 + 1 + 1 = 3.0
    assert abs(result - 3.0) < 0.001
    print(f"✓ math_compress result={result}")

def test_math_compress_empty():
    pm = ParticleMath()
    assert pm.compress([], n=0) == 0.0
    assert pm.compress([1.0], n=-1) == 0.0
    print("✓ math_compress_empty")

def test_math_compress_particle():
    pm = ParticleMath()
    p = Particle(ptype=SEED, energy=1.0, reality_layer=3)
    cp = pm.compress_particle(p, n=2)
    assert cp.reality_layer == 1
    assert cp.properties["compressed_from"] == p.id
    print(f"✓ math_compress_particle energy={cp.energy}")

def test_math_evolve():
    pm = ParticleMath()
    p = Particle(ptype=SEED, energy=2.0)
    evolved = pm.evolve(p, env_factor=1.5, internal_factor=0.8)
    assert abs(evolved.energy - 2.4) < 0.001  # 1.5 * 2.0 * 0.8
    print(f"✓ math_evolve energy={evolved.energy}")

def test_math_evolve_steps():
    pm = ParticleMath()
    p = Particle(ptype=SEED, energy=1.0)
    trajectory = pm.evolve_steps(p, steps=3, env_factors=[1.1, 1.2, 0.9])
    assert len(trajectory) == 4
    assert trajectory[-1].energy != 1.0
    print(f"✓ math_evolve_steps final_energy={trajectory[-1].energy}")

def test_math_version_convert():
    pm = ParticleMath()
    p = Particle(ptype=SEED, energy=1.0)
    upgraded = pm.convert_version(p, 0.5, 1.0)
    assert upgraded.energy > 1.0
    downgraded = pm.convert_version(p, 1.0, 0.5)
    assert downgraded.properties.get("compressed_from") == p.id
    same = pm.convert_version(p, 1.0, 1.0)
    assert same.id == p.id
    print("✓ math_version_convert")


# ── Reality Layers & Jump Network ──

def test_reality_layers_init():
    jn = JumpNetwork()
    assert len(jn.layers) == 5
    r0 = jn.get_layer(0)
    assert r0.name_zh == "種子/場層"
    r4 = jn.get_layer(4)
    assert r4.name_zh == "母體核心層"
    assert jn.get_layer(99) is None
    print("✓ reality_layers_init")

def test_jump_energy_cost():
    jn = JumpNetwork()
    cost1 = jn.calculate_energy_cost(1)
    cost2 = jn.calculate_energy_cost(2)
    cost4 = jn.calculate_energy_cost(4)
    assert cost1 < cost2 < cost4
    assert abs(cost1 - 0.1) < 0.001  # 0.1 * 1^2.5
    print(f"✓ jump_energy_cost d=1:{cost1} d=2:{cost2} d=4:{cost4}")

def test_jump_gravity_coherence():
    jn = JumpNetwork()
    c1 = jn.calculate_gravity_coherence(1.0, 1.0)
    assert c1 == 1.0
    c2 = jn.calculate_gravity_coherence(1.0, 0.5)
    assert c2 == 0.5
    c3 = jn.calculate_gravity_coherence(0.0, 0.0)
    assert c3 == 1.0
    print("✓ jump_gravity_coherence")

def test_jump_success():
    jn = JumpNetwork()
    p = Particle(ptype=JUMP, energy=5.0, reality_layer=1, gravity=0.9)
    result = jn.jump(p, 2)
    assert result.success is True
    assert p.reality_layer == 2
    assert p.energy < 5.0
    print(f"✓ jump_success cost={result.energy_cost}")

def test_jump_fail_type_mask():
    jn = JumpNetwork()
    p = Particle(ptype=ANCHOR, energy=5.0, reality_layer=0)
    result = jn.jump(p, 1)
    assert result.success is False
    assert "JUMP_MASK" in result.reason
    print(f"✓ jump_fail_type_mask reason={result.reason}")

def test_jump_fail_not_accepted():
    jn = JumpNetwork()
    p = Particle(ptype=JUMP, energy=5.0, reality_layer=0, gravity=1.0)
    # R3 only accepts FUSION and MEMORY, not JUMP
    result = jn.jump(p, 3)
    assert result.success is False
    assert "does not accept" in result.reason
    print(f"✓ jump_fail_not_accepted reason={result.reason}")

def test_jump_fail_energy():
    jn = JumpNetwork()
    p = Particle(ptype=FUSION, energy=0.001, reality_layer=0, gravity=0.5)
    result = jn.jump(p, 4)
    assert result.success is False
    assert "insufficient energy" in result.reason
    print(f"✓ jump_fail_energy reason={result.reason}")

def test_jump_fail_invalid_layer():
    jn = JumpNetwork()
    p = Particle(ptype=JUMP, energy=5.0)
    result = jn.jump(p, 99)
    assert result.success is False
    assert "does not exist" in result.reason
    print("✓ jump_fail_invalid_layer")

def test_jump_place():
    jn = JumpNetwork()
    p = Particle(ptype=SEED, reality_layer=0)
    assert jn.place(p) is True
    assert p.id in jn.layers[0].particles
    p2 = Particle(ptype=SEED, reality_layer=99)
    assert jn.place(p2) is False
    print("✓ jump_place")

def test_jump_stats():
    jn = JumpNetwork()
    p = Particle(ptype=FUSION, energy=5.0, reality_layer=0, gravity=0.5)
    jn.jump(p, 4)
    s = jn.stats()
    assert s["total_jumps"] == 1
    assert "R0" in s["layers"]
    print("✓ jump_stats")


# ── Fluin Language ──

def test_fluin_create_particle():
    fi = FluinInterpreter()
    results = fi.execute('⏤myanchor⏤ := { "type": "anchor", "energy": 2.5 }')
    assert len(results) == 1
    assert results[0]["action"] == "define"
    assert "myanchor" in fi.variables
    print("✓ fluin_create_particle")

def test_fluin_expand():
    fi = FluinInterpreter()
    fi.execute('⏤s⏤ := { "type": "seed", "energy": 1.0 }')
    results = fi.execute("EXPAND(s, level=2)")
    assert results[0]["action"] == "expand"
    assert results[0]["expanded_energy"] > 1.0
    print(f"✓ fluin_expand energy={results[0]['expanded_energy']}")

def test_fluin_compress():
    fi = FluinInterpreter()
    fi.execute('⏤s⏤ := { "type": "seed", "energy": 1.0 }')
    results = fi.execute("COMPRESS(s, level=2)")
    assert results[0]["action"] == "compress"
    print(f"✓ fluin_compress energy={results[0]['compressed_energy']}")

def test_fluin_combine():
    fi = FluinInterpreter()
    fi.execute('⏤a⏤ := { "type": "anchor", "energy": 1.0 }')
    fi.execute('⏤b⏤ := { "type": "seed", "energy": 2.0 }')
    results = fi.execute("COMBINE(a, b)")
    assert results[0]["action"] == "combine"
    assert results[0]["combined_energy"] == 3.0
    print("✓ fluin_combine")

def test_fluin_combine_operator():
    fi = FluinInterpreter()
    fi.execute('⏤x⏤ := { "type": "anchor", "energy": 1.0 }')
    fi.execute('⏤y⏤ := { "type": "seed", "energy": 1.0 }')
    results = fi.execute("x ⊕ y")
    assert results[0]["action"] == "combine"
    print("✓ fluin_combine_operator")

def test_fluin_jump():
    fi = FluinInterpreter()
    fi.execute('⏤j⏤ := { "type": "jump", "energy": 5.0 }')
    results = fi.execute("JUMP(j, FROM: R1, TO: R2)")
    assert results[0]["action"] == "jump"
    assert results[0]["success"] is True
    print("✓ fluin_jump")

def test_fluin_check():
    fi = FluinInterpreter()
    fi.execute('⏤p1⏤ := { "type": "seed", "energy": 3.0 }')
    fi.execute('⏤p2⏤ := { "type": "seed", "energy": 0.5 }')
    results = fi.execute("CHECK(energy > 1.0)")
    assert results[0]["action"] == "check"
    checks = results[0]["results"]
    p1_check = next(c for c in checks if c["name"] == "p1")
    p2_check = next(c for c in checks if c["name"] == "p2")
    assert p1_check["passes"] is True
    assert p2_check["passes"] is False
    print("✓ fluin_check")

def test_fluin_auto_resolve():
    fi = FluinInterpreter()
    results = fi.execute("EXPAND(particle.seed, level=1)")
    assert results[0]["action"] == "expand"
    assert "particle.seed" not in fi.variables or "seed" in fi.variables
    print("✓ fluin_auto_resolve")

def test_fluin_multiline():
    fi = FluinInterpreter()
    program = """
// MRLiou Particle Program
⏤a⏤ := { "type": "anchor", "energy": 1.0 }
⏤s⏤ := { "type": "seed", "energy": 2.0 }
COMBINE(a, s)
CHECK(energy > 0.5)
"""
    results = fi.execute(program)
    assert len(results) == 4
    print(f"✓ fluin_multiline results={len(results)}")

def test_fluin_ref_not_found():
    fi = FluinInterpreter()
    results = fi.execute("EXPAND(nonexistent, level=1)")
    assert "error" in results[0]
    print("✓ fluin_ref_not_found")


# ── FlpkgLoader ──

def test_flpkg_create_and_load():
    loader = FlpkgLoader()
    pkg = loader.create_package("TestModule", "1.0.0",
        particles=[{"type": "anchor"}, {"type": "seed"}],
        transforms=[{"rule": "expand"}])
    loaded = loader.load(pkg)
    assert loaded["valid"] is True
    assert loaded["particle_count"] == 2
    assert loaded["transform_count"] == 1
    print("✓ flpkg_create_and_load")

def test_flpkg_validate_invalid():
    loader = FlpkgLoader()
    assert loader.validate({}) is False
    assert loader.validate({"metadata": {}}) is False
    assert loader.validate({"metadata": {"name": "x", "version": "1"}, "particleDefinitions": []}) is True
    print("✓ flpkg_validate_invalid")

def test_flpkg_load_json():
    loader = FlpkgLoader()
    import json
    pkg = json.dumps({
        "metadata": {"name": "JsonPkg", "version": "0.1"},
        "particleDefinitions": [{"type": "seed"}],
    })
    loaded = loader.load_json(pkg)
    assert loaded["valid"] is True
    print("✓ flpkg_load_json")


# ── Existence Proof ──

def test_proof_genesis():
    ep = ExistenceProof("MrLiouWord")
    assert len(ep.chain) == 1
    assert ep.chain[0].identity == "MrLiouWord"
    assert ep.chain[0].claim.startswith("genesis")
    assert ep.verify_chain() is True
    print("✓ proof_genesis")

def test_proof_anchor_and_verify():
    ep = ExistenceProof("MrLiouWord")
    ep.anchor("created particle system")
    ep.anchor("deployed to cloud", data="deployment_hash_abc123")
    ep.anchor("connected starlink bridge")
    assert len(ep.chain) == 4
    assert ep.verify_chain() is True
    assert ep.verify_identity("MrLiouWord") is True
    assert ep.verify_identity("SomeoneElse") is False
    print("✓ proof_anchor_and_verify")

def test_proof_tamper_detection():
    ep = ExistenceProof("MrLiouWord")
    ep.anchor("claim1")
    ep.anchor("claim2")
    # Tamper with chain
    ep.chain[1].claim = "tampered"
    assert ep.verify_chain() is False
    print("✓ proof_tamper_detection")

def test_proof_merkle_root():
    ep = ExistenceProof("MrLiouWord")
    root1 = ep.merkle_root()
    ep.anchor("new claim")
    root2 = ep.merkle_root()
    assert root1 != root2
    assert len(root1) == 64
    print("✓ proof_merkle_root")

def test_proof_get_proof():
    ep = ExistenceProof("MrLiouWord")
    ep.anchor("test claim")
    proof = ep.get_proof(1)
    assert proof is not None
    assert proof["chain_valid"] is True
    assert proof["identity_verified"] is True
    assert ep.get_proof(999) is None
    print("✓ proof_get_proof")

def test_proof_export():
    ep = ExistenceProof("MrLiouWord")
    ep.anchor("export test")
    export = ep.export_chain()
    assert export["identity"] == "MrLiouWord"
    assert export["chain_length"] == 2
    assert len(export["anchors"]) == 2
    print("✓ proof_export")

def test_proof_stats():
    ep = ExistenceProof("MrLiouWord")
    s = ep.stats()
    assert s["chain_valid"] is True
    assert s["origin_signature"] == "MrLiouWord"
    print("✓ proof_stats")


# ── Parallel World Bridge ──

def test_bridge_r_to_l_mapping():
    b = ParallelWorldBridge()
    assert b.r_to_l(0) == ["L-1"]
    assert b.r_to_l(1) == ["L0", "L1"]
    assert b.r_to_l(2) == ["L2", "L3"]
    assert b.r_to_l(3) == ["L4", "L5"]
    assert b.r_to_l(4) == ["L6", "L7"]
    print("✓ bridge_r_to_l_mapping")

def test_bridge_l_to_r_mapping():
    b = ParallelWorldBridge()
    assert b.l_to_r("L-1") == 0
    assert b.l_to_r("L0") == 1
    assert b.l_to_r("L3") == 2
    assert b.l_to_r("L5") == 3
    assert b.l_to_r("L7") == 4
    print("✓ bridge_l_to_r_mapping")

def test_bridge_particle_jump():
    b = ParallelWorldBridge()
    p = Particle(ptype=FUSION, energy=5.0, reality_layer=0, gravity=0.5)
    result = b.particle_jump_to_network(p, target_r=4)
    assert result["jump"]["success"] is True
    assert result["network"]["route_needed"] is True
    assert result["proof_chain_length"] >= 3
    print("✓ bridge_particle_jump")

def test_bridge_particle_jump_fail():
    b = ParallelWorldBridge()
    p = Particle(ptype=ANCHOR, energy=0.01, reality_layer=0)
    result = b.particle_jump_to_network(p, target_r=4)
    assert result["jump"]["success"] is False
    print(f"✓ bridge_particle_jump_fail reason={result['jump']['reason']}")

def test_bridge_network_event():
    b = ParallelWorldBridge()
    result = b.network_event_to_particle("L2", "scale_up")
    assert result["reality_layer"] == 2
    assert result["env_factor"] == 1.5
    assert result["evolved_energy"] > result["original_energy"]
    print("✓ bridge_network_event")

def test_bridge_network_event_failure():
    b = ParallelWorldBridge()
    result = b.network_event_to_particle("L5", "failure")
    assert result["env_factor"] == 0.5
    assert result["evolved_energy"] < result["original_energy"]
    print("✓ bridge_network_event_failure")

def test_bridge_full_status():
    b = ParallelWorldBridge()
    p = Particle(ptype=FUSION, energy=5.0, reality_layer=0, gravity=0.5)
    b.particle_jump_to_network(p, 4)
    b.network_event_to_particle("L0", "recovery")
    status = b.full_system_status()
    assert "R0" in status["layers"]
    assert "R4" in status["layers"]
    assert status["proof_valid"] is True
    assert status["origin_signature"] == "MrLiouWord"
    print("✓ bridge_full_status")

def test_bridge_stats():
    b = ParallelWorldBridge()
    b.network_event_to_particle("L-1", "high_load")
    s = b.stats()
    assert s["l_to_r_events"] == 1
    assert s["origin_signature"] == "MrLiouWord"
    print("✓ bridge_stats")


# ── Run all ──

if __name__ == "__main__":
    tests = [
        test_particle_types_bit_ids, test_particle_symbols, test_particle_creation,
        test_particle_can_jump, test_particle_to_dict, test_particle_field_crud,
        test_particle_field_combine, test_particle_field_fuse_all,
        test_particle_field_filters, test_particle_field_stats,
        test_math_expand, test_math_expand_zero, test_math_expand_particle,
        test_math_compress, test_math_compress_empty, test_math_compress_particle,
        test_math_evolve, test_math_evolve_steps, test_math_version_convert,
        test_reality_layers_init, test_jump_energy_cost, test_jump_gravity_coherence,
        test_jump_success, test_jump_fail_type_mask, test_jump_fail_not_accepted,
        test_jump_fail_energy, test_jump_fail_invalid_layer, test_jump_place, test_jump_stats,
        test_fluin_create_particle, test_fluin_expand, test_fluin_compress,
        test_fluin_combine, test_fluin_combine_operator, test_fluin_jump,
        test_fluin_check, test_fluin_auto_resolve, test_fluin_multiline, test_fluin_ref_not_found,
        test_flpkg_create_and_load, test_flpkg_validate_invalid, test_flpkg_load_json,
        test_proof_genesis, test_proof_anchor_and_verify, test_proof_tamper_detection,
        test_proof_merkle_root, test_proof_get_proof, test_proof_export, test_proof_stats,
        test_bridge_r_to_l_mapping, test_bridge_l_to_r_mapping, test_bridge_particle_jump,
        test_bridge_particle_jump_fail, test_bridge_network_event,
        test_bridge_network_event_failure, test_bridge_full_status, test_bridge_stats,
    ]
    passed = failed = 0
    for t in tests:
        try:
            t()
            passed += 1
        except Exception as e:
            print(f"✗ {t.__name__}: {e}")
            import traceback; traceback.print_exc()
            failed += 1
    print(f"\n{'='*50}")
    print(f"Results: {passed} passed, {failed} failed, {passed+failed} total")
    if failed: exit(1)
    else: print("All tests passed!")
