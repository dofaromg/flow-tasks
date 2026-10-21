#!/usr/bin/env python3
"""
MRL_MotherModel_Snapshot_v0_1
Generate state snapshot from current registries.
"""

import sys
import os
import json
import hashlib
from datetime import datetime
from pathlib import Path

def sha256_file(filepath):
    """Compute SHA256 hash of a file."""
    sha256_hash = hashlib.sha256()
    try:
        with open(filepath, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    except Exception:
        return None

def count_lines(filepath):
    """Count lines in a file."""
    try:
        with open(filepath, "r") as f:
            return sum(1 for _ in f)
    except Exception:
        return 0

def generate_snapshot():
    """Generate a snapshot of the current mother model state."""
    base_dir = os.path.dirname(__file__)
    model_dir = os.path.join(base_dir, "..")

    timestamp = datetime.utcnow().isoformat() + "Z"

    # Collect registry data
    registries = {}
    registry_files = [
        "mother_model.json",
        "module_registry.json",
        "evidence_registry.jsonl",
        "ingest_queue.jsonl",
        "absorb_log.jsonl",
        "dependency_map.json",
        "runtime_bridge.json",
        "verification_gate.json",
        "replay_restore_hooks.json"
    ]

    for reg_file in registry_files:
        filepath = os.path.join(model_dir, reg_file)
        if os.path.exists(filepath):
            size = os.path.getsize(filepath)
            sha256 = sha256_file(filepath) or "error"
            line_count = count_lines(filepath) if reg_file.endswith(".jsonl") else None

            registries[reg_file] = {
                "file": reg_file,
                "size": size,
                "sha256": sha256
            }
            if line_count is not None:
                registries[reg_file]["line_count"] = line_count

    # Count absorbed evidence
    evidence_registry_path = os.path.join(model_dir, "evidence_registry.jsonl")
    evidence_count = count_lines(evidence_registry_path) if os.path.exists(evidence_registry_path) else 0

    # Count ingest queue
    ingest_queue_path = os.path.join(model_dir, "ingest_queue.jsonl")
    ingest_count = count_lines(ingest_queue_path) if os.path.exists(ingest_queue_path) else 0

    # Build snapshot
    snapshot = {
        "schema": "MRL_State_Snapshot_v0_1",
        "origin_signature": "MrLiouWord",
        "snapshot_timestamp": timestamp,
        "snapshot_source": "mrl_mothermodel_snapshot.py",
        "status": "INITIALIZED",
        "registries": registries,
        "system_status": {
            "mainline_nodes": 14,
            "infrastructure_modules": 12,
            "evidence_items_absorbed": evidence_count,
            "ingest_queue_pending": ingest_count,
            "overall_system_status": "INITIALIZATION" if evidence_count == 0 else "ABSORBING",
            "ready_for_absorption": True
        },
        "notes": f"Snapshot taken at {timestamp}. {evidence_count} items absorbed, {ingest_count} pending."
    }

    # Write snapshot
    snapshot_path = os.path.join(model_dir, "state_snapshot.json")
    try:
        with open(snapshot_path, "w") as f:
            json.dump(snapshot, f, indent=2)
        print(f"✓ Snapshot written: {snapshot_path}")
        print(f"  Timestamp: {timestamp}")
        print(f"  Evidence absorbed: {evidence_count}")
        print(f"  Ingest queue: {ingest_count}")
        return 0
    except Exception as e:
        print(f"✗ Failed to write snapshot: {e}")
        return 1

def main():
    result = generate_snapshot()
    sys.exit(result)

if __name__ == "__main__":
    main()
