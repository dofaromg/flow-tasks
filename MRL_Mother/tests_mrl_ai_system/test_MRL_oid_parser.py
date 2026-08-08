"""
test_MRL_oid_parser.py — OID/EC 解析器驗收(PARK-01)
origin_signature: MrLiouWord
"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "09_workflow"))

import pytest  # noqa: E402

from MRL_OID_Parser_v1 import (  # noqa: E402
    parse_hex, parse_der_oid, decode_oid_bytes, _hex_to_bytes,
)


class TestPark01:
    def test_gts_root_r4_unparseable_param(self):
        # 兌現 PARK-01:GTS Root R4「無法剖析的參數」
        r = parse_hex("06 05 2b 81 04 00 22")
        assert r["oid"] == "1.3.132.0.34"
        assert r["name"] == "secp384r1"
        assert r["alias"] == "NIST P-384"
        assert r["origin_signature"] == "MrLiouWord"


class TestOIDDecode:
    def test_decode_value_only(self):
        assert decode_oid_bytes(bytes([0x2b, 0x81, 0x04, 0x00, 0x22])) == "1.3.132.0.34"

    def test_secp256r1(self):
        r = parse_hex("06 08 2a 86 48 ce 3d 03 01 07")
        assert r["oid"] == "1.2.840.10045.3.1.7"
        assert r["name"] == "secp256r1"

    def test_ec_public_key(self):
        r = parse_hex("06 07 2a 86 48 ce 3d 02 01")
        assert r["oid"] == "1.2.840.10045.2.1"
        assert r["name"] == "id-ecPublicKey"

    def test_first_byte_split(self):
        # 第一 byte 2b = 43 = 40*1+3 → 節點 1.3
        assert decode_oid_bytes(bytes([0x2b])) == "1.3"

    def test_base128_multibyte(self):
        # 0x81 0x04 = (1<<7)|4 = 132
        assert decode_oid_bytes(bytes([0x2b, 0x81, 0x04])).startswith("1.3.132")


class TestErrors:
    def test_wrong_tag(self):
        with pytest.raises(ValueError):
            parse_hex("02 01 00")          # 0x02 = INTEGER, 不是 OID

    def test_length_mismatch(self):
        with pytest.raises(ValueError):
            parse_hex("06 05 2b 81 04")     # 宣告 5 但只給 3

    def test_odd_hex(self):
        with pytest.raises(ValueError):
            _hex_to_bytes("06 5")

    def test_unknown_oid_still_decodes(self):
        # 未知 OID 仍能解出點分字串,只是 known=False
        r = parse_hex("06 03 88 37 03")
        assert r["known"] is False
        assert r["oid"] is not None


class TestFirstArcFix:
    """Codex review:first subidentifier >=80 不可產生無效 arc"""
    def test_first_byte_120_is_2_40(self):
        assert parse_hex("06 01 78")["oid"] == "2.40"   # 0x78=120 → 2.40 (非 3.0)
    def test_first_byte_40_is_1_0(self):
        assert parse_hex("06 01 28")["oid"] == "1.0"     # 0x28=40 → 1.0
    def test_secp384r1_unbroken(self):
        assert parse_hex("06 05 2b 81 04 00 22")["oid"] == "1.3.132.0.34"
