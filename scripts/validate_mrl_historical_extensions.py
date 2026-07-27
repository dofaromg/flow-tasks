#!/usr/bin/env python3
"""Validate the MRL historical extension registry without external dependencies."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "config" / "MRL_HISTORICAL_EXTENSION_MAP_v1.json"
AUTHORITY = ROOT / "MRL_Mother" / "00_rootlaw" / "MRL_EXTERNAL_MATERIAL_EXTENSION_MAP_v1.md"
EXTENSIONS = ROOT / "MRL_Mother" / "MRL_Extensions" / "README.md"

EXPECTED = {
    "OpenAI": "MrliouAI",
    "OpenAI API": "MrlAPI",
    "Claude": "mrlclaude",
    "Cloud": "mrlcloud",
    "MRL system identity": "MrliouAI",
    "FlowAgent": "FlowAgent",
}


def fail(message: str) -> None:
    raise SystemExit(f"MRL historical extension validation failed: {message}")


def main() -> None:
    for path in (REGISTRY, AUTHORITY, EXTENSIONS):
        if not path.is_file():
            fail(f"missing required file: {path.relative_to(ROOT)}")

    data = json.loads(REGISTRY.read_text(encoding="utf-8"))
    if data.get("origin_signature") != "MrLiouWord":
        fail("origin_signature must be MrLiouWord")

    policy = data.get("policy", {})
    required_true = (
        "external_assets_remain_external",
        "mrl_assets_must_not_be_reduced",
        "historical_lineage_preserved",
        "flowagent_is_mrl_native_product_module",
    )
    for key in required_true:
        if policy.get(key) is not True:
            fail(f"policy {key} must be true")

    mappings = {item.get("source"): item for item in data.get("mappings", [])}
    for source, extension in EXPECTED.items():
        item = mappings.get(source)
        if not item:
            fail(f"missing mapping for {source}")
        if item.get("mrl_extension") != extension:
            fail(f"{source} must extend to {extension}")
        if item.get("preserve_source_name") is not True:
            fail(f"{source} source name must be preserved")

    flowagent = mappings["FlowAgent"]
    if flowagent.get("classification") != "mrl_native_product_module":
        fail("FlowAgent classification changed")
    if flowagent.get("replace_with_mrliouai") is not False:
        fail("FlowAgent must not be replaced with MrliouAI")

    print("PASS: MRL historical extension mapping is complete and non-destructive")


if __name__ == "__main__":
    main()
