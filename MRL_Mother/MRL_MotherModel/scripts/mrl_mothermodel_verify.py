#!/usr/bin/env python3
"""
MRL_MotherModel_Verify_v0_1
Verify that all required files exist and are valid.
"""

import sys
import os
import json
from pathlib import Path

def verify_mother_model():
    """Verify all components of the mother model."""
    base_dir = os.path.dirname(__file__)
    model_dir = os.path.join(base_dir, "..")

    required_files = [
        "README.md",
        "mother_model.json",
        "module_registry.json",
        "dependency_map.json",
        "runtime_bridge.json",
        "verification_gate.json",
        "replay_restore_hooks.json",
        "state_snapshot.json",
        "ingest_queue.jsonl",
        "evidence_registry.jsonl",
        "absorb_log.jsonl",
        "scripts/mrl_mothermodel_ingest.py",
        "scripts/mrl_mothermodel_absorb.py",
        "scripts/mrl_mothermodel_verify.py",
        "scripts/mrl_mothermodel_snapshot.py"
    ]

    print("MRL_MotherModel_v0_1 Verification")
    print("=" * 50)

    all_valid = True
    for req_file in required_files:
        filepath = os.path.join(model_dir, req_file)
        exists = os.path.exists(filepath)
        is_nonempty = exists and os.path.getsize(filepath) > 0

        status = "✓" if exists else "✗"
        nonempty_status = "" if not exists else ("" if is_nonempty else " (empty)")

        print(f"{status} {req_file}{nonempty_status}")

        if not exists or (req_file.endswith(".json") and not is_nonempty):
            all_valid = False

    print("=" * 50)

    # Verify JSON files are parseable
    json_files = [
        "mother_model.json",
        "module_registry.json",
        "dependency_map.json",
        "runtime_bridge.json",
        "verification_gate.json",
        "replay_restore_hooks.json",
        "state_snapshot.json"
    ]

    print("\nJSON Validation:")
    for json_file in json_files:
        filepath = os.path.join(model_dir, json_file)
        try:
            with open(filepath, "r") as f:
                json.load(f)
            print(f"✓ {json_file} - valid JSON")
        except Exception as e:
            print(f"✗ {json_file} - {e}")
            all_valid = False

    print("=" * 50)
    if all_valid:
        print("✓ All verifications PASS")
        return 0
    else:
        print("✗ Some verifications FAILED")
        return 1

def main():
    result = verify_mother_model()
    sys.exit(result)

if __name__ == "__main__":
    main()
