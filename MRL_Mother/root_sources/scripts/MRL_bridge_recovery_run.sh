#!/usr/bin/env bash
# MRL_bridge_recovery_run.sh — DL580 bridge 復原一次打完腳本
# origin_signature: MrLiouWord
#
# 用途：雲端 session 網路白名單放行 mrliouword.com 之後，一次執行：
#   Phase 0：bridge 連通性驗證（/health）
#   Phase 1：7700 ASI Engine（app\server.js）診斷 — netstat / tasklist / log
#   Phase 2：重啟 7700，驗證 http://127.0.0.1:7700/health
#   Phase 3：bridge key 輪替（作廢已在對話中曝光的舊 key）
#   Phase 4：官網（mrliouword.com）端點 / OAuth session 驗證
#
# 用法：
#   export MRL_BRIDGE_KEY=<目前有效的 bridge key>   # 不得硬碼在檔案內
#   bash scripts/MRL_bridge_recovery_run.sh all      # 或指定單一 phase: 0|1|2|3|4
#
# 可選環境變數（Phase 1 的診斷輸出會告訴你該填什麼）：
#   MRL_7700_TASK     — 7700 的 schtasks 工作名稱（若已註冊開機自啟）
#   MRL_7700_HOME     — 7700 app 的工作目錄（例 D:\mrl\asi），用 node app\server.js 直啟
#   MRL_BRIDGE_TASK   — bridge 服務的 schtasks 工作名稱（key 輪替後重啟用）
#   MRL_BRIDGE_CONFIG — bridge 設定檔在 DL580 上的絕對路徑（Phase 3 key 輪替必要）
#   MRL_TIMEOUT       — 每個指令的 curl timeout 秒數（預設 60）
#
# 約定（CLAUDE.md）：實跑過才算 PASS；本腳本每一步都印出實際回應，不預設成功。

set -u

BRIDGE="https://bridge.mrliouword.com"
SITE="https://mrliouword.com"
TIMEOUT="${MRL_TIMEOUT:-60}"
PHASE="${1:-all}"

hr() { printf '\n===== %s =====\n' "$*"; }

need_key() {
  if [ -z "${MRL_BRIDGE_KEY:-}" ]; then
    echo "[FAIL] 未設 MRL_BRIDGE_KEY — key 一律走環境變數，不得硬碼。" >&2
    exit 1
  fi
}

# 經 bridge 在 DL580 上執行指令（cmd 內容 URL-encode 後帶入 MRL_run）
mrl_run() {
  local cmd="$1"
  echo "--- DL580> ${cmd}"
  curl -sS --max-time "${TIMEOUT}" --get "${BRIDGE}/MRL_run" \
    --data-urlencode "key=${MRL_BRIDGE_KEY}" \
    --data-urlencode "cmd=${cmd}"
  local rc=$?
  echo
  return $rc
}

phase0() {
  hr "Phase 0：bridge 連通性"
  echo "--- GET ${BRIDGE}/health"
  curl -sSf --max-time "${TIMEOUT}" "${BRIDGE}/health" || {
    echo "[FAIL] bridge 連不到 — 若是 CONNECT tunnel 403，代表雲端網路白名單尚未放行 mrliouword.com。" >&2
    echo "       放行步驟見 deploy/dl580/MRL_network_whitelist_recovery_v1.md" >&2
    exit 2
  }
  echo
  need_key
  mrl_run "echo PING"
}

phase1() {
  hr "Phase 1：7700 ASI Engine 診斷"
  need_key
  # 1a. 埠有沒有人聽、是哪個 PID
  mrl_run "netstat -ano | findstr :7700"
  # 1b. node 行程與完整命令列（找出 app\\server.js 是誰、從哪個目錄跑）
  mrl_run "wmic process where \"name='node.exe'\" get ProcessId,CommandLine"
  # 1c. 已註冊的 MRL 相關 schtasks（供 MRL_7700_TASK / MRL_BRIDGE_TASK 取名）
  mrl_run "schtasks /query /fo LIST | findstr /i \"TaskName mrl asi bridge\""
  # 1d. 本機 health 實測（分辨「行程死了」vs「行程活著但 health 紅」）
  mrl_run "curl.exe -s -m 5 http://127.0.0.1:7700/health"
  # 1e. log 尾巴（目錄以 Phase 1b 查到的工作目錄為準；先試常見位置）
  mrl_run "powershell -NoProfile -Command \"Get-ChildItem -Path D:\\mrl -Recurse -Filter *.log -ErrorAction SilentlyContinue | Sort-Object LastWriteTime -Descending | Select-Object -First 5 FullName,LastWriteTime | Format-List\""
  echo "[NOTE] 依 1b/1c 的輸出設定 MRL_7700_TASK 或 MRL_7700_HOME 後再跑 Phase 2。"
}

phase2() {
  hr "Phase 2：重啟 7700 並驗證"
  need_key
  if [ -n "${MRL_7700_TASK:-}" ]; then
    mrl_run "schtasks /end /tn \"${MRL_7700_TASK}\""
    mrl_run "schtasks /run /tn \"${MRL_7700_TASK}\""
  elif [ -n "${MRL_7700_HOME:-}" ]; then
    # 先收掉佔著 7700 的舊行程（只殺該埠 PID，不動其他 node）
    mrl_run "for /f \"tokens=5\" %p in ('netstat -ano ^| findstr :7700 ^| findstr LISTENING') do taskkill /PID %p /F"
    mrl_run "powershell -NoProfile -Command \"Start-Process node -ArgumentList 'app\\server.js' -WorkingDirectory '${MRL_7700_HOME}' -WindowStyle Hidden\""
  else
    echo "[SKIP] 未設 MRL_7700_TASK 或 MRL_7700_HOME — 先跑 Phase 1 取得後再來。"
    return 0
  fi
  # 給服務幾秒起來再驗
  mrl_run "powershell -NoProfile -Command \"Start-Sleep -Seconds 5\""
  mrl_run "curl.exe -s -m 5 http://127.0.0.1:7700/health"
  echo "[NOTE] 上面 health 有 ok/status 才算 PASS（實機）；沒有就回 Phase 1 看 log。"
}

phase3() {
  hr "Phase 3：bridge key 輪替（作廢舊 key）"
  need_key
  NEW_KEY="$(openssl rand -hex 24)"
  echo "[NEW KEY] ${NEW_KEY}"
  echo "          ↑ 立刻抄下存到安全處（密碼管理器）；本腳本不落地保存。"
  if [ -n "${MRL_BRIDGE_CONFIG:-}" ]; then
    # 在 DL580 上把設定檔中的舊 key 換成新 key（舊 key 值 = 目前的 MRL_BRIDGE_KEY）
    mrl_run "powershell -NoProfile -Command \"(Get-Content '${MRL_BRIDGE_CONFIG}' -Raw) -replace [regex]::Escape('${MRL_BRIDGE_KEY}'), '${NEW_KEY}' | Set-Content '${MRL_BRIDGE_CONFIG}'\""
    if [ -n "${MRL_BRIDGE_TASK:-}" ]; then
      mrl_run "schtasks /end /tn \"${MRL_BRIDGE_TASK}\""
      mrl_run "schtasks /run /tn \"${MRL_BRIDGE_TASK}\""
      sleep 5
    else
      echo "[NOTE] 未設 MRL_BRIDGE_TASK — 請手動重啟 bridge 服務讓新 key 生效。"
    fi
    echo "--- 驗證：舊 key 應被拒絕"
    OLD_STATUS=$(curl -sS -o /dev/null -w '%{http_code}' --max-time "${TIMEOUT}" --get "${BRIDGE}/MRL_run" \
      --data-urlencode "key=${MRL_BRIDGE_KEY}" --data-urlencode "cmd=echo OLDKEY")
    echo "    舊 key HTTP status: ${OLD_STATUS}"
    if [ "${OLD_STATUS}" -lt 400 ] 2>/dev/null; then
      echo "[FAIL] 舊 key 仍被接受（HTTP ${OLD_STATUS}）— 輪替失敗，請確認 bridge 是否已重啟。" >&2
      exit 3
    fi
    echo "--- 驗證：新 key 應可用"
    NEW_STATUS=$(curl -sS -o /dev/null -w '%{http_code}' --max-time "${TIMEOUT}" --get "${BRIDGE}/MRL_run" \
      --data-urlencode "key=${NEW_KEY}" --data-urlencode "cmd=echo NEWKEY")
    echo "    新 key HTTP status: ${NEW_STATUS}"
    if [ "${NEW_STATUS}" -ge 400 ] 2>/dev/null; then
      echo "[FAIL] 新 key 被拒（HTTP ${NEW_STATUS}）— 請確認設定檔更新是否成功。" >&2
      exit 3
    fi
    echo "[PASS] 舊 key 被拒（HTTP ${OLD_STATUS}）+ 新 key 可用（HTTP ${NEW_STATUS}）— 輪替 PASS。之後 export MRL_BRIDGE_KEY=${NEW_KEY}。"
  else
    echo "[SKIP] 未設 MRL_BRIDGE_CONFIG（bridge 設定檔在 DL580 上的路徑）。"
    echo "       先用 Phase 1b 的 node 命令列找出 bridge server 讀 key 的位置，再："
    echo "       export MRL_BRIDGE_CONFIG='D:\\...\\<bridge設定檔>' && bash $0 3"
  fi
}

phase4() {
  hr "Phase 4：官網端點 / OAuth session 驗證"
  echo "--- GET ${SITE}/health（Worker 邊緣，不需 DL580）"
  curl -sS --max-time "${TIMEOUT}" "${SITE}/health"; echo
  echo "--- GET ${SITE}/mrl/state"
  curl -sS --max-time "${TIMEOUT}" "${SITE}/mrl/state"; echo
  echo "--- GET ${SITE}/api/mother/status（轉發 DL580，需 MRL_DL580_ORIGIN 已設）"
  curl -sS --max-time "${TIMEOUT}" "${SITE}/api/mother/status"; echo
  echo "--- 登入端點狀態碼（magic-link / OAuth）"
  for p in /login /auth/login /api/auth/session; do
    code=$(curl -sS -o /dev/null -w '%{http_code}' --max-time "${TIMEOUT}" "${SITE}${p}")
    echo "    ${SITE}${p} -> HTTP ${code}"
  done
  echo "[NOTE] session 驗證需帶真使用者 cookie，最終以瀏覽器實登為準（實機驗收）。"
}

case "${PHASE}" in
  0) phase0 ;;
  1) phase0; phase1 ;;
  2) phase0; phase2 ;;
  3) phase0; phase3 ;;
  4) phase4 ;;
  all) phase0; phase1; phase2; phase3; phase4 ;;
  *) echo "用法: $0 [0|1|2|3|4|all]" >&2; exit 1 ;;
esac

hr "完成 — 依 CLAUDE.md 約定：以上輸出為當下狀態，實跑通過才可標 PASS（實機）。"
