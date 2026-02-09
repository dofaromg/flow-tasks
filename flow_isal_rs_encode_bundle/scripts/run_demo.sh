#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
mkdir -p "$ROOT/out"

# demo input
dd if=/dev/urandom of="$ROOT/out/input.bin" bs=1M count=8 status=none

# run wrapper
"$ROOT/bin/rswrap" \
  --in "$ROOT/out/input.bin" \
  --out "$ROOT/out" \
  --k 4 --m 2 --w 8

# merkle_root for out directory
bash "$ROOT/scripts/merkle_dir.sh" "$ROOT/out" "$ROOT/out/.merkle_root"

echo "OK. out/manifest.json out/trace.json out/.merkle_root generated"
