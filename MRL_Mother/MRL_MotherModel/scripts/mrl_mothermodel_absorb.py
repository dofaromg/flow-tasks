#!/usr/bin/env python3
"""
MRL_MotherModel_Absorb_v0_1
Process queued files from ingest_queue into evidence_registry and absorb_log.
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

def absorb_queue():
    """Process all queued files into the registry."""
    base_dir = os.path.dirname(__file__)
    model_dir = os.path.join(base_dir, "..")

    queue_file = os.path.join(model_dir, "ingest_queue.jsonl")
    evidence_file = os.path.join(model_dir, "evidence_registry.jsonl")
    absorb_log_file = os.path.join(model_dir, "absorb_log.jsonl")

    if not os.path.exists(queue_file):
        print("No ingest queue found.")
        return 0

    absorbed_count = 0
    timestamp = datetime.utcnow().isoformat() + "Z"

    # Read all queued items
    queued_items = []
    try:
        with open(queue_file, "r") as f:
            for line in f:
                if line.strip():
                    queued_items.append(json.loads(line))
    except Exception as e:
        print(f"ERROR: Failed to read queue: {e}")
        return 0

    if not queued_items:
        print("Ingest queue is empty.")
        return 0

    print(f"Processing {len(queued_items)} queued items...")

    # Process each item
    for item in queued_items:
        source_path = item.get("source_path")
        if not source_path or not os.path.exists(source_path):
            print(f"✗ Source not found: {source_path}")
            continue

        # Verify SHA256
        computed_sha256 = sha256_file(source_path)
        if not computed_sha256:
            print(f"✗ Failed to compute SHA256: {source_path}")
            continue

        if computed_sha256 != item.get("sha256"):
            print(f"✗ SHA256 mismatch: {source_path}")
            continue

        # Create evidence record
        evidence_record = {
            "evidence_id": f"ABSORBED-{absorbed_count + 1:06d}",
            "absorption_timestamp": timestamp,
            "source_path": source_path,
            "size": item.get("size"),
            "sha256": computed_sha256,
            "status": "verified",
            "origin_signature": "MrLiouWord"
        }

        # Append to evidence registry
        try:
            with open(evidence_file, "a") as f:
                f.write(json.dumps(evidence_record) + "\n")
        except Exception as e:
            print(f"✗ Failed to write evidence: {e}")
            continue

        # Log absorption
        absorb_record = {
            "absorb_timestamp": timestamp,
            "evidence_id": evidence_record["evidence_id"],
            "source_path": source_path,
            "size": item.get("size"),
            "sha256": computed_sha256,
            "action": "absorbed_into_registry",
            "origin_signature": "MrLiouWord"
        }

        try:
            with open(absorb_log_file, "a") as f:
                f.write(json.dumps(absorb_record) + "\n")
        except Exception as e:
            print(f"✗ Failed to write absorb log: {e}")
            continue

        print(f"✓ Absorbed: {evidence_record['evidence_id']} ({item.get('size')} bytes)")
        absorbed_count += 1

    # Clear the queue after successful absorption
    if absorbed_count > 0:
        try:
            os.remove(queue_file)
            print(f"\nCleared ingest queue. Absorbed {absorbed_count} items.")
        except Exception as e:
            print(f"WARNING: Failed to clear queue: {e}")

    return absorbed_count

def main():
    absorbed = absorb_queue()
    sys.exit(0 if absorbed >= 0 else 1)

if __name__ == "__main__":
    main()
