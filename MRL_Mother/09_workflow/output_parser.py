#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
output_parser.py — Structured Output Parsers
origin_signature: MrLiouWord
layer: L7 LOOP
group: Y=3 MrLiouAIRuntime

Goal: extract structured data from free-form LLM text — zero external
      dependencies, pure Python stdlib (json, re) only.

Parsers
-------
  JSONParser       : extract the first valid JSON object/array from text
  ListParser       : extract bulleted, numbered, or dash-prefixed lists
  KeyValueParser   : extract "Key: value" or "Key = value" pairs
  CodeBlockParser  : extract fenced code blocks (```lang ... ```)
  TableParser      : extract simple markdown tables as list-of-dicts
  ParserChain      : try a sequence of parsers and return the first success

Every result is wrapped in a standard envelope stamped with origin_signature.

Result envelope
---------------
    {
      "ok":               bool,
      "parser":           str,         # parser class name
      "raw":              str,         # original input text
      "data":             any,         # parsed output (type depends on parser)
      "error":            str | None,
      "parsed_at_ms":     int,
      "origin_signature": "MrLiouWord",
    }

Usage (library)
---------------
    from output_parser import JSONParser, ListParser, ParserChain

    text = '''
    Here is the result:
    ```json
    {"answer": 42, "unit": "meaning of life"}
    ```
    '''

    result = JSONParser().parse(text)
    print(result["data"])  # {"answer": 42, "unit": "meaning of life"}

    # Try JSON first, then fall back to key-value
    chain = ParserChain([JSONParser(), KeyValueParser()])
    result = chain.parse("Name: Alice\\nAge: 30")
    print(result["data"])  # {"Name": "Alice", "Age": "30"}

CLI
---
    python 09_workflow/output_parser.py parse-json    --text '{"a":1}'
    python 09_workflow/output_parser.py parse-list    --text "- item1\\n- item2"
    python 09_workflow/output_parser.py parse-kv      --text "Key: Value"
    python 09_workflow/output_parser.py parse-code    --text '```python\\nprint(1)\\n```'
    python 09_workflow/output_parser.py parse-table   --text '| A | B |\\n|---|---|\\n| 1 | 2 |'
    python 09_workflow/output_parser.py demo
"""

from __future__ import annotations

import argparse
import json
import re
import time
from typing import Any, Dict, List, Optional

ORIGIN_SIGNATURE = "MrLiouWord"

# ─── Result builder ───────────────────────────────────────────────────────────

def _result(
    parser: str,
    raw: str,
    *,
    ok: bool,
    data: Any = None,
    error: Optional[str] = None,
) -> Dict[str, Any]:
    return {
        "ok":               ok,
        "parser":           parser,
        "raw":              raw,
        "data":             data,
        "error":            error,
        "parsed_at_ms":     int(time.time() * 1000),
        "origin_signature": ORIGIN_SIGNATURE,
    }


# ─── JSONParser ───────────────────────────────────────────────────────────────

class JSONParser:
    """
    Extract the first valid JSON object ``{...}`` or array ``[...]`` from text.

    Strategy:
      1. Try to parse the whole text directly.
      2. Scan for fenced ```json ... ``` blocks.
      3. Scan for the first ``{`` or ``[`` and attempt a greedy parse.
    """

    name = "JSONParser"

    def parse(self, text: str) -> Dict[str, Any]:
        # Strategy 1: whole text
        try:
            data = json.loads(text.strip())
            return _result(self.name, text, ok=True, data=data)
        except (json.JSONDecodeError, ValueError):
            pass

        # Strategy 2: fenced block
        fence_match = re.search(
            r"```(?:json)?\s*\n([\s\S]*?)\n```",
            text,
            re.IGNORECASE,
        )
        if fence_match:
            try:
                data = json.loads(fence_match.group(1).strip())
                return _result(self.name, text, ok=True, data=data)
            except (json.JSONDecodeError, ValueError):
                pass

        # Strategy 3: greedy bracket scan
        for start_char, end_char in [('{', '}'), ('[', ']')]:
            idx = text.find(start_char)
            if idx == -1:
                continue
            depth = 0
            in_str = False
            escape = False
            for j, ch in enumerate(text[idx:], start=idx):
                if escape:
                    escape = False
                    continue
                if ch == '\\' and in_str:
                    escape = True
                    continue
                if ch == '"':
                    in_str = not in_str
                    continue
                if in_str:
                    continue
                if ch == start_char:
                    depth += 1
                elif ch == end_char:
                    depth -= 1
                    if depth == 0:
                        candidate = text[idx:j + 1]
                        try:
                            data = json.loads(candidate)
                            return _result(self.name, text, ok=True, data=data)
                        except (json.JSONDecodeError, ValueError):
                            break

        return _result(self.name, text, ok=False, error="No valid JSON found")


# ─── ListParser ───────────────────────────────────────────────────────────────

class ListParser:
    """
    Extract bulleted (- / * / •), numbered (1. / 1)), or dash-prefixed lists.

    Returns a list of stripped string items.
    """

    name = "ListParser"

    # Matches "- text", "* text", "• text", "1. text", "1) text"
    _ITEM_RE = re.compile(
        r"^[ \t]*(?:[-*•]|\d+[.):])\s+(.+)",
        re.MULTILINE,
    )

    def parse(self, text: str) -> Dict[str, Any]:
        matches = self._ITEM_RE.findall(text)
        items = [m.strip() for m in matches if m.strip()]
        if items:
            return _result(self.name, text, ok=True, data=items)
        return _result(self.name, text, ok=False, error="No list items found")


# ─── KeyValueParser ───────────────────────────────────────────────────────────

class KeyValueParser:
    """
    Extract ``Key: Value``, ``Key = Value``, or ``Key — Value`` pairs.

    Returns a dict mapping stripped keys to stripped values.
    Keys must be non-empty strings without special characters.
    """

    name = "KeyValueParser"

    _KV_RE = re.compile(
        r"^[ \t]*([\w\s\u4e00-\u9fff\-_()（）]{1,60})[ \t]*[:=—–\-]{1,2}[ \t]*(.+)",
        re.MULTILINE,
    )

    def parse(self, text: str) -> Dict[str, Any]:
        pairs: Dict[str, str] = {}
        for key, val in self._KV_RE.findall(text):
            k = key.strip()
            v = val.strip()
            if k and v:
                pairs[k] = v
        if pairs:
            return _result(self.name, text, ok=True, data=pairs)
        return _result(self.name, text, ok=False, error="No key-value pairs found")


# ─── CodeBlockParser ──────────────────────────────────────────────────────────

class CodeBlockParser:
    """
    Extract all fenced code blocks ````` ```lang\\n...\\n``` ```.

    Returns a list of dicts::

        [{"language": str, "code": str}, ...]
    """

    name = "CodeBlockParser"

    _FENCE_RE = re.compile(
        r"```(\w*)\s*\n([\s\S]*?)\n```",
        re.IGNORECASE,
    )

    def parse(self, text: str) -> Dict[str, Any]:
        blocks = []
        for m in self._FENCE_RE.finditer(text):
            lang = m.group(1).strip() or "text"
            code = m.group(2)
            blocks.append({"language": lang, "code": code})
        if blocks:
            return _result(self.name, text, ok=True, data=blocks)
        return _result(self.name, text, ok=False, error="No code blocks found")


# ─── TableParser ──────────────────────────────────────────────────────────────

class TableParser:
    """
    Extract a simple GitHub-Flavored Markdown table.

    Returns a list of dicts where keys are the column headers.
    Only the first table found is returned.
    """

    name = "TableParser"

    _ROW_RE = re.compile(r"\|(.+)\|")
    _SEP_RE = re.compile(r"^\|[-:| ]+\|$")

    def parse(self, text: str) -> Dict[str, Any]:
        lines = text.splitlines()
        table_lines: List[str] = []
        in_table = False

        for line in lines:
            stripped = line.strip()
            if self._ROW_RE.match(stripped):
                table_lines.append(stripped)
                in_table = True
            elif in_table:
                break  # end of table

        if len(table_lines) < 2:
            return _result(self.name, text, ok=False, error="No markdown table found")

        # Row 0: headers; Row 1: separator (skip); Rows 2+: data
        headers = [h.strip() for h in table_lines[0].strip("|").split("|")]

        rows: List[Dict[str, str]] = []
        for row_line in table_lines[2:]:
            if self._SEP_RE.match(row_line):
                continue
            cells = [c.strip() for c in row_line.strip("|").split("|")]
            row_dict = {headers[i]: cells[i] if i < len(cells) else ""
                        for i in range(len(headers))}
            rows.append(row_dict)

        if rows:
            return _result(self.name, text, ok=True, data=rows)
        return _result(self.name, text, ok=False, error="Table has no data rows")


# ─── ParserChain ──────────────────────────────────────────────────────────────

class ParserChain:
    """
    Try parsers in sequence; return the first successful result.

    Parameters
    ----------
    parsers : list
        Ordered list of parser instances to try.
    """

    name = "ParserChain"

    def __init__(self, parsers: List[Any]) -> None:
        if not parsers:
            raise ValueError("ParserChain: parsers list must not be empty")
        self._parsers = parsers

    def parse(self, text: str) -> Dict[str, Any]:
        errors: List[str] = []
        for parser in self._parsers:
            result = parser.parse(text)
            if result["ok"]:
                result["parser"] = f"ParserChain→{result['parser']}"
                return result
            errors.append(f"{parser.name}: {result.get('error','failed')}")

        return _result(
            self.name,
            text,
            ok=False,
            error="; ".join(errors),
        )


# ─── CLI ─────────────────────────────────────────────────────────────────────

def _print_result(result: Dict[str, Any]) -> None:
    status = "✅ OK" if result["ok"] else "❌ FAIL"
    print(f"{status}  parser={result['parser']}")
    if result["ok"]:
        print(json.dumps(result["data"], ensure_ascii=False, indent=2, default=str))
    else:
        print(f"  error: {result['error']}")


def _cmd_parse_json(args: argparse.Namespace) -> None:
    _print_result(JSONParser().parse(args.text))


def _cmd_parse_list(args: argparse.Namespace) -> None:
    _print_result(ListParser().parse(args.text))


def _cmd_parse_kv(args: argparse.Namespace) -> None:
    _print_result(KeyValueParser().parse(args.text))


def _cmd_parse_code(args: argparse.Namespace) -> None:
    _print_result(CodeBlockParser().parse(args.text))


def _cmd_parse_table(args: argparse.Namespace) -> None:
    _print_result(TableParser().parse(args.text))


def _cmd_demo(_args: argparse.Namespace) -> None:
    samples = [
        ("JSONParser",      JSONParser(),      '{"name":"MRL","version":"1.0"}'),
        ("JSONParser fence",JSONParser(),      '```json\n{"ok":true}\n```'),
        ("ListParser",      ListParser(),      "- Alpha\n- Beta\n1. Gamma"),
        ("KeyValueParser",  KeyValueParser(),  "Name: MrLiouAI\nLayer: L7\nVersion: 2"),
        ("CodeBlockParser", CodeBlockParser(), "```python\nprint('hello')\n```"),
        ("TableParser",     TableParser(),
         "| A | B |\n|---|---|\n| 1 | 2 |\n| 3 | 4 |"),
        ("ParserChain",
         ParserChain([JSONParser(), KeyValueParser(), ListParser()]),
         "Status: OK\nScore: 0.95"),
    ]
    for label, parser, text in samples:
        result = parser.parse(text)
        status = "✅" if result["ok"] else "❌"
        print(f"{status} {label}")
        if result["ok"]:
            preview = json.dumps(result["data"], ensure_ascii=False)[:80]
            print(f"   {preview}")
        else:
            print(f"   error: {result['error']}")


def _build_argparser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="OutputParser — structured output extractors")
    sub = p.add_subparsers(dest="cmd", required=True)

    for cmd_name in ("parse-json", "parse-list", "parse-kv", "parse-code", "parse-table"):
        sp = sub.add_parser(cmd_name)
        sp.add_argument("--text", required=True)

    sub.add_parser("demo", help="Run built-in demo cases")

    return p


def main() -> None:
    parser = _build_argparser()
    args = parser.parse_args()
    dispatch = {
        "parse-json":  _cmd_parse_json,
        "parse-list":  _cmd_parse_list,
        "parse-kv":    _cmd_parse_kv,
        "parse-code":  _cmd_parse_code,
        "parse-table": _cmd_parse_table,
        "demo":        _cmd_demo,
    }
    dispatch[args.cmd](args)


if __name__ == "__main__":
    main()
