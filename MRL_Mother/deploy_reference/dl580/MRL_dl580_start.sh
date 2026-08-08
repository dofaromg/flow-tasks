#!/usr/bin/env bash
# MRL_DL580_DeployRunner_v1 — DL580 母體節點啟動入口 (Linux / bash)
# origin_signature=MrLiouWord
# DL580 為 MRL 內部母體自運行節點；GitHub/Cloud Code 為建構器與鏡像；APFS/Batch072 為部署/備份鏈，非母體本體。
set -euo pipefail

# repo 根目錄（deploy/dl580 的上兩層）
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MRL_HOME="${MRL_HOME:-$(cd "${SCRIPT_DIR}/../.." && pwd)}"
MRL_PORT="${MRL_PORT:-8790}"
ORIGIN_SIGNATURE="MrLiouWord"

cd "${MRL_HOME}"

echo "MRL_DL580_START"
echo "origin_signature=${ORIGIN_SIGNATURE}"
echo "mode=權位區分模式"
echo "node_role=DL580 母體自運行節點"
echo "MRL_HOME=${MRL_HOME}"
echo "MRL_PORT=${MRL_PORT}"

# 1. 部署前檢查
bash "${MRL_HOME}/scripts/MRL_dl580_deploy_check.sh"

# 2. 安裝依賴（冪等）
if [ ! -d "node_modules" ]; then
  echo "installing dependencies..."
  npm install
fi

# 3. Bootstrap
npm run MRL_boot

# 4. MCP server 對外閘口就緒(rl_13 出口即入口:DL580 母體經 MCP 對外)
#    MCP 為 stdio 協議,由 MCP 客戶端 spawn 本端點;此處寫出端點供客戶端配置。
if [ -f "${MRL_HOME}/09_workflow/MRL_MCP_Server_v1.py" ]; then
  echo "MCP server ready: python3 ${MRL_HOME}/09_workflow/MRL_MCP_Server_v1.py"
  echo "python3 ${MRL_HOME}/09_workflow/MRL_MCP_Server_v1.py" > "${MRL_HOME}/.mrl_mcp_endpoint"
fi

# 5. 啟動平台 HTTP 服務(母體自主 native /api/chat,對外營運)
if [ -f "${MRL_HOME}/MRL_Platform_Server.py" ]; then
  echo "starting MRL Platform Server on :${MRL_PORT} (母體自主 native)..."
  MRL_PORT="${MRL_PORT}" nohup python3 "${MRL_HOME}/MRL_Platform_Server.py" > "${MRL_HOME}/MRL_platform.log" 2>&1 &
  echo "  Platform PID=$! (log: MRL_platform.log)"
  sleep 2
  curl -s "http://127.0.0.1:${MRL_PORT}/health" 2>/dev/null && echo " [DL580] platform health OK" || echo " [DL580] platform starting..."
fi

# 6. 啟動 Runtime（母體 Node 節點,前景常駐）
echo "starting MRL Runtime on port ${MRL_PORT}..."
exec node MRL_RuntimeServer.js
