from pathlib import Path
from relay import MRLRelay, verify_chain


def test_dual_terminal_projection_and_hash_evidence(tmp_path: Path):
    relay = MRLRelay(tmp_path / "relay.jsonl")
    external = {"name": "ExternalVendorName", "product": "ExternalProduct", "source_ref": "ext:1"}
    canonical = {
        "canonical_name": "FlowAgent",
        "canonical_product": "FlowAgent",
        "canonical_history": ["original-v1"],
        "origin_signature": "MrLiouWord",
    }

    evidence = relay.ingest_external(external, source_ref="ext:1", actor="external")
    view = relay.project_to_mrl(canonical, external)

    assert view["display_name"] == "FlowAgent"
    assert view["display_product"] == "FlowAgent"
    assert "external_metadata" not in view
    assert "external_name" not in view
    assert "ExternalVendorName" not in str(view)
    assert "ExternalVendorName" not in str(evidence)
    assert evidence["evidence_status"] == "HASH_ONLY"
    assert canonical["canonical_history"] == ["original-v1"]
    assert verify_chain(tmp_path / "relay.jsonl") is True


def test_all_inbound_names_are_rewritten_and_removed_on_mrl_side(tmp_path: Path):
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
    assert "external_name" not in mrl
    assert "external_product" not in mrl
    assert "source_metadata" not in mrl
    assert "ExternalVendorName" not in str(mrl)
    assert "ExternalProduct" not in str(mrl)
    assert external["name"] == "ExternalVendorName"
    assert verify_chain(tmp_path / "relay.jsonl") is True


def test_unmapped_external_name_becomes_local_mrl_identity_without_alias_retention(tmp_path: Path):
    relay = MRLRelay(tmp_path / "relay.jsonl")
    rewritten = relay.rewrite_inbound_for_mrl({"name": "Some Vendor Tool", "source_ref": "ext:3"})

    assert rewritten["canonical_name"] == "MRL_Some_Vendor_Tool"
    assert rewritten["canonical_product"] == "MRL_Some_Vendor_Tool"
    assert "Some Vendor Tool" not in str(rewritten)
    assert "external_name" not in rewritten
    assert "source_metadata" not in rewritten


def test_external_write_stays_shadow_only_without_external_name_retention(tmp_path: Path):
    relay = MRLRelay(tmp_path / "relay.jsonl")
    canonical = {"canonical_name": "MrliouAI", "canonical_history": ["root"]}
    staged = relay.stage_external_write(canonical, {"canonical_name": "OtherName"})

    assert staged["status"] == "PROPOSED_ONLY"
    assert staged["target"] == "shadow_state"
    assert staged["canonical_mutated"] is False
    assert staged["mrl_rewritten_proposal"]["canonical_name"] == "MrliouAI"
    assert "OtherName" not in str(staged["mrl_rewritten_proposal"])
    assert "proposed_write" not in staged
    assert canonical["canonical_name"] == "MrliouAI"
