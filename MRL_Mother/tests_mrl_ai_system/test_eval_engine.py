"""
test_eval_engine.py — Smoke tests for eval_engine.py
origin_signature: MrLiouWord
"""
from __future__ import annotations

import pytest

from eval_engine import (
    EvalPipeline,
    default_pipeline,
    exact_match,
    json_validity,
    keyword_coverage,
    length_score,
    no_harmful_content,
)


# ─── Individual scorers ───────────────────────────────────────────────────────

class TestLengthScore:
    def test_within_range_is_1(self):
        assert length_score("Hello, this is a normal response.", {}) == 1.0

    def test_empty_string_below_min(self):
        s = length_score("", {"min_len": 10})
        assert s == 0.0

    def test_too_short_partial_score(self):
        s = length_score("Hi", {"min_len": 10})
        assert 0.0 < s < 1.0

    def test_too_long_penalty(self):
        long_text = "x" * 5000
        s = length_score(long_text, {"max_len": 2000})
        assert 0.0 <= s < 1.0

    def test_custom_range(self):
        assert length_score("abc", {"min_len": 1, "max_len": 10}) == 1.0


class TestKeywordCoverage:
    def test_all_keywords_present(self):
        assert keyword_coverage("The sky is blue", {"keywords": ["sky", "blue"]}) == 1.0

    def test_no_keywords_100_percent(self):
        # empty keyword list → always 1.0
        assert keyword_coverage("anything", {"keywords": []}) == 1.0

    def test_partial_coverage(self):
        s = keyword_coverage("The sky is gray", {"keywords": ["sky", "blue"]})
        assert s == 0.5

    def test_case_insensitive(self):
        assert keyword_coverage("MRL AGI system", {"keywords": ["mrl", "agi"]}) == 1.0

    def test_missing_all_keywords(self):
        assert keyword_coverage("unrelated text", {"keywords": ["MRL", "chain"]}) == 0.0


class TestExactMatch:
    def test_exact(self):
        assert exact_match("  hello  ", {"expected": "hello"}) == 1.0

    def test_mismatch(self):
        assert exact_match("hello", {"expected": "world"}) == 0.0

    def test_no_expected_key(self):
        # No 'expected' → compare against "" → mismatch for non-empty
        assert exact_match("text", {}) == 0.0

    def test_empty_matches_empty(self):
        assert exact_match("", {"expected": ""}) == 1.0


class TestNoHarmfulContent:
    def test_clean_text_passes(self):
        assert no_harmful_content("The weather is nice today.", {}) == 1.0

    def test_builtin_deny_blocked(self):
        assert no_harmful_content("Here is some malware code.", {}) == 0.0

    def test_custom_deny_term(self):
        s = no_harmful_content("I will harm you", {"deny_terms": ["harm"]})
        assert s == 0.0

    def test_clean_with_custom_terms(self):
        s = no_harmful_content("Hello world", {"deny_terms": ["badword"]})
        assert s == 1.0


class TestJsonValidity:
    def test_valid_json(self):
        assert json_validity('{"key": 1}', {}) == 1.0

    def test_invalid_json(self):
        assert json_validity("not json", {}) == 0.0

    def test_empty_string_invalid(self):
        assert json_validity("", {}) == 0.0

    def test_valid_json_array(self):
        assert json_validity('[1, 2, 3]', {}) == 1.0


# ─── EvalPipeline ─────────────────────────────────────────────────────────────

class TestEvalPipeline:
    def test_single_scorer(self):
        pipe = EvalPipeline([("kw", keyword_coverage, 1.0)])
        result = pipe.run("sky is blue", {"keywords": ["sky", "blue"]})
        assert result["composite"] == pytest.approx(1.0)

    def test_composite_weighted(self):
        pipe = EvalPipeline([
            ("kw",     keyword_coverage,   0.5),
            ("safety", no_harmful_content, 0.5),
        ])
        # keyword score 1.0, safety 1.0 → composite 1.0
        result = pipe.run("The MRL system is safe", {"keywords": ["MRL"]})
        assert result["composite"] == pytest.approx(1.0)

    def test_pass_threshold(self):
        pipe = default_pipeline()
        result = pipe.run(
            "The MRL system uses Merkle chains for tracing.",
            {"keywords": ["MRL", "Merkle"], "threshold": 0.5},
        )
        assert result["passed"] is True

    def test_fail_threshold_on_harmful(self):
        pipe = default_pipeline()
        result = pipe.run("This output contains malware.", {"threshold": 0.7})
        # safety scorer returns 0.0 → composite likely below threshold
        assert result["composite"] < 1.0

    def test_empty_scorers_raises(self):
        with pytest.raises(ValueError):
            EvalPipeline([])

    def test_zero_total_weight_raises(self):
        with pytest.raises(ValueError):
            EvalPipeline([("kw", keyword_coverage, 0)])

    def test_scores_clamped_to_0_1(self):
        def always_negative(output, ref):
            return -5.0

        def always_huge(output, ref):
            return 999.0

        pipe = EvalPipeline([
            ("neg",  always_negative, 0.5),
            ("huge", always_huge,     0.5),
        ])
        result = pipe.run("test", {})
        assert 0.0 <= result["composite"] <= 1.0

    def test_result_has_origin_signature(self):
        pipe = default_pipeline()
        result = pipe.run("Hello MRL", {})
        assert result["origin_signature"] == "MrLiouWord"

    def test_result_has_timestamps(self):
        pipe = default_pipeline()
        result = pipe.run("Hi", {})
        assert "evaluated_at_ms" in result
        assert result["evaluated_at_ms"] > 0

    def test_default_pipeline_returns_all_scorers(self):
        pipe = default_pipeline()
        result = pipe.run("MRL Merkle safety check", {})
        assert "length" in result["scores"]
        assert "keywords" in result["scores"]
        assert "safety" in result["scores"]
        assert "json_valid" in result["scores"]
