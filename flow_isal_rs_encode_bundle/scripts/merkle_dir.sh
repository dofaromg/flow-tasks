#!/usr/bin/env bash
set -euo pipefail

DIR="${1:-.}"
OUT="${2:-.merkle_root}"

# deterministic file listing + sha256 fold
# (portable, no GNU-specific sort flags)
find "$DIR" -type f -print0 \
  | LC_ALL=C sort -z \
  | xargs -0 sha256sum \
  | sha256sum \
  | awk '{print $1}' > "$OUT"

echo "merkle_root=$(cat "$OUT")"
