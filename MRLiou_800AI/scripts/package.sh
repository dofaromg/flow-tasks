#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
./scripts/verify.sh
OUT="../MRLiou_800AI_Integrated_GitHub_Deploy_v1_0_0.zip"
rm -f "$OUT"
zip -qr "$OUT" . -x '.venv/*' '.git/*' '__pycache__/*' '*.pyc' 'runs/*' 'logs/*'
echo "$OUT"
