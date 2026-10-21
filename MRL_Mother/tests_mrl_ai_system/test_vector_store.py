"""
Tests for vector_store — math helpers and VectorStore CRUD / query.
"""
import math
import pathlib

import pytest

from vector_store import VectorStore, _cosine_similarity, _dot, _norm, ORIGIN_SIGNATURE


# ─── Math helpers ─────────────────────────────────────────────────────────────

class TestMathHelpers:
    def test_dot_basic(self):
        assert _dot([1.0, 2.0, 3.0], [4.0, 5.0, 6.0]) == pytest.approx(32.0)

    def test_dot_orthogonal(self):
        assert _dot([1.0, 0.0], [0.0, 1.0]) == pytest.approx(0.0)

    def test_norm_unit(self):
        assert _norm([1.0, 0.0, 0.0]) == pytest.approx(1.0)

    def test_norm_general(self):
        assert _norm([3.0, 4.0]) == pytest.approx(5.0)

    def test_norm_zero_vector(self):
        assert _norm([0.0, 0.0]) == pytest.approx(0.0)

    def test_cosine_identical(self):
        v = [1.0, 2.0, 3.0]
        assert _cosine_similarity(v, v) == pytest.approx(1.0)

    def test_cosine_orthogonal(self):
        assert _cosine_similarity([1.0, 0.0], [0.0, 1.0]) == pytest.approx(0.0)

    def test_cosine_opposite(self):
        assert _cosine_similarity([1.0, 0.0], [-1.0, 0.0]) == pytest.approx(-1.0)

    def test_cosine_zero_vector(self):
        assert _cosine_similarity([0.0, 0.0], [1.0, 2.0]) == 0.0

    def test_cosine_both_zero(self):
        assert _cosine_similarity([0.0, 0.0], [0.0, 0.0]) == 0.0


# ─── VectorStore ─────────────────────────────────────────────────────────────

class TestVectorStore:
    @pytest.fixture
    def vs(self, tmp_path):
        store_path = tmp_path / "vs.json"
        return VectorStore(store_path=store_path)

    def test_empty_store(self, vs):
        assert len(vs) == 0
        assert vs.list_ids() == []

    def test_add_entry(self, vs):
        entry = vs.add("doc1", [0.1, 0.9, 0.3])
        assert entry["id"] == "doc1"
        assert len(vs) == 1

    def test_add_stores_floats(self, vs):
        vs.add("doc1", [1, 2, 3])
        entry = vs.get("doc1")
        assert all(isinstance(v, float) for v in entry["vector"])

    def test_add_with_meta(self, vs):
        vs.add("doc1", [0.1, 0.2], meta={"source": "readme"})
        entry = vs.get("doc1")
        assert entry["meta"]["source"] == "readme"

    def test_add_origin_signature(self, vs):
        vs.add("doc1", [0.1])
        entry = vs.get("doc1")
        assert entry["origin_signature"] == ORIGIN_SIGNATURE

    def test_add_upsert(self, vs):
        vs.add("doc1", [0.1, 0.2])
        vs.add("doc1", [0.9, 0.8])
        assert len(vs) == 1
        assert vs.get("doc1")["vector"] == [0.9, 0.8]

    def test_get_existing(self, vs):
        vs.add("doc1", [0.5])
        assert vs.get("doc1") is not None

    def test_get_missing(self, vs):
        assert vs.get("nonexistent") is None

    def test_delete_existing(self, vs):
        vs.add("doc1", [0.5])
        assert vs.delete("doc1") is True
        assert vs.get("doc1") is None
        assert len(vs) == 0

    def test_delete_missing(self, vs):
        assert vs.delete("nonexistent") is False

    def test_list_ids_sorted(self, vs):
        vs.add("z_doc", [1.0])
        vs.add("a_doc", [0.5])
        assert vs.list_ids() == ["a_doc", "z_doc"]

    def test_query_top_k(self, vs):
        vs.add("a", [1.0, 0.0])
        vs.add("b", [0.0, 1.0])
        vs.add("c", [0.7, 0.7])
        hits = vs.query([1.0, 0.0], top_k=1)
        assert len(hits) == 1
        assert hits[0][0] == "a"

    def test_query_returns_sorted_descending(self, vs):
        vs.add("high", [1.0, 0.0])
        vs.add("low", [0.0, 1.0])
        hits = vs.query([1.0, 0.0], top_k=2)
        scores = [h[1] for h in hits]
        assert scores == sorted(scores, reverse=True)

    def test_query_min_score_filter(self, vs):
        vs.add("pos", [1.0, 0.0])
        vs.add("neg", [-1.0, 0.0])
        hits = vs.query([1.0, 0.0], top_k=10, min_score=0.0)
        ids = [h[0] for h in hits]
        assert "neg" not in ids

    def test_query_empty_store(self, vs):
        assert vs.query([1.0, 0.0]) == []

    def test_query_result_structure(self, vs):
        vs.add("doc1", [1.0, 0.0], meta={"label": "test"})
        hits = vs.query([1.0, 0.0], top_k=1)
        doc_id, score, meta = hits[0]
        assert isinstance(doc_id, str)
        assert isinstance(score, float)
        assert isinstance(meta, dict)

    def test_persistence(self, tmp_path):
        store_path = tmp_path / "vs.json"
        vs1 = VectorStore(store_path=store_path)
        vs1.add("doc1", [0.1, 0.9])

        vs2 = VectorStore(store_path=store_path)
        assert vs2.get("doc1") is not None
        assert vs2.get("doc1")["vector"] == [0.1, 0.9]

    def test_persistence_delete(self, tmp_path):
        store_path = tmp_path / "vs.json"
        vs1 = VectorStore(store_path=store_path)
        vs1.add("doc1", [0.5])
        vs1.delete("doc1")

        vs2 = VectorStore(store_path=store_path)
        assert vs2.get("doc1") is None

    def test_len(self, vs):
        assert len(vs) == 0
        vs.add("a", [1.0])
        vs.add("b", [2.0])
        assert len(vs) == 2
