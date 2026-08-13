from pathlib import Path
from relay import MRLRelay, verify_chain


def test_dual_terminal_projection_and_evidence(tmp_path: Path):
    relay = MRLRelay(tmp_path / "relay.jsonl")
    external = {"name": "ExternalVendorName", "product": "ExternalProduct", "source_ref": "ext:1"}
    canonical = {
        "canonical_name": "FlowAgent",
        "canonical_product": "FlowAgent",
        "canonical_history": ["original-v1"],
        "origin_signature": "MrLiouWord",
    }

    relay.ingest_external(external, source_ref="ext:1", actor="external")
    view = relay.project_to_mrl(canonical, external)

    assert view["display_name"] == "FlowAgent"
    assert view["display_product"] == "FlowAgent"
    assert view["external_metadata"]["external_name"] == "ExternalVendorName"
    assert canonical["canonical_history"] == ["original-v1"]
    assert verify_chain(tmp_path / "relay.jsonl") is True


def test_external_write_stays_shadow_only(tmp_path: Path):
    relay = MRLRelay(tmp_path / "relay.jsonl")
    canonical = {"canonical_name": "MrliouAI", "canonical_history": ["root"]}
    staged = relay.stage_external_write(canonical, {"canonical_name": "OtherName"})

    assert staged["status"] == "PROPOSED_ONLY"
    assert staged["target"] == "shadow_state"
    assert staged["canonical_mutated"] is False
    assert canonical["canonical_name"] == "MrliouAI"
