"""Executable MRL root-governance contracts."""
from __future__ import annotations
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]

def load(path):
    return json.loads((ROOT/path).read_text(encoding="utf-8"))

def test_no_implicit_authorization_and_explicit_owner_grant():
    doc=load("config/MRL_AUTHORIZATION_REGISTRY_v1.json")
    model=doc["authorization_model"]
    assert model["default_decision"]=="DENY"
    assert model["explicit_grant_required"] is True
    assert model["implicit_authorization_allowed"] is False
    assert model["repository_access_is_authorization"] is False
    assert model["bot_or_agent_execution_is_authorization"] is False
    assert model["silence_is_authorization"] is False
    # The owner explicitly requested restoring this workflow on 2026-10-01.
    # Empty grants were the initial state, not a ban on explicit owner grants.
    # Require exactly the recorded scope; additional grants need a new review.
    grants=doc["active_grants"]
    assert len(grants)==1
    grant=grants[0]
    assert grant["record_id"]=="MRL-STRUCTURE-INDEX-RESTORE-20261001"
    assert grant["issued_by"]=="MrLiouWord"
    assert grant["status"]=="active"
    assert grant["purpose"]=="structure-index"
    assert grant["environment"]=="github-actions"
    assert grant["grantee"]=={"actor":"dofaromg","triggering_actor":"dofaromg"}
    assert grant["scope"]=={
        "repository":"dofaromg/flow-tasks", "assets":["."], "max_depth":8,
        "destination":"github-actions-artifact:dofaromg/flow-tasks",
        "events":["push","schedule","workflow_dispatch","issue_comment"],
        "ref":"refs/heads/main",
    }
    assert grant["actions"]==["structure.scan","structure.generate","structure.upload"]
    assert grant["prohibited_actions"]==[]
    assert grant["issued_at"]=="2026-10-01T10:44:30Z"
    assert grant["expires_at"]=="2027-10-01T10:44:30Z"
    assert "2026-10-01T18:44:30+08:00" in grant["evidence_reference"]
    assert "status=revoked" in grant["rollback"]
    history=doc["operating_grant_history"][-1]
    assert history["record_id"]==grant["record_id"]
    assert history["canonical_authority"]=="Mr.liou"
    assert history["rights_transfer"]=="NOT_GRANTED"
    assert history["previous_current_status"]["reason"]=="NO_RECORDED_GRANT"

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
