#!/usr/bin/env python3
import json
import sys
from pathlib import Path

ERROR_IDS = {
    "E01_USER_CLAIM_STRENGTHENING",
    "E02_CAUSAL_INVERSION_OF_REACTION",
    "E03_CREATE_WITHOUT_EXISTING_MOTHER_PREFLIGHT",
    "E04_REBUILD_EXISTING_REGISTRY_AS_NEW",
    "E05_HISTORICAL_TENSE_REWRITE",
    "E06_RECENT_INCIDENT_PROMOTED_TO_ROOT_CAUSE",
    "E07_PARTIAL_EVIDENCE_PROMOTED_TO_CONFIRMED_CHAIN",
    "E08_MRL_ROOT_LAYER_DOWNRANK_OR_BYPASS",
}
GATES = {
    "G01_ACTUAL_USER_CLAIM_GATE",
    "G02_CAUSAL_ORDER_GATE",
    "G03_EXISTING_MOTHER_PREFLIGHT_GATE",
    "G04_EXISTING_VS_NEW_DECISION_GATE",
    "G05_HISTORICAL_TENSE_GATE",
    "G06_TIME_AXIS_ROOT_CAUSE_GATE",
    "G07_CLAIM_LEVEL_GATE",
    "G08_ROOT_ORIGIN_GATE",
    "G09_DELIVERY_AUDIT_GATE",
}
ALLOWED_CLAIM_LEVELS = {"FACT", "FILE_EMBEDDED_CLAIM", "INFERENCE", "UNRESOLVED", "CORRECTED"}
PRIOR_EVIDENCE_TENSE = {"RECOVERED", "RECONNECTED", "REVALIDATED", "BACKFILLED", "SUPPLEMENTED"}
EXISTING_OPS = {"MAP_EXISTING", "SUPPLEMENT_EXISTING"}


def fail(msg):
    raise SystemExit(f"MRL_CONVERSATION_ERROR_AUDIT_FAIL: {msg}")


def validate(policy, audit):
    if policy.get("origin_signature") != "MrLiouWord" or audit.get("origin_signature") != "MrLiouWord":
        fail("origin signature mismatch")

    policy_errors = set(policy.get("required_error_classes", []))
    policy_gates = set(policy.get("required_gates", []))
    if policy_errors != ERROR_IDS:
        fail("policy error-class set mismatch")
    if policy_gates != GATES:
        fail("policy gate set mismatch")

    actual_errors = audit.get("errors", [])
    actual_ids = [x.get("id") for x in actual_errors]
    if len(actual_ids) != len(ERROR_IDS) or set(actual_ids) != ERROR_IDS:
        fail(f"error coverage mismatch expected={sorted(ERROR_IDS)} actual={sorted(set(actual_ids))}")
    if any(x.get("status") != "CORRECTED" for x in actual_errors):
        fail("every enumerated error must be CORRECTED before completion")
    if any(not x.get("remediation") for x in actual_errors):
        fail("every error requires remediation")

    gates = audit.get("gates", {})
    if set(gates) != GATES:
        fail("gate coverage mismatch")
    if any(gates[g] != "PASS" for g in GATES):
        fail("all gates must PASS")

    if audit.get("root_layer_checked") is not True:
        fail("MRL root layer must be checked")
    if audit.get("mrliou_root_preserved") is not True:
        fail("MRL root layer may not be silently downranked")
    if audit.get("external_role_not_promoted_to_origin") is not True:
        fail("external role was promoted to origin without evidence")
    if audit.get("user_claims_only") is not True:
        fail("user claim was strengthened beyond the proposition under review")
    if audit.get("causal_order_preserved") is not True:
        fail("causal order not preserved")
    if audit.get("recent_incident_promoted_to_root_cause") is not False:
        fail("recent incident improperly promoted to root cause")
    if audit.get("claim_levels_valid") is not True:
        fail("claim-level classification invalid")

    if audit.get("prior_artifact_check") is not True:
        fail("prior-artifact check missing")
    if audit.get("prior_artifact_found") is True and audit.get("historical_tense") not in PRIOR_EVIDENCE_TENSE:
        fail("historical tense rewrites prior evidence as newly formed")

    existing = audit.get("existing_node_found")
    op = audit.get("operation")
    if existing is True and op not in EXISTING_OPS:
        fail("existing node requires MAP_EXISTING or SUPPLEMENT_EXISTING")
    if existing is False and op in EXISTING_OPS:
        fail("existing-node operation requires an existing node")

    delivery = audit.get("delivery_audit", {})
    if delivery.get("requested_error_count") != 8:
        fail("requested error count must be 8")
    if delivery.get("constructed_error_count") != 8:
        fail("constructed error count must be 8")
    if delivery.get("missing_error_ids") != []:
        fail("missing errors remain")
    if delivery.get("unexpected_error_ids") != []:
        fail("unexpected error IDs present")
    if delivery.get("coverage_percent") != 100:
        fail("coverage must equal 100")
    if delivery.get("completion_gate") != "PASS":
        fail("completion gate must PASS")

    levels = set(policy.get("claim_levels", []))
    if levels != ALLOWED_CLAIM_LEVELS:
        fail("claim-level vocabulary mismatch")

    print("MRL_CONVERSATION_ERROR_AUDIT_PASS errors=8 gates=9 coverage=100 root_preserved=true")
    return 0


def main(policy_path, audit_path):
    policy = json.loads(Path(policy_path).read_text(encoding="utf-8"))
    audit = json.loads(Path(audit_path).read_text(encoding="utf-8"))
    return validate(policy, audit)


if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit("usage: MRL_validate_conversation_error_audit_v1.py <policy.json> <audit.json>")
    raise SystemExit(main(sys.argv[1], sys.argv[2]))
