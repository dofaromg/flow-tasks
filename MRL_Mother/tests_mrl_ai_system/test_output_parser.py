"""
test_output_parser.py — Smoke tests for output_parser.py
origin_signature: MrLiouWord
"""
from __future__ import annotations

import pytest

from output_parser import (
    JSONParser,
    ListParser,
    KeyValueParser,
    CodeBlockParser,
    TableParser,
    ParserChain,
)


# ─── JSONParser ───────────────────────────────────────────────────────────────

class TestJSONParser:
    def test_parses_clean_json(self):
        p = JSONParser()
        result = p.parse('{"key": "value", "num": 42}')
        assert result["ok"] is True
        assert result["data"] == {"key": "value", "num": 42}

    def test_parses_json_embedded_in_text(self):
        p = JSONParser()
        result = p.parse('Here is the data: {"status": "ok"}')
        assert result["ok"] is True
        assert result["data"]["status"] == "ok"

    def test_fails_on_non_json(self):
        p = JSONParser()
        result = p.parse("This is just plain text with no JSON at all.")
        assert result["ok"] is False


# ─── ListParser ───────────────────────────────────────────────────────────────

class TestListParser:
    def test_parses_bullet_list(self):
        p = ListParser()
        text = "- item one\n- item two\n- item three"
        result = p.parse(text)
        assert result["ok"] is True
        assert len(result["data"]) == 3

    def test_parses_numbered_list(self):
        p = ListParser()
        text = "1. first\n2. second\n3. third"
        result = p.parse(text)
        assert result["ok"] is True
        assert len(result["data"]) == 3


# ─── KeyValueParser ───────────────────────────────────────────────────────────

class TestKeyValueParser:
    def test_parses_colon_kv(self):
        p = KeyValueParser()
        text = "name: Alice\nage: 30\ncity: Taipei"
        result = p.parse(text)
        assert result["ok"] is True
        assert result["data"].get("name") == "Alice"

    def test_parses_equals_kv(self):
        p = KeyValueParser()
        text = "x=10\ny=20"
        result = p.parse(text)
        assert result["ok"] is True


# ─── CodeBlockParser ──────────────────────────────────────────────────────────

class TestCodeBlockParser:
    def test_parses_fenced_code(self):
        p = CodeBlockParser()
        text = "Here is code:\n```python\nprint('hello')\n```"
        result = p.parse(text)
        assert result["ok"] is True
        # data is a list of {language, code} dicts
        assert isinstance(result["data"], list)
        assert len(result["data"]) >= 1
        assert "print" in result["data"][0]["code"]

    def test_no_code_block_fails(self):
        p = CodeBlockParser()
        result = p.parse("No code here, just prose.")
        assert result["ok"] is False


# ─── ParserChain (auto mode) ──────────────────────────────────────────────────

class TestParserChain:
    def test_auto_detects_json(self):
        chain = ParserChain([JSONParser(), ListParser(), KeyValueParser()])
        result = chain.parse('{"answer": 42}')
        assert result["ok"] is True
        assert result["data"]["answer"] == 42

    def test_auto_falls_through_to_list(self):
        chain = ParserChain([JSONParser(), ListParser()])
        result = chain.parse("- apple\n- banana")
        assert result["ok"] is True
        assert len(result["data"]) == 2
