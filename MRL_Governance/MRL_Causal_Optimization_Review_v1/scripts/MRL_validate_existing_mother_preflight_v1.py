#!/usr/bin/env python3
import json, sys
from pathlib import Path

REQUIRED_CHAIN = {
    "Wake Memory",
    "Mrliou_MRL_Origin_Registry_v1",
    "Mrliou_MRL_Workspace_Node_Registry_v1",
    "MRL_CanonicalRegistry v1.0",
    "Mrliou_MRL_Authority_Registry_v1",
    "MRL_Mother_Top_Source_Layer_v1",
}
REQUIRED_REFS = {
    "origin_registry",
    "workspace_node_registry",
    "canonical_registry",
    "authority_registry",
    "top_source_layer",
    "world_model_engineering_navigation",
}
ALLOWED = {"MAP_EXISTING", "SUPPLEMENT_EXISTING", "CREATE_NEW", "QUARANTINE_EXTERNAL", "HOLD_FOR_EVIDENCE"}


def fail(msg):
    raise SystemExit(f"MRL_EXISTING_MOTHER_PREFLIGHT_FAIL: {msg}")


def main(path):
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    chain = set(data.get("required_lookup_chain", []))
    missing_chain = REQUIRED_CHAIN - chain
    if missing_chain:
        fail(f"missing lookup chain entries: {sorted(missing_chain)}")
    refs = data.get("notion_refs", {})
    missing_refs = REQUIRED_REFS - set(refs)
    if missing_refs:
        fail(f"missing notion refs: {sorted(missing_refs)}")
    if any(not str(refs[k]).startswith("https://app.notion.com/p/") for k in REQUIRED_REFS):
        fail("invalid notion ref")

    op = data.get("operation")
    if op not in ALLOWED:
        fail("invalid operation")

    existing = data.get("existing_node_found")
    if not isinstance(existing, bool):
        fail("existing_node_found must be boolean")

    if existing and op == "CREATE_NEW":
        fail("CREATE_NEW forbidden when an existing node is found")
    if not existing and op in {"MAP_EXISTING", "SUPPLEMENT_EXISTING"}:
        fail("existing-node operation requires existing_node_found=true")

    if op in {"MAP_EXISTING", "SUPPLEMENT_EXISTING"}:
        if data.get("parallel_mother_created") is not False:
            fail("existing-node operations may not create a parallel mother")
        if not data.get("existing_mother_position"):
            fail("existing-node operation requires existing_mother_position")

    if op == "CREATE_NEW":
        if data.get("create_new_requires_no_existing_node") is not True:
            fail("CREATE_NEW must require no existing node")
        if data.get("backfill_required_after_create") is not True:
            fail("backfill after create must be mandatory")

    if data.get("origin_signature") != "MrLiouWord":
        fail("origin signature mismatch")

    print(f"MRL_EXISTING_MOTHER_PREFLIGHT_PASS operation={op} existing_node_found={str(existing).lower()}")
    return 0


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("usage: MRL_validate_existing_mother_preflight_v1.py <preflight.json>")
    raise SystemExit(main(sys.argv[1]))
