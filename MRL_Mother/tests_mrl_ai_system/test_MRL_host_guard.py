"""
test_MRL_host_guard.py — Unit tests for MRL_host_guard.py
origin_signature: MrLiouWord
product: MRL_AI_SYSTEM
"""
from __future__ import annotations

import os
import socket
import tempfile

import pytest

from MRL_host_guard import (
    DEFAULT_DL580_CONFIG,
    HostGuardConfig,
    NodeRole,
    _get_hostname_candidates,
    _get_ip_candidates,
    _ip_in_cidrs,
    _norm_host,
    _read_fingerprint,
    get_node_role,
    is_dl580_canonical_host,
    node_role_detail,
)


# ─── _norm_host ────────────────────────────────────────────────────────────────

class TestNormHost:
    def test_lowercases(self):
        assert _norm_host("WIN-PBVUI7VK2A6") == "win-pbvui7vk2a6"

    def test_strips_trailing_dot(self):
        assert _norm_host("host.example.com.") == "host.example.com"

    def test_strips_whitespace(self):
        assert _norm_host("  host  ") == "host"

    def test_empty_string(self):
        assert _norm_host("") == ""

    def test_none_like_empty(self):
        assert _norm_host(None) == ""   # type: ignore[arg-type]


# ─── _ip_in_cidrs ─────────────────────────────────────────────────────────────

class TestIpInCidrs:
    def test_loopback_in_loopback_cidr(self):
        assert _ip_in_cidrs("127.0.0.1", ["127.0.0.1/32"])

    def test_tailscale_ip(self):
        assert _ip_in_cidrs("100.78.70.78", ["100.78.70.78/32"])

    def test_wrong_ip_not_in_cidr(self):
        assert not _ip_in_cidrs("10.0.0.1", ["100.78.70.78/32", "127.0.0.1/32"])

    def test_ip_in_broad_cidr(self):
        assert _ip_in_cidrs("192.168.1.50", ["192.168.1.0/24"])

    def test_invalid_ip_returns_false(self):
        assert not _ip_in_cidrs("not-an-ip", ["127.0.0.1/32"])

    def test_invalid_cidr_skipped(self):
        # Invalid CIDR entry is skipped; valid one still matches
        assert _ip_in_cidrs("127.0.0.1", ["bad_cidr", "127.0.0.1/32"])


# ─── _read_fingerprint ────────────────────────────────────────────────────────

class TestReadFingerprint:
    def test_reads_existing_file(self, tmp_path):
        fp = tmp_path / "role.txt"
        fp.write_text("MRL_DL580_CANONICAL_MOTHER\n", encoding="utf-8")
        ok, val = _read_fingerprint(str(fp))
        assert ok is True
        assert val == "MRL_DL580_CANONICAL_MOTHER"

    def test_missing_file_returns_false(self, tmp_path):
        ok, msg = _read_fingerprint(str(tmp_path / "nonexistent.txt"))
        assert ok is False
        assert "not found" in msg

    def test_empty_path_returns_false(self):
        ok, msg = _read_fingerprint("")
        assert ok is False

    def test_strips_whitespace(self, tmp_path):
        fp = tmp_path / "role.txt"
        fp.write_text("  MRL_DL580_CANONICAL_MOTHER  \n", encoding="utf-8")
        ok, val = _read_fingerprint(str(fp))
        assert ok is True
        assert val == "MRL_DL580_CANONICAL_MOTHER"


# ─── is_dl580_canonical_host — forced true/false configs ─────────────────────

def _make_cfg(*, hostname=None, cidr=None, fp_file="", fp_value=""):
    """Build a HostGuardConfig with the current hostname/IP for forced-pass tests."""
    hn = hostname or [_norm_host(socket.gethostname())]
    ip = cidr or []
    return HostGuardConfig(
        hostname_allowlist=hn,
        cidr_allowlist=ip,
        fingerprint_file=fp_file,
        fingerprint_value=fp_value,
    )


class TestIsDl580CanonicalHost:
    def test_returns_false_when_hostname_not_in_allowlist(self, tmp_path):
        fp = tmp_path / "role.txt"
        fp.write_text("MRL_DL580_CANONICAL_MOTHER", encoding="utf-8")
        cfg = HostGuardConfig(
            hostname_allowlist=["definitely-not-this-machine-12345"],
            cidr_allowlist=[],
            fingerprint_file=str(fp),
            fingerprint_value="MRL_DL580_CANONICAL_MOTHER",
        )
        ok, reason = is_dl580_canonical_host(cfg)
        assert ok is False
        assert "hostname" in reason

    def test_returns_false_when_fingerprint_mismatch(self, tmp_path):
        fp = tmp_path / "role.txt"
        fp.write_text("WRONG_VALUE", encoding="utf-8")
        hn = _norm_host(socket.gethostname())
        cfg = HostGuardConfig(
            hostname_allowlist=[hn],
            cidr_allowlist=[],
            fingerprint_file=str(fp),
            fingerprint_value="MRL_DL580_CANONICAL_MOTHER",
        )
        ok, reason = is_dl580_canonical_host(cfg)
        assert ok is False
        assert "fingerprint" in reason

    def test_returns_false_when_fingerprint_file_missing(self):
        hn = _norm_host(socket.gethostname())
        cfg = HostGuardConfig(
            hostname_allowlist=[hn],
            cidr_allowlist=[],
            fingerprint_file="/nonexistent/path/role.txt",
            fingerprint_value="MRL_DL580_CANONICAL_MOTHER",
        )
        ok, reason = is_dl580_canonical_host(cfg)
        assert ok is False
        assert "fingerprint" in reason

    def test_returns_true_when_all_checks_pass(self, tmp_path):
        fp = tmp_path / "role.txt"
        fp.write_text("MRL_DL580_CANONICAL_MOTHER", encoding="utf-8")
        hn = _norm_host(socket.gethostname())
        cfg = HostGuardConfig(
            hostname_allowlist=[hn],
            cidr_allowlist=[],          # skip CIDR check
            fingerprint_file=str(fp),
            fingerprint_value="MRL_DL580_CANONICAL_MOTHER",
        )
        ok, reason = is_dl580_canonical_host(cfg)
        assert ok is True
        assert "verified" in reason

    def test_cidr_check_fails_when_no_ip_matches(self, tmp_path):
        import ipaddress

        fp = tmp_path / "role.txt"
        fp.write_text("MRL_DL580_CANONICAL_MOTHER", encoding="utf-8")
        hn = _norm_host(socket.gethostname())

        # Derive a /32 that is provably NOT any local candidate IP so the CIDR
        # check misses regardless of environment. Hardcoding a documentation
        # range (e.g. 192.0.2.0/24) is fragile — some sandboxes assign their
        # outbound IP from exactly that range, making the test flaky.
        candidates = set(_get_ip_candidates())
        probe = ipaddress.ip_address("198.51.100.7")  # TEST-NET-2
        while str(probe) in candidates:
            probe += 1
        no_match_cidr = f"{probe}/32"

        cfg = HostGuardConfig(
            hostname_allowlist=[hn],
            cidr_allowlist=[no_match_cidr],
            fingerprint_file=str(fp),
            fingerprint_value="MRL_DL580_CANONICAL_MOTHER",
        )
        ok, reason = is_dl580_canonical_host(cfg)
        assert ok is False
        assert "ip" in reason


# ─── get_node_role ────────────────────────────────────────────────────────────

class TestGetNodeRole:
    def test_returns_material_for_non_dl580(self):
        cfg = HostGuardConfig(
            hostname_allowlist=["definitely-not-this-machine-12345"],
            cidr_allowlist=[],
            fingerprint_file="/nonexistent",
            fingerprint_value="MRL_DL580_CANONICAL_MOTHER",
        )
        role = get_node_role(cfg)
        assert role is NodeRole.MATERIAL

    def test_returns_mother_when_all_pass(self, tmp_path):
        fp = tmp_path / "role.txt"
        fp.write_text("MRL_DL580_CANONICAL_MOTHER", encoding="utf-8")
        hn = _norm_host(socket.gethostname())
        cfg = HostGuardConfig(
            hostname_allowlist=[hn],
            cidr_allowlist=[],
            fingerprint_file=str(fp),
            fingerprint_value="MRL_DL580_CANONICAL_MOTHER",
        )
        role = get_node_role(cfg)
        assert role is NodeRole.MOTHER

    def test_noderole_is_string_enum(self):
        assert NodeRole.MOTHER.value   == "MOTHER"
        assert NodeRole.MATERIAL.value == "MATERIAL"


# ─── node_role_detail ────────────────────────────────────────────────────────

class TestNodeRoleDetail:
    def test_detail_has_required_keys(self):
        cfg = HostGuardConfig(
            hostname_allowlist=["not-this-host"],
            cidr_allowlist=[],
            fingerprint_file="/nonexistent",
            fingerprint_value="x",
        )
        d = node_role_detail(cfg)
        for key in ("role", "verified", "reason", "hostnames", "ips",
                    "origin_signature", "product_name", "checked_at_ms"):
            assert key in d, f"missing key: {key}"

    def test_origin_signature(self):
        d = node_role_detail()
        assert d["origin_signature"] == "MrLiouWord"
        assert d["product_name"] == "MRL_AI_SYSTEM"

    def test_material_role_when_not_dl580(self):
        cfg = HostGuardConfig(
            hostname_allowlist=["not-this-host"],
            cidr_allowlist=[],
            fingerprint_file="/nonexistent",
            fingerprint_value="x",
        )
        d = node_role_detail(cfg)
        assert d["role"] == "MATERIAL"
        assert d["verified"] is False


# ─── DEFAULT_DL580_CONFIG sanity checks ──────────────────────────────────────

class TestDefaultConfig:
    def test_hostnames_are_lowercase(self):
        for hn in DEFAULT_DL580_CONFIG.hostname_allowlist:
            assert hn == hn.lower(), f"hostname not lowercase: {hn}"

    def test_cidr_parseable(self):
        import ipaddress
        for cidr in DEFAULT_DL580_CONFIG.cidr_allowlist:
            ipaddress.ip_network(cidr, strict=False)  # must not raise

    def test_fingerprint_value_set(self):
        assert DEFAULT_DL580_CONFIG.fingerprint_value == "MRL_DL580_CANONICAL_MOTHER"
