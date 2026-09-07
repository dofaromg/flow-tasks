"""Executable MRL root-governance contracts."""
from __future__ import annotations
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]

def load(path):
    return json.loads((ROOT/path).read_text(encoding="utf-8"))

def test_no_implicit_authorization_and_no_active_grants():
    doc=load("config/MRL_AUTHORIZATION_REGISTRY_v1.json")
    model=doc["authorization_model"]
    assert model["default_decision"]=="DENY"
    assert model["explicit_grant_required"] is True
    assert model["implicit_authorization_allowed"] is False
    assert model["repository_access_is_authorization"] is False
    assert model["bot_or_agent_execution_is_authorization"] is False
    assert model["silence_is_authorization"] is False
    assert doc["active_grants"]==[]

def test_flowagent_is_native_and_immutable():
    doc=load("config/MRL_HISTORICAL_EXTENSION_MAP_v1.json")
    item=next(x for x in doc["mappings"] if x["source"]=="FlowAgent")
    assert item["classification"]=="mrl_native_product_module"
    assert item["rename_allowed"] is False
    assert item["replace_with_mrliouai"] is False

def test_destructive_migration_defaults_are_denied():
    doc=load("config/MRL_MIGRATION_CONTRACTS_v1.json")
    assert doc["default_decision"]=="DENY"
    assert doc["contract"]["global_replace_allowed"] is False
    assert doc["migrations"]==[]

def test_license_scope_is_not_inferred():
    doc=load("config/MRL_LICENSE_SCOPE_REGISTRY_v1.json")
    assert doc["whole_repository_inference_allowed"] is False
    assert doc["commercial_permission_inference_allowed"] is False

def test_rootlaw_v11_binding():
    text=(ROOT/"MRL_Mother/00_rootlaw/rootlaw.yaml").read_text(encoding="utf-8")
    assert "version: 11" in text
    assert "rl_21_classification_before_reclamation_and_explicit_authorization" in text
