#!/usr/bin/env python3
"""Verify the MRL APIWorks first-transaction closure package."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EXPECTED_LIST = ROOT / "EXPECTED_FILE_LIST.txt"
SCHEMA = ROOT / "schemas" / "MRL_APIWorks_Transaction_Evidence_Record_v1.schema.json"
RECORD = ROOT / "templates" / "MRL_APIWorks_Transaction_Closure_Record_v1.md"

REQUIRED_SCHEMA_TEXT = {
    "canonical_product_id": "MRL_APIWorks_BYOH_Deployment_Product_v1",
    "sku": "MRL-APIWORKS-BYOH-DEPLOY-V1",
    "origin_signature": "MrLiouWord",
    "revenue_gate": "FIRST_REALIZED_REVENUE_PASS",
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

def main() -> int:
    expected = {
        line.strip()
        for line in EXPECTED_LIST.read_text(encoding="utf-8").splitlines()
        if line.strip()
    }
    actual = source_files()
    missing = sorted(expected - actual)
    extra = sorted(actual - expected)
    empty = sorted(path for path in expected if not (ROOT / path).read_text(encoding="utf-8").strip())

    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    schema_text = json.dumps(schema, sort_keys=True)
    schema_failures = sorted(
        name for name, value in REQUIRED_SCHEMA_TEXT.items() if value not in schema_text
    )

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