#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MRL_OID_Parser_v1.py — ASN.1 OID / EC 參數解析器(PARK-01 兌現)
origin_signature: MrLiouWord
layer: L4 WORLD (對外材料解析)

緣起(Mr.liou):GTS Root R4 憑證顯示「無法剖析的參數 06 05 2b 81 04 00 22」,
憑證檢視器懶得解,丟原始 bytes。本模組把「無法剖析」變「可剖析」——
純 stdlib 解析 ASN.1 DER 裡的 OID,並對應已知的橢圓曲線。

驗證目標:06 05 2b 81 04 00 22
  06 = OID tag, 05 = length 5 bytes, 2b 81 04 00 22 = 1.3.132.0.34 = secp384r1 (NIST P-384)

零依賴。CLI:python3 09_workflow/MRL_OID_Parser_v1.py
"""
from __future__ import annotations

from typing import Dict, List, Optional, Tuple

from MRL_utils import ORIGIN_SIGNATURE
# 已知 OID 對照(可 additive 擴充,No-Delete)
KNOWN_OIDS: Dict[str, Dict[str, str]] = {
    "1.2.840.10045.3.1.7": {"name": "secp256r1", "alias": "NIST P-256 / prime256v1"},
    "1.3.132.0.34":        {"name": "secp384r1", "alias": "NIST P-384"},
    "1.3.132.0.35":        {"name": "secp521r1", "alias": "NIST P-521"},
    "1.3.132.0.10":        {"name": "secp256k1", "alias": "Koblitz (Bitcoin)"},
    "1.2.840.10045.2.1":   {"name": "id-ecPublicKey", "alias": "EC Public Key"},
    "1.2.840.113549.1.1.1":{"name": "rsaEncryption", "alias": "RSA"},
    "2.5.4.3":             {"name": "commonName", "alias": "CN"},
}


def _hex_to_bytes(s: str) -> bytes:
    """接受 '06 05 2b ...' 或 '060552b...' 形式。"""
    clean = s.replace(" ", "").replace(":", "").replace("\n", "").strip()
    if len(clean) % 2 != 0:
        raise ValueError("hex length must be even")
    return bytes(int(clean[i:i+2], 16) for i in range(0, len(clean), 2))


def decode_oid_bytes(data: bytes) -> str:
    """
    把 OID 的 value bytes(不含 tag/length)解成點分字串。
    規則(ASN.1 DER):
      - 第一 byte = 40*X + Y(X=第一節點 0/1/2,Y=第二節點)
      - 其餘:base-128,每 byte 高位 bit=1 表示續接,低 7 位是數值
    """
    if not data:
        raise ValueError("empty OID value")
    # 先 base-128 解出所有 subidentifier(第一個也可能多 byte)
    subids: List[int] = []
    value = 0
    for b in data:
        value = (value << 7) | (b & 0x7F)
        if not (b & 0x80):          # 高位 0 = 此 subidentifier 結束
            subids.append(value)
            value = 0
    if not subids:
        raise ValueError("no subidentifier decoded")
    # 第一 subidentifier 拆成前兩節點:<80 → X.Y(X=v//40,Y=v%40);>=80 → 2.(v-80)
    # (避免 v>=80 時 v//40 產生無效的第一節點 3)
    f = subids[0]
    if f < 80:
        nodes: List[int] = [f // 40, f % 40]
    else:
        nodes = [2, f - 80]
    nodes.extend(subids[1:])
    return ".".join(str(n) for n in nodes)


def parse_der_oid(der: bytes) -> Dict[str, object]:
    """
    解析完整 DER 編碼的 OID(含 tag 0x06 + length + value)。
    回傳 oid 字串 + 已知對應(若有)。
    """
    if len(der) < 2:
        raise ValueError("DER too short")
    tag = der[0]
    if tag != 0x06:
        raise ValueError(f"not an OID tag: 0x{tag:02x} (expected 0x06)")
    length = der[1]
    if length & 0x80:               # 長格式 length(此處只處理短格式,OID 通常 <128)
        raise ValueError("long-form length not supported for OID")
    value = der[2:2 + length]
    if len(value) != length:
        raise ValueError(f"length mismatch: declared {length}, got {len(value)}")
    oid = decode_oid_bytes(value)
    known = KNOWN_OIDS.get(oid)
    return {
        "tag": "0x06 (OBJECT IDENTIFIER)",
        "length": length,
        "oid": oid,
        "known": known is not None,
        "name": known["name"] if known else None,
        "alias": known["alias"] if known else None,
        "origin_signature": ORIGIN_SIGNATURE,
    }


def parse_hex(hexstr: str) -> Dict[str, object]:
    """從 hex 字串(如 '06 05 2b 81 04 00 22')解析。"""
    return parse_der_oid(_hex_to_bytes(hexstr))


def main() -> int:
    import json
    # 兌現 PARK-01:GTS Root R4 的「無法剖析的參數」
    target = "06 05 2b 81 04 00 22"
    result = parse_hex(target)
    print(f"輸入(憑證檢視器顯示『無法剖析』): {target}")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    assert result["oid"] == "1.3.132.0.34"
    assert result["name"] == "secp384r1"
    print("\n→ 已剖析:這就是 secp384r1 (NIST P-384) 橢圓曲線。")
    print("MRL_OID_PARSER_OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
