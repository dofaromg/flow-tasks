#!/usr/bin/env python3
"""
MRL_MotherModel_Ingest_v0_1
Queue files for absorption into evidence registry.
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
    with open(filepath, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def ingest_file(filepath):
    """Ingest a single file into the queue."""
    if not os.path.exists(filepath):
        print(f"ERROR: File not found: {filepath}")
        return False

    if not os.path.isfile(filepath):
        print(f"ERROR: Not a file: {filepath}")
        return False

    try:
        stat = os.stat(filepath)
        size = stat.st_size
        sha256 = sha256_file(filepath)
        timestamp = datetime.utcnow().isoformat() + "Z"

        record = {
            "ingest_timestamp": timestamp,
            "source_path": filepath,
            "size": size,
            "sha256": sha256,
            "status": "queued",
            "origin_signature": "MrLiouWord"
        }

        queue_file = os.path.join(os.path.dirname(__file__), "..", "ingest_queue.jsonl")
        with open(queue_file, "a") as f:
            f.write(json.dumps(record) + "\n")

        print(f"✓ Queued: {filepath} ({size} bytes)")
        return True
    except Exception as e:
        print(f"ERROR: Failed to ingest {filepath}: {e}")
        return False

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 mrl_mothermodel_ingest.py <file1> [file2] [file3] ...")
        sys.exit(1)

    success_count = 0
    for filepath in sys.argv[1:]:
        if ingest_file(filepath):
            success_count += 1

    print(f"\nIngested: {success_count}/{len(sys.argv)-1} files")
    sys.exit(0 if success_count == len(sys.argv) - 1 else 1)

if __name__ == "__main__":
    main()
