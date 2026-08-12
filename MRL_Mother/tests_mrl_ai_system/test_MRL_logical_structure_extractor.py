"""
test_MRL_logical_structure_extractor.py — FlowAgent.Runtime 回收對齊版驗收
origin_signature: MrLiouWord
product: MRL_AI_SYSTEM
"""
from __future__ import annotations

import pytest

from MRL_LogicalStructureExtractor_v1 import MRL_LogicalStructureExtractor


@pytest.fixture
def ex():
    return MRL_LogicalStructureExtractor()


PY = '''
# This works because particle memory persists via merkle chain.
import os
from collections import defaultdict

class Foo(Bar):
    def perceive(self, world, ctx):
        """Perception is canonical; attention is historical. if ready then go."""
        return world
'''

TS = '''
import { A } from "./a";
class Widget extends Base {
  function render(props, ctx) { return props; }
}
'''


class TestPython:
    def test_extracts_class_and_function(self, ex):
        r = ex.extract_from_code(PY, "python")
        names = {f["name"] for f in r["functions"]}
        assert "Foo" in names and "perceive" in names

    def test_extracts_imports(self, ex):
        r = ex.extract_from_code(PY, "python")
        assert "os" in r["imports"] and "collections" in r["imports"]

    def test_detects_patterns_including_perception(self, ex):
        r = ex.extract_from_code(PY, "python")
        assert "perception" in r["patterns"]      # MRL canonical 主體
        assert "merkle" in r["patterns"]
        assert "particle" in r["patterns"]

    def test_causal_relation_detected(self, ex):
        r = ex.extract_from_code(PY, "python")
        assert any(rel["marker"] == "because" for rel in r["relationships"])

    def test_reasoning_chain_detected(self, ex):
        r = ex.extract_from_code(PY, "python")
        markers = {c["marker"] for c in r["reasoning_chains"]}
        assert "if" in markers or "then" in markers


class TestTypeScript:
    def test_extracts_class_with_extends(self, ex):
        r = ex.extract_from_code(TS, "typescript")
        cls = [f for f in r["functions"] if f["type"] == "class"]
        assert any(c["name"] == "Widget" and c.get("extends") == "Base" for c in cls)

    def test_extracts_ts_imports(self, ex):
        r = ex.extract_from_code(TS, "typescript")
        assert "./a" in r["imports"]


class TestAlignment:
    def test_origin_signature_stamped(self, ex):
        r = ex.extract_from_code("x=1", "python")
        assert r["origin_signature"] == "MrLiouWord"

    def test_perception_is_canonical_attention_historical(self, ex):
        # MRL 對齊:perception 與 attention 皆可偵測,但 perception 為 canonical 主體
        assert "perception" in ex.pattern_keywords
        assert "attention" in ex.pattern_keywords
