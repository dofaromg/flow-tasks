"""
test_fltnz_parser.py — Smoke tests for fltnz_parser.py
origin_signature: MrLiouWord
"""
from __future__ import annotations

import hashlib
import json

import pytest

from fltnz_parser import (
    decode,
    encode,
    from_map,
    pack,
    seal,
    text_to_trace,
    to_map,
    trace_to_text,
    unpack,
    unseal,
    _tokenise,
    _compress_tokens,
    _decompress_tokens,
    _tokens_to_text,
    _sha256_text,
)


# ─── Tokeniser ────────────────────────────────────────────────────────────────

class TestTokeniser:
    def test_word_token(self):
        tokens = _tokenise("hello")
        assert len(tokens) == 1
        assert tokens[0] == {"t": "word", "v": "hello"}

    def test_newline_token(self):
        tokens = _tokenise("a\nb")
        types = [t["t"] for t in tokens]
        assert "nl" in types

    def test_whitespace_token(self):
        tokens = _tokenise("a b")
        types = [t["t"] for t in tokens]
        assert "ws" in types

    def test_roundtrip_tokenise(self):
        text = "Hello, world!\nSecond line."
        tokens = _tokenise(text)
        reconstructed = _tokens_to_text(tokens)
        assert reconstructed == text


# ─── Compression ─────────────────────────────────────────────────────────────

class TestCompression:
    def test_repeated_words_become_refs(self):
        tokens = _tokenise("the cat sat on the mat the cat")
        compressed = _compress_tokens(tokens)
        ref_count = sum(1 for t in compressed if t["t"] == "ref")
        assert ref_count > 0

    def test_decompress_roundtrip(self):
        text = "MRL MRL MRL system"
        raw = _tokenise(text)
        compressed = _compress_tokens(raw)
        decompressed = _decompress_tokens(compressed)
        result = _tokens_to_text(decompressed)
        assert result == text

    def test_invalid_ref_raises(self):
        tokens = [{"t": "ref", "v": 999}]
        with pytest.raises(ValueError, match="out of range"):
            _decompress_tokens(tokens)


# ─── Encode / Decode ─────────────────────────────────────────────────────────

class TestEncodeDecode:
    TEXTS = [
        "Hello world",
        "MRL AI system\nWith newlines\n  and spaces",
        "CJK: 你好世界 MrLiouWord",
        "Short",
        "Repeated repeated repeated repeated",
        "",  # empty string edge case
    ]

    @pytest.mark.parametrize("text", TEXTS)
    def test_roundtrip(self, text):
        envelope = encode(text)
        recovered = decode(envelope)
        assert recovered == text

    def test_envelope_has_required_keys(self):
        env = encode("test")
        assert "fltnz_version" in env
        assert "origin_signature" in env
        assert "checksum" in env
        assert "length" in env
        assert "tokens" in env

    def test_origin_signature(self):
        env = encode("test")
        assert env["origin_signature"] == "MrLiouWord"

    def test_checksum_matches(self):
        text = "verify me"
        env = encode(text)
        expected = hashlib.sha256(text.encode("utf-8")).hexdigest()
        assert env["checksum"] == expected

    def test_tampered_checksum_raises(self):
        env = encode("original")
        env["checksum"] = "0" * 64  # wrong checksum
        with pytest.raises(ValueError, match="checksum mismatch"):
            decode(env)


# ─── Map layer ───────────────────────────────────────────────────────────────

class TestMapLayer:
    def test_to_map_has_metadata(self):
        env = encode("hello world hello")
        m = to_map(env)
        assert "word_count" in m
        assert "unique_words" in m
        assert "word_positions" in m

    def test_word_positions_correct(self):
        env = encode("cat dog cat")
        m = to_map(env)
        assert "cat" in m["word_positions"]
        assert len(m["word_positions"]["cat"]) == 2

    def test_from_map_roundtrip(self):
        text = "from_map test"
        env = encode(text)
        m = to_map(env)
        env2 = from_map(m, env)
        assert decode(env2) == text

    def test_from_map_checksum_mismatch_raises(self):
        env = encode("a")
        m = to_map(env)
        m["source_checksum"] = "wrong"
        with pytest.raises(ValueError, match="source_checksum"):
            from_map(m, env)


# ─── Pack / Unpack ────────────────────────────────────────────────────────────

class TestPackUnpack:
    def test_pack_has_payload(self):
        env = encode("pack me")
        bundle = pack(env, label="test")
        assert bundle["payload_type"] == "fltnz"
        assert "payload" in bundle
        assert bundle["label"] == "test"

    def test_unpack_returns_envelope(self):
        env = encode("unpack me")
        bundle = pack(env)
        recovered = unpack(bundle)
        assert recovered == env

    def test_unpack_wrong_type_raises(self):
        bundle = {"payload_type": "other", "payload": {}}
        with pytest.raises(ValueError, match="payload_type"):
            unpack(bundle)


# ─── Seal / Unseal ───────────────────────────────────────────────────────────

class TestSealUnseal:
    def test_seal_has_bundle_checksum(self):
        env = encode("seal me")
        bundle = pack(env)
        trace = seal(bundle)
        assert "bundle_checksum" in trace
        assert "bundle" in trace

    def test_unseal_verifies_checksum(self):
        env = encode("verify seal")
        bundle = pack(env)
        trace = seal(bundle)
        recovered_bundle = unseal(trace)
        assert recovered_bundle == bundle

    def test_tampered_trace_raises(self):
        env = encode("tamper test")
        bundle = pack(env)
        trace = seal(bundle)
        trace["bundle"]["label"] = "tampered"
        with pytest.raises(ValueError, match="checksum mismatch"):
            unseal(trace)


# ─── Full chain ───────────────────────────────────────────────────────────────

class TestFullChain:
    @pytest.mark.parametrize("text", [
        "MRL reversible chain",
        "怎麼過去，就怎麼回來",
        "A" * 500,
    ])
    def test_text_to_trace_and_back(self, text):
        trace = text_to_trace(text, label="pytest")
        recovered = trace_to_text(trace)
        assert recovered == text

    def test_trace_has_origin_signature(self):
        trace = text_to_trace("sig test")
        assert trace["origin_signature"] == "MrLiouWord"
