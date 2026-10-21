"""Tests for Metacode System — L0-L7 consciousness layers. origin_signature: MrLiouWord"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

import pytest
from terminal_seed.metacode_system import (
    MetacodeSystem, Certificate, CertificateMapping,
    Role, CertType, SourceMode, LAYERS, QUANTUM_SPLIT_PAIRS,
    ORIGIN_SIGNATURE, LayerDef,
)


# ── Certificate ──

def test_certificate_creation():
    c = Certificate(role=Role.AR_SYS, level=0)
    assert c.origin_signature == ORIGIN_SIGNATURE
    assert c.role == Role.AR_SYS
    assert c.level == 0
    assert len(c.certificate_id) == 16
    assert len(c.source_hash) == 16


def test_certificate_to_dict():
    c = Certificate(role=Role.AR_USR, level=3, cert_type=CertType.CERT_NEW)
    d = c.to_dict()
    assert d["role"] == "AR_USR"
    assert d["level"] == 3
    assert d["cert_type"] == "CERT_NEW"
    assert d["origin_signature"] == ORIGIN_SIGNATURE


def test_certificate_source_hash_deterministic():
    c1 = Certificate(role=Role.AR_SYS, level=2, parent_cert="abc")
    c2 = Certificate(role=Role.AR_SYS, level=2, parent_cert="abc")
    assert c1.source_hash == c2.source_hash


def test_certificate_different_params_different_hash():
    c1 = Certificate(role=Role.AR_SYS, level=0)
    c2 = Certificate(role=Role.AR_USR, level=0)
    assert c1.source_hash != c2.source_hash


# ── CertificateMapping ──

def test_mapping_validation():
    m = CertificateMapping(
        old_cert_id="aaa", new_cert_id="bbb",
        level_mapping={0: 0},
    )
    assert m.validate() is True


def test_mapping_tampered_fails():
    m = CertificateMapping(
        old_cert_id="aaa", new_cert_id="bbb",
        level_mapping={0: 0},
    )
    m.validation_hash = "tampered"
    assert m.validate() is False


# ── Layer definitions ──

def test_all_layers_defined():
    for level in range(8):
        assert level in LAYERS
        layer = LAYERS[level]
        assert isinstance(layer, LayerDef)
        assert layer.level == level
        assert len(layer.name) > 0
        assert len(layer.name_zh) > 0


def test_quantum_split_pairs():
    assert QUANTUM_SPLIT_PAIRS == [(0, 1), (2, 3), (4, 5), (6, 7)]


# ── MetacodeSystem initialization ──

def test_system_init():
    ms = MetacodeSystem()
    assert ms.cycle_status == "initialized"
    assert ms.origin_signature == ORIGIN_SIGNATURE


def test_source_duality_on_init():
    ms = MetacodeSystem()
    duality = ms.validate_source_duality()
    assert duality["duality_intact"] is True
    assert duality["sys_source_exists"] is True
    assert duality["usr_source_exists"] is True
    assert duality["mapping_valid"] is True
    assert duality["parent_link_valid"] is True


def test_initial_certificates_count():
    ms = MetacodeSystem()
    # 2 source certs (L0 sys + L0 usr) + 7 sys levels + 7 usr levels = 16
    assert len(ms.certificates) == 16


def test_initial_mappings_count():
    ms = MetacodeSystem()
    # 1 source mapping + 7 level mappings = 8
    assert len(ms.mappings) == 8


def test_certificates_at_each_level():
    ms = MetacodeSystem()
    for level in range(8):
        certs = ms.get_certificates_at_level(level)
        assert len(certs) >= 2  # at least sys + usr


# ── Certificate operations ──

def test_create_certificate():
    ms = MetacodeSystem()
    c = ms.create_certificate(Role.AR_AST, 4, CertType.CERT_MAP)
    assert c.role == Role.AR_AST
    assert c.level == 4
    assert c.certificate_id in ms.certificates


def test_get_certificate():
    ms = MetacodeSystem()
    c = ms.create_certificate(Role.AR_TOOL, 2, CertType.CERT_OLD)
    retrieved = ms.get_certificate(c.certificate_id)
    assert retrieved is c


def test_get_nonexistent_certificate():
    ms = MetacodeSystem()
    assert ms.get_certificate("nonexistent") is None


def test_map_certificates():
    ms = MetacodeSystem()
    old = ms.create_certificate(Role.AR_SYS, 3, CertType.CERT_OLD)
    new = ms.create_certificate(Role.AR_USR, 3, CertType.CERT_NEW)
    mapping = ms.map_certificates(old, new)
    assert mapping.old_cert_id == old.certificate_id
    assert mapping.new_cert_id == new.certificate_id
    assert ms.validate_mapping(mapping) is True


def test_validate_mapping_missing_cert():
    ms = MetacodeSystem()
    mapping = CertificateMapping(
        old_cert_id="missing1", new_cert_id="missing2",
        level_mapping={0: 0},
    )
    assert ms.validate_mapping(mapping) is False


# ── Quantum split ──

def test_quantum_split_l0_to_l1():
    ms = MetacodeSystem()
    source = ms.create_certificate(Role.AR_SYS, 0, CertType.CERT_OLD)
    results = ms.quantum_split(0, source)
    assert len(results) == 1  # L0→L1 produces 1
    assert all(c.level == 1 for c in results)
    assert all(c.parent_cert == source.certificate_id for c in results)


def test_quantum_split_l2_to_l3():
    ms = MetacodeSystem()
    source = ms.create_certificate(Role.AR_SYS, 2, CertType.CERT_OLD)
    results = ms.quantum_split(2, source)
    assert len(results) == 2  # L2→L3 produces 2


def test_quantum_split_l4_to_l5():
    ms = MetacodeSystem()
    source = ms.create_certificate(Role.AR_SYS, 4, CertType.CERT_OLD)
    results = ms.quantum_split(4, source)
    assert len(results) == 3  # L4→L5 produces 3


def test_quantum_split_l6_to_l7():
    ms = MetacodeSystem()
    source = ms.create_certificate(Role.AR_SYS, 6, CertType.CERT_OLD)
    results = ms.quantum_split(6, source)
    assert len(results) == 4  # L6→L7 produces 4


def test_quantum_split_invalid_pair():
    ms = MetacodeSystem()
    source = ms.create_certificate(Role.AR_SYS, 1, CertType.CERT_OLD)
    results = ms.quantum_split(1, source)  # L1→L2 is not a valid pair
    assert results == []


def test_quantum_split_log():
    ms = MetacodeSystem()
    source = ms.create_certificate(Role.AR_SYS, 0, CertType.CERT_OLD)
    ms.quantum_split(0, source)
    assert len(ms.split_log) == 1
    assert ms.split_log[0]["from_level"] == 0
    assert ms.split_log[0]["to_level"] == 1


# ── Simhash / Merkle ──

def test_simhash64():
    ms = MetacodeSystem()
    h1 = ms.simhash64(["hello", "world"])
    h2 = ms.simhash64(["hello", "world"])
    assert h1 == h2  # deterministic
    h3 = ms.simhash64(["different", "tokens"])
    # Different tokens should (usually) produce different hashes
    assert isinstance(h3, int)


def test_hamming_distance():
    ms = MetacodeSystem()
    assert ms.hamming_distance(0b1010, 0b1010) == 0
    assert ms.hamming_distance(0b1010, 0b0101) == 4
    assert ms.hamming_distance(0b1111, 0b0000) == 4


def test_merkle_fold():
    ms = MetacodeSystem()
    result = ms.merkle_fold([1, 2, 3, 4])
    assert isinstance(result, int)
    assert result > 0


def test_merkle_fold_empty():
    ms = MetacodeSystem()
    assert ms.merkle_fold([]) == 0


def test_merkle_fold_single():
    ms = MetacodeSystem()
    assert ms.merkle_fold([42]) == 42


# ── Layer queries ──

def test_get_layer_def():
    ms = MetacodeSystem()
    l0 = ms.get_layer_def(0)
    assert l0.name == "Pure Consciousness"
    assert l0.name_zh == "純粹意識"
    l7 = ms.get_layer_def(7)
    assert l7.name == "Cycle Carrier"


def test_get_layer_def_invalid():
    ms = MetacodeSystem()
    assert ms.get_layer_def(99) is None


# ── Stats ──

def test_stats():
    ms = MetacodeSystem()
    s = ms.stats()
    assert s["total_certificates"] == 16
    assert s["mappings"] == 8
    assert s["splits"] == 0
    assert s["cycle_status"] == "initialized"
    assert s["source_duality"] is True
    assert s["origin_signature"] == ORIGIN_SIGNATURE
