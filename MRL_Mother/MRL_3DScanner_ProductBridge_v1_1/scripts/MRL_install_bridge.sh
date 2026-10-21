#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT/backend/MRL_3D_Reconstruction_Server"
npm install
if [ -f "$ROOT/included/mrl3d_ai_reconstruction-1.0.0-src.zip" ]; then
  python3 -m pip install "$ROOT/included/mrl3d_ai_reconstruction-1.0.0-src.zip"
fi
echo "INSTALL PASS"
