#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT/backend/MRL_3D_Reconstruction_Server"
if python3 -c "import json,pathlib,sys; pkg=json.loads(pathlib.Path('package.json').read_text()); sys.exit(0 if pkg.get('dependencies') else 1)"; then
  npm install
else
  echo "NODE_PACKAGES_NONE"
fi
if [ -f "$ROOT/included/mrl3d_ai_reconstruction-1.0.0-src.zip" ]; then
  python3 -m pip install "$ROOT/included/mrl3d_ai_reconstruction-1.0.0-src.zip"
fi
echo "INSTALL PASS"
