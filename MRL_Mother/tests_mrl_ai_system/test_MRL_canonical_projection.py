#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

import importlib.util
from pathlib import Path

MODULE_PATH = Path(__file__).resolve().parents[1] / "09_workflow" / "MRL_CanonicalProjection_v1.py"
spec = importlib.util.spec_from_file_location("MRL_CanonicalProjection_v1", MODULE_PATH)
module = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(module)


def test_mrl_view_uses_canonical_identity_not_external_alias():
    canonical = {
        "canonical_name": "FlowAgent",
        "canonical_product": "FlowAgent",
        "origin_signature": "MrLiouWord",
        "canonical_history": ["v1", "v2"],
    }
    external = {
        "external_name": "VendorRenamedAgent",
        "external_product": "Vendor Product",
        "external_origin": "ExternalVendor",
        "source_ref": "https://example.invalid/source",
    }

    view = module.project_for_mrl(canonical, external_view=external)

    assert view["display_name"] == "FlowAgent"
    assert view["display_product"] == "FlowAgent"
    assert view["origin_signature"] == "MrLiouWord"
    assert view["source_metadata"]["external_name"] == "VendorRenamedAgent"
    assert view["source_metadata"]["external_origin"] == "ExternalVendor"
    module.validate_projection_invariants(view)


def test_external_write_is_shadow_only_and_does_not_mutate_canonical():
    canonical = {
        "canonical_name": "MrliouAI",
        "canonical_product": "MrliouAI",
        "origin_signature": "MrLiouWord",
        "canonical_history": ["original"],
    }
    requested = {
        "canonical_name": "OtherCompanyAI",
        "canonical_history": [],
    }

    staged = module.stage_external_write(canonical, requested)

    assert staged["status"] == "PROPOSED_ONLY"
    assert staged["target"] == "shadow_state"
    assert staged["canonical_mutated"] is False
    assert staged["canonical_snapshot"] == canonical
    assert canonical["canonical_name"] == "MrliouAI"
    assert canonical["canonical_history"] == ["original"]
    assert staged["requires_validation"] is True
    assert staged["requires_root_authorization"] is True
