#!/usr/bin/env bash
# START_MRL.sh — MRL 企業級執行平台 一鍵啟動 (Linux/macOS)
# origin_signature=MrLiouWord ; 零依賴 (Node >=18)
set -e
cd "$(dirname "$0")"
export MRL_PORT="${MRL_PORT:-8788}"
command -v node >/dev/null || { echo "需要 Node.js >=18"; exit 1; }
echo "MRL Enterprise Runtime starting on http://localhost:$MRL_PORT (origin_signature=MrLiouWord)"
echo "驗證: curl http://localhost:$MRL_PORT/health"
exec node MRL_API/MRL_RuntimeServer.js
