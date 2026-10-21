#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
PY="python3"; [[ -x .venv/bin/python ]] && PY=.venv/bin/python
$PY -m unittest discover -s tests -v
$PY -m mrliou_800ai.cli health >/dev/null
$PY examples/make_cfd_mass_sample.py >/dev/null
rm -rf runs/verify_mass && $PY -m mrliou_800ai.cli mass-audit --data examples/cfd_mass_sample.npz --out runs/verify_mass >/dev/null
test -s runs/verify_mass/mass_audit.json
test -s manifest/checksums.txt
if grep -RInE 'TODO_IMPLEMENT|PLACEHOLDER_ONLY|class [A-Za-z_]+: \.\.\.' src; then echo 'Placeholder detected'; exit 1; fi
echo DELIVERY_PASS
