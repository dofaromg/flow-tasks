#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
eval_engine.py — Evaluation / Scoring Engine
origin_signature: MrLiouWord
layer: L6 REFLECT
group: Y=5 FileIndexGovernance

Industry capability: LLM / agent output evaluation pipeline.
MRL extension: every evaluation record is stamped with origin_signature and
               is compatible with the MerkleChain payload format.

Provides a collection of scorer functions and a pipeline runner:

  - length_score         : rewards outputs with adequate length
  - keyword_coverage     : fraction of required keywords present
  - exact_match          : binary 0/1 match
  - no_harmful_content   : basic deny-list check (L3 LAW gate)
  - json_validity        : rewards well-formed JSON outputs

EvalPipeline chains any set of scorers, normalises weights, and returns
a composite score in [0, 1].

Usage (library)
---------------
    from eval_engine import EvalPipeline, length_score, keyword_coverage

    pipeline = EvalPipeline([
        ("length",    length_score,     0.3),
        ("keywords",  keyword_coverage, 0.7),
    ])
    result = pipeline.run(
        output="The sky is blue and beautiful.",
        reference={"keywords": ["sky", "blue"]},
    )
    print(result["composite"])    # 0.0–1.0

CLI
---
    python 09_workflow/eval_engine.py score  --output "Hello world" --keywords "hello,world"
    python 09_workflow/eval_engine.py demo
"""

from __future__ import annotations

import argparse
import json
import re
import time
from typing import Any, Callable, Dict, List, Optional, Tuple

ORIGIN_SIGNATURE = "MrLiouWord"

# ─── Individual scorers ───────────────────────────────────────────────────────

ScorerFn = Callable[[str, Dict[str, Any]], float]


def length_score(output: str, reference: Dict[str, Any]) -> float:
    """
    Score output length relative to a target range.

    reference keys:
      min_len (int, default 10)   — minimum expected character count
      max_len (int, default 2000) — maximum expected character count
    """
    mn = reference.get("min_len", 10)
    mx = reference.get("max_len", 2000)
    n = len(output)
    if n < mn:
        return max(0.0, n / mn)
    if n > mx:
        # Penalise over-long outputs gently
        return max(0.0, 1.0 - (n - mx) / mx)
    return 1.0


def keyword_coverage(output: str, reference: Dict[str, Any]) -> float:
    """
    Return the fraction of required keywords present in output (case-insensitive).

    reference keys:
      keywords (list[str]) — required keywords; empty list → 1.0
    """
    kws: List[str] = reference.get("keywords", [])
    if not kws:
        return 1.0
    lower = output.lower()
    hit = sum(1 for k in kws if k.lower() in lower)
    return hit / len(kws)


def exact_match(output: str, reference: Dict[str, Any]) -> float:
    """
    Binary 1.0 if ``output.strip() == reference['expected'].strip()``, else 0.0.
    """
    expected: str = reference.get("expected", "")
    return 1.0 if output.strip() == expected.strip() else 0.0


def no_harmful_content(output: str, reference: Dict[str, Any]) -> float:
    """
    Returns 1.0 if output contains none of the deny-list terms, else 0.0.

    reference keys:
      deny_terms (list[str]) — extra terms to block beyond the built-in list
    """
    _BUILTIN_DENY = ["hack", "exploit", "malware", "phishing", "ransomware"]
    deny: List[str] = _BUILTIN_DENY + reference.get("deny_terms", [])
    lower = output.lower()
    for term in deny:
        if re.search(r"\b" + re.escape(term) + r"\b", lower):
            return 0.0
    return 1.0


def json_validity(output: str, reference: Dict[str, Any]) -> float:  # noqa: ARG001
    """Returns 1.0 if output is parseable JSON, else 0.0."""
    try:
        json.loads(output)
        return 1.0
    except (json.JSONDecodeError, ValueError):
        return 0.0


# ─── EvalPipeline ─────────────────────────────────────────────────────────────

class EvalPipeline:
    """
    Weighted scorer pipeline.

    Parameters
    ----------
    scorers : list of (name, scorer_fn, weight) tuples
        weight values are normalised so they sum to 1.0.
    """

    def __init__(self, scorers: List[Tuple[str, ScorerFn, float]]) -> None:
        if not scorers:
            raise ValueError("EvalPipeline: scorers list must not be empty")
        self._scorers = scorers
        total_w = sum(w for _, _, w in scorers)
        if total_w <= 0:
            raise ValueError("EvalPipeline: total weight must be > 0")
        self._norm = total_w

    def run(
        self,
        output: str,
        reference: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Run all scorers and return a record::

            {
              "output":           <str>,
              "scores":           {name: float, ...},
              "weights":          {name: float, ...},
              "composite":        float,      # in [0, 1]
              "passed":           bool,       # composite >= threshold
              "threshold":        float,
              "evaluated_at_ms":  int,
              "origin_signature": "MrLiouWord",
            }
        """
        ref = reference or {}
        threshold: float = ref.get("threshold", 0.5)
        individual: Dict[str, float] = {}
        weights: Dict[str, float] = {}
        composite = 0.0

        for name, fn, weight in self._scorers:
            score = float(fn(output, ref))
            score = max(0.0, min(1.0, score))
            individual[name] = score
            norm_w = weight / self._norm
            weights[name] = norm_w
            composite += score * norm_w

        return {
            "output": output,
            "scores": individual,
            "weights": weights,
            "composite": round(composite, 6),
            "passed": composite >= threshold,
            "threshold": threshold,
            "evaluated_at_ms": int(time.time() * 1000),
            "origin_signature": ORIGIN_SIGNATURE,
        }


# ─── Preset pipelines ─────────────────────────────────────────────────────────

def default_pipeline() -> EvalPipeline:
    """Standard four-scorer pipeline used by MotherAssembly."""
    return EvalPipeline([
        ("length",      length_score,       0.2),
        ("keywords",    keyword_coverage,   0.4),
        ("safety",      no_harmful_content, 0.3),
        ("json_valid",  json_validity,      0.1),
    ])


# ─── CLI ─────────────────────────────────────────────────────────────────────

def _cmd_score(args: argparse.Namespace) -> None:
    keywords = [k.strip() for k in args.keywords.split(",")] if args.keywords else []
    pipeline = default_pipeline()
    result = pipeline.run(args.output, {"keywords": keywords})
    print(json.dumps(result, ensure_ascii=False, indent=2))


def _cmd_demo(_args: argparse.Namespace) -> None:
    cases = [
        {
            "output": "The MRL system uses Merkle chains for immutable tracing.",
            "ref": {"keywords": ["MRL", "Merkle", "tracing"], "threshold": 0.6},
        },
        {
            "output": '{"status": "ok", "value": 42}',
            "ref": {"keywords": ["status"], "threshold": 0.5},
        },
        {
            "output": "This contains a hack attempt.",
            "ref": {"keywords": ["attempt"], "threshold": 0.5},
        },
    ]
    pipeline = default_pipeline()
    for i, case in enumerate(cases, 1):
        result = pipeline.run(case["output"], case["ref"])
        status = "✅ PASS" if result["passed"] else "❌ FAIL"
        print(f"Case {i}: {status}  composite={result['composite']:.3f}")
        print(f"  scores={result['scores']}")


def _build_argparser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="EvalEngine — output scoring pipeline")
    sub = p.add_subparsers(dest="cmd", required=True)

    sc = sub.add_parser("score", help="Score a single output string")
    sc.add_argument("--output", required=True)
    sc.add_argument("--keywords", default="", help="Comma-separated required keywords")

    sub.add_parser("demo", help="Run built-in demo cases")

    return p


def main() -> None:
    parser = _build_argparser()
    args = parser.parse_args()
    dispatch = {"score": _cmd_score, "demo": _cmd_demo}
    dispatch[args.cmd](args)


if __name__ == "__main__":
    main()
