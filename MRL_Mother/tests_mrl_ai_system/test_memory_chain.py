"""
Tests for memory_chain — MerkleChain commit / verify / rollback.
"""
import json
import pathlib

import pytest

from memory_chain import MerkleChain, ChainEntry, _sha256_json


# ─── Hash helpers ─────────────────────────────────────────────────────────────

class TestHashHelpers:
    def test_sha256_json_deterministic(self):
        obj = {"a": 1, "b": [1, 2]}
        assert _sha256_json(obj) == _sha256_json(obj)

    def test_sha256_json_sort_keys(self):
        # Different key ordering must produce the same hash
        a = {"z": 1, "a": 2}
        b = {"a": 2, "z": 1}
        assert _sha256_json(a) == _sha256_json(b)

    def test_sha256_json_different_values(self):
        assert _sha256_json({"x": 1}) != _sha256_json({"x": 2})


# ─── MerkleChain ──────────────────────────────────────────────────────────────

class TestMerkleChain:
    @pytest.fixture
    def chain(self, tmp_path):
        return MerkleChain(tmp_path / "chain_data")

    def test_initial_head(self, chain):
        assert chain.head == "0" * 64

    def test_commit_returns_entry(self, chain):
        entry = chain.commit({"event": "test"})
        assert isinstance(entry, ChainEntry)

    def test_commit_head_changes(self, chain):
        initial = chain.head
        chain.commit({"event": "first"})
        assert chain.head != initial

    def test_commit_prev_links(self, chain):
        e1 = chain.commit({"n": 1})
        e2 = chain.commit({"n": 2})
        assert e2.prev == e1.merkle

    def test_commit_with_custom_id(self, chain):
        e = chain.commit({"n": 1}, entry_id="my-id")
        assert e.entry_id == "my-id"

    def test_commit_with_tags(self, chain):
        e = chain.commit({"n": 1}, tags=["important", "L7"])
        assert "important" in e.tags
        assert "L7" in e.tags

    def test_commit_with_layer(self, chain):
        e = chain.commit({"n": 1}, layer="L3")
        assert e.layer == "L3"

    def test_commit_with_meta(self, chain):
        e = chain.commit({"n": 1}, meta={"source": "test"})
        assert e.meta["source"] == "test"

    def test_read_all_empty(self, chain):
        assert chain.read_all() == []

    def test_read_all_returns_entries(self, chain):
        chain.commit({"n": 1})
        chain.commit({"n": 2})
        entries = chain.read_all()
        assert len(entries) == 2

    def test_read_all_dicts(self, chain):
        chain.commit({"n": 1})
        entries = chain.read_all()
        assert isinstance(entries[0], dict)

    def test_verify_empty_chain(self, chain):
        ok, errors = chain.verify()
        assert ok is True
        assert errors == []

    def test_verify_valid_chain(self, chain):
        chain.commit({"n": 1})
        chain.commit({"n": 2})
        chain.commit({"n": 3})
        ok, errors = chain.verify()
        assert ok is True
        assert errors == []

    def test_verify_tampered_merkle(self, chain):
        chain.commit({"n": 1})
        entries = chain.read_all()
        entries[0]["merkle"] = "tampered"
        with chain.entries_file.open("w", encoding="utf-8") as f:
            for e in entries:
                f.write(json.dumps(e) + "\n")
        ok, errors = chain.verify()
        assert ok is False
        assert len(errors) > 0

    def test_verify_tampered_prev(self, chain):
        chain.commit({"n": 1})
        chain.commit({"n": 2})
        entries = chain.read_all()
        # Sort by timestamp as verify() does
        entries.sort(key=lambda x: x["timestamp_ms"])
        # "badhash" is 7 chars; pad to 64 chars total (SHA-256 hex digest length)
        entries[1]["prev"] = "badhash" + "0" * 57
        with chain.entries_file.open("w", encoding="utf-8") as f:
            for e in entries:
                f.write(json.dumps(e) + "\n")
        ok, errors = chain.verify()
        assert ok is False

    def test_rollback_to_entry(self, chain):
        e1 = chain.commit({"n": 1})
        chain.commit({"n": 2})
        chain.commit({"n": 3})
        result = chain.rollback(e1.merkle)
        assert result is True
        entries = chain.read_all()
        assert len(entries) == 1
        assert chain.head == e1.merkle

    def test_rollback_nonexistent_returns_false(self, chain):
        chain.commit({"n": 1})
        # "nonexistent_merkle" is 18 chars; pad to 64 chars total (SHA-256 hex digest length)
        assert chain.rollback("nonexistent_merkle" + "0" * 46) is False

    def test_rollback_empty_chain_returns_false(self, chain):
        assert chain.rollback("anything") is False

    def test_persistence_across_instances(self, tmp_path):
        data_dir = tmp_path / "chain_data"
        c1 = MerkleChain(data_dir)
        e1 = c1.commit({"n": 1})
        c1.commit({"n": 2})

        c2 = MerkleChain(data_dir)
        assert c2.head == c1.head
        entries = c2.read_all()
        assert len(entries) == 2

    def test_head_file_written(self, chain):
        e = chain.commit({"n": 1})
        head_txt = chain.head_file.read_text(encoding="utf-8").strip()
        assert head_txt == e.merkle

    def test_merkle_is_deterministic(self, tmp_path):
        """Same payload + prev → same merkle hash."""
        import time
        # Build two identical merkle inputs and verify their hashes match
        obj = {
            "entry_id": "fixed-id",
            "timestamp_ms": 1000,
            "payload": {"n": 1},
            "prev": "0" * 64,
        }
        h1 = _sha256_json(obj)
        h2 = _sha256_json(obj)
        assert h1 == h2
