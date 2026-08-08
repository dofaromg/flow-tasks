#!/usr/bin/env bash
# FlowContainer — MRL Native Runtime boot (Linux/Mac)
# origin_signature: MrLiouWord
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

python MRL_Mother/04_runtime/flowcontainer.py start \
  --config config/flowcontainer.json \
  --base-dir "$SCRIPT_DIR"
