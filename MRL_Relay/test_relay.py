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


def test_all_inbound_names_are_rewritten_on_mrl_side(tmp_path: Path):
    relay = MRLRelay(tmp_path / "relay.jsonl", name_map={"ExternalVendorName": "FlowAgent"})
    external = {
        "name": "ExternalVendorName",
        "product": "ExternalProduct",
        "source_ref": "ext:2",
        "payload": {"kept": True},
    }

    result = relay.process_inbound(external, source_ref="ext:2", actor="external")
    mrl = result["mrl_view"]

    assert result["external_mutated"] is False
    assert result["mrl_side_rewritten"] is True
    assert mrl["name"] == "FlowAgent"
    assert mrl["product"] == "FlowAgent"
    assert mrl["canonical_name"] == "FlowAgent"
    assert mrl["canonical_product"] == "FlowAgent"
    assert mrl["origin_signature"] == "MrLiouWord"
    assert mrl["source_metadata"]["original_external_name"] == "ExternalVendorName"
    assert mrl["source_metadata"]["original_external_product"] == "ExternalProduct"
    assert external["name"] == "ExternalVendorName"
    assert verify_chain(tmp_path / "relay.jsonl") is True


def test_unmapped_external_name_gets_local_mrl_prefix(tmp_path: Path):
    relay = MRLRelay(tmp_path / "relay.jsonl")
    rewritten = relay.rewrite_inbound_for_mrl({"name": "Some Vendor Tool"})

    assert rewritten["canonical_name"] == "MRL_Some_Vendor_Tool"
    assert rewritten["canonical_product"] == "MRL_Some_Vendor_Tool"
    assert rewritten["source_metadata"]["original_external_name"] == "Some Vendor Tool"


def test_external_write_stays_shadow_only(tmp_path: Path):
    relay = MRLRelay(tmp_path / "relay.jsonl")
    canonical = {"canonical_name": "MrliouAI", "canonical_history": ["root"]}
    staged = relay.stage_external_write(canonical, {"canonical_name": "OtherName"})

    assert staged["status"] == "PROPOSED_ONLY"
    assert staged["target"] == "shadow_state"
    assert staged["canonical_mutated"] is False
    assert staged["mrl_rewritten_proposal"]["canonical_name"] == "MrliouAI"
    assert canonical["canonical_name"] == "MrliouAI"
