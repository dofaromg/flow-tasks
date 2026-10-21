#!/usr/bin/env python3
"""Verify the MRL APIWorks first-transaction closure package."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXPECTED_LIST = ROOT / "EXPECTED_FILE_LIST.txt"
SCHEMA = ROOT / "schemas" / "MRL_APIWorks_Transaction_Evidence_Record_v1.schema.json"
RECORD = ROOT / "templates" / "MRL_APIWorks_Transaction_Closure_Record_v1.md"

EXPECTED_STATES = (
    "QUOTE_PENDING",
    "ORDER_SIGNED",
    "PAYMENT_CONFIRMED",
    "DEPLOYMENT_COMPLETED",
    "CUSTOMER_ACCEPTANCE_PASS",
    "PAYOUT_RECONCILED",
    "FIRST_REALIZED_REVENUE_PASS",
)
EXPECTED_REFERENCES = (
    "order_reference",
    "payment_reference",
    "deployment_receipt_reference",
    "acceptance_reference",
    "payout_reference",
    "revenue_ledger_reference",
)
STATE_REQUIREMENTS = {
    "ORDER_SIGNED": ("order_reference",),
    "PAYMENT_CONFIRMED": ("order_reference", "payment_reference"),
    "DEPLOYMENT_COMPLETED": (
        "order_reference",
        "payment_reference",
        "deployment_receipt_reference",
    ),
    "CUSTOMER_ACCEPTANCE_PASS": (
        "order_reference",
        "payment_reference",
        "deployment_receipt_reference",
        "acceptance_reference",
    ),
    "PAYOUT_RECONCILED": EXPECTED_REFERENCES[:-1],
    "FIRST_REALIZED_REVENUE_PASS": EXPECTED_REFERENCES,
}
REQUIRED_RECORD_TEXT = {
    "same_transaction": "same transaction",
    "not_contract": "not a contract",
    "private_boundary": "authorized private system of record",
}

def source_files() -> set[str]:
    return {
        path.relative_to(ROOT).as_posix()
        for path in ROOT.rglob("*")
        if path.is_file() and "__pycache__" not in path.parts
    }


def validate_schema(schema: dict[str, object]) -> list[str]:
    """Validate the evidence schema's structure and cumulative state gates."""
    failures: list[str] = []
    properties = schema.get("properties")
    if not isinstance(properties, dict):
        return ["root.properties"]

    expected_constants = {
        "canonical_product_id": "MRL_APIWorks_BYOH_Deployment_Product_v1",
        "sku": "MRL-APIWORKS-BYOH-DEPLOY-V1",
        "origin_signature": "MrLiouWord",
    }
    for name, expected in expected_constants.items():
        definition = properties.get(name)
        if not isinstance(definition, dict) or definition.get("const") != expected:
            failures.append(f"const.{name}")

    state_definition = properties.get("transaction_state")
    if (
        not isinstance(state_definition, dict)
        or state_definition.get("enum") != list(EXPECTED_STATES)
    ):
        failures.append("transaction_state.enum")

    evidence_definition = properties.get("evidence_references")
    if not isinstance(evidence_definition, dict):
        failures.append("evidence_references")
    else:
        if evidence_definition.get("additionalProperties") is not False:
            failures.append("evidence_references.additionalProperties")
        if evidence_definition.get("required") != list(EXPECTED_REFERENCES):
            failures.append("evidence_references.required")
        reference_properties = evidence_definition.get("properties")
        if not isinstance(reference_properties, dict):
            failures.append("evidence_references.properties")
        else:
            for reference in EXPECTED_REFERENCES:
                definition = reference_properties.get(reference)
                if not isinstance(definition, dict):
                    failures.append(f"reference.{reference}")
                    continue
                if definition.get("type") != ["string", "null"] or definition.get("minLength") != 1:
                    failures.append(f"reference.{reference}.nullable_string")

    rules = schema.get("allOf")
    indexed_rules: dict[str, dict[str, object]] = {}
    if isinstance(rules, list):
        for rule in rules:
            if not isinstance(rule, dict):
                continue
            condition = rule.get("if")
            if not isinstance(condition, dict):
                continue
            condition_properties = condition.get("properties")
            if not isinstance(condition_properties, dict):
                continue
            state_condition = condition_properties.get("transaction_state")
            if isinstance(state_condition, dict) and isinstance(state_condition.get("const"), str):
                indexed_rules[state_condition["const"]] = rule

    for state, expected_references in STATE_REQUIREMENTS.items():
        rule = indexed_rules.get(state)
        if rule is None:
            failures.append(f"gate.{state}.missing")
            continue
        then = rule.get("then")
        then_properties = then.get("properties") if isinstance(then, dict) else None
        evidence = (
            then_properties.get("evidence_references")
            if isinstance(then_properties, dict)
            else None
        )
        evidence_properties = evidence.get("properties") if isinstance(evidence, dict) else None
        for reference in expected_references:
            definition = (
                evidence_properties.get(reference)
                if isinstance(evidence_properties, dict)
                else None
            )
            if (
                not isinstance(definition, dict)
                or definition.get("type") != "string"
                or definition.get("minLength") != 1
            ):
                failures.append(f"gate.{state}.{reference}")
        if state in {
            "DEPLOYMENT_COMPLETED",
            "CUSTOMER_ACCEPTANCE_PASS",
            "PAYOUT_RECONCILED",
            "FIRST_REALIZED_REVENUE_PASS",
        }:
            required = then.get("required") if isinstance(then, dict) else None
            if required != ["product_commit", "customer_bundle_sha256"]:
                failures.append(f"gate.{state}.artifact_identity")
            for field, pattern in {
                "product_commit": "^[0-9a-f]{40}$",
                "customer_bundle_sha256": "^[0-9a-f]{64}$",
            }.items():
                definition = (
                    then_properties.get(field)
                    if isinstance(then_properties, dict)
                    else None
                )
                if (
                    not isinstance(definition, dict)
                    or definition.get("type") != "string"
                    or definition.get("pattern") != pattern
                ):
                    failures.append(f"gate.{state}.{field}.non_null")

    return sorted(failures)

def main() -> int:
    expected = {
        line.strip()
        for line in EXPECTED_LIST.read_text(encoding="utf-8").splitlines()
        if line.strip()
    }
    actual = source_files()
    missing = sorted(expected - actual)
    extra = sorted(actual - expected)
    empty = sorted(
        path
        for path in expected
        if not (ROOT / path).read_text(encoding="utf-8").strip()
    )

    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    schema_failures = validate_schema(schema)

    record_text = RECORD.read_text(encoding="utf-8").lower()
    record_failures = sorted(
        name for name, value in REQUIRED_RECORD_TEXT.items() if value not in record_text
    )

    print(f"expected={len(expected)} actual={len(actual)}")
    print(f"missing={missing}")
    print(f"extra={extra}")
    print(f"empty={empty}")
    print(f"schema_failures={schema_failures}")
    print(f"record_failures={record_failures}")

    return 1 if any((missing, extra, empty, schema_failures, record_failures)) else 0

if __name__ == "__main__":
    raise SystemExit(main())
