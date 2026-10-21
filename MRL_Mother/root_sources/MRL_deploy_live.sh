#!/bin/bash
# MRL 母體一鍵上線(在你的伺服器跑)— origin_signature: MrLiouWord
# 用法: bash MRL_deploy_live.sh [port]
set -e
PORT="${1:-8790}"
echo "[MRL] 啟動母體平台 :$PORT (零外部公司,母體自主 native 推理)"
export MRL_PORT="$PORT"
export MRL_PLATFORM_DOMAIN="${MRL_PLATFORM_DOMAIN:-mrliouword.com}"
# 背景常駐(nohup);上線後 /api/chat 即母體自主回應
nohup python3 MRL_Platform_Server.py > MRL_platform.log 2>&1 &
echo "[MRL] PID=$! 已常駐;log: MRL_platform.log"
sleep 2
curl -s "http://127.0.0.1:$PORT/health" && echo " [MRL] health OK — 已上線"
