#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT/backend/MRL_3D_Reconstruction_Server"
export MRL_3D_BRIDGE_PORT=3050
node server.js
