#!/usr/bin/env bash
# scripts/post-deploy-verify.sh
# MRL_Product_v1 — 部署後驗收腳本
# origin_signature: MrLiouWord
# 用途：docker compose up 後，確認服務健康、DB 正常、API 可用

set -euo pipefail

HOST="${1:-localhost}"
PORT="${2:-80}"
APP_PORT="${3:-3000}"
PASS=0
FAIL=0

log_ok()   { echo "  [ OK ] $1"; PASS=$((PASS+1)); }
log_fail() { echo "  [FAIL] $1"; FAIL=$((FAIL+1)); }
log_warn() { echo "  [WARN] $1"; }
log_info() { echo "         $1"; }

check_http() {
  local desc="$1"
  local url="$2"
  local expected="${3:-200}"
  local status
  status=$(curl -s -o /dev/null -w "%{http_code}" --max-time 10 "$url" 2>/dev/null || echo "000")
  if [ "$status" = "$expected" ]; then
    log_ok "$desc (HTTP $status)"
  else
    log_fail "$desc (expected $expected, got $status) — $url"
  fi
}

echo "======================================================="
echo " MRL_Product_v1 — Post-Deploy Verification"
echo " host: $HOST  port: $PORT"
echo " origin_signature: MrLiouWord"
echo "======================================================="
echo ""

# ── 容器狀態 ────────────────────────────────────────────────────
echo "── Docker 容器狀態 ──"
for svc in mrl-app mrl-nginx; do
  STATUS=$(docker inspect --format='{{.State.Status}}' "$svc" 2>/dev/null || echo "not_found")
  HEALTH=$(docker inspect --format='{{.State.Health.Status}}' "$svc" 2>/dev/null || echo "n/a")
  if [ "$STATUS" = "running" ]; then
    log_ok "$svc running (health: $HEALTH)"
  else
    log_fail "$svc — status: $STATUS"
  fi
done

echo ""
echo "── HTTP 端點驗收 ──"

# 直接打 app port（繞過 nginx）
check_http "/health (direct app:$APP_PORT)" "http://$HOST:$APP_PORT/health" "200"

# 透過 nginx
check_http "/health (via nginx:$PORT)"      "http://$HOST:$PORT/health" "200"
check_http "/ (homepage)"                   "http://$HOST:$PORT/" "200"
check_http "/pricing.html"                  "http://$HOST:$PORT/pricing.html" "200"

# API
check_http "POST /api/session"              "http://$HOST:$PORT/api/session" "405"  # GET 會 405
check_http "GET /api/nonexistent → 404"     "http://$HOST:$PORT/api/nonexistent_endpoint_xyz" "404"

echo ""
echo "── Health Response 內容 ──"
HEALTH_BODY=$(curl -s --max-time 10 "http://$HOST:$APP_PORT/health" 2>/dev/null || echo '{}')
if echo "$HEALTH_BODY" | grep -q '"status":"ok"'; then
  log_ok "health.status = ok"
else
  log_fail "health.status 異常: $HEALTH_BODY"
fi

if echo "$HEALTH_BODY" | grep -q 'MrLiouWord'; then
  log_ok "origin_signature: MrLiouWord 存在"
else
  log_warn "origin_signature 未出現在 health response"
fi

echo ""
echo "── DB 狀態 ──"
DB_PATH="${DB_PATH:-/opt/mrl_product_v1/storage/db.sqlite}"
if [ -f "$DB_PATH" ]; then
  SIZE=$(du -sh "$DB_PATH" 2>/dev/null | cut -f1)
  log_ok "SQLite 存在 ($SIZE)"
else
  log_warn "SQLite 不在 $DB_PATH（可能在容器 volume 內）"
fi

echo ""
echo "── Log 目錄 ──"
LOG_DIR="${LOG_DIR:-/opt/mrl_product_v1/logs}"
if [ -d "$LOG_DIR" ]; then
  log_ok "logs 目錄存在: $LOG_DIR"
else
  log_warn "logs 目錄不存在: $LOG_DIR"
fi

echo ""
echo "======================================================="
echo " 結果: $PASS 通過  $FAIL 失敗"

if [ "$FAIL" -gt 0 ]; then
  echo " 狀態: ⚠ 有項目未通過，請確認"
  echo " 排查: docker compose logs -f app"
  exit 1
else
  echo " 狀態: ✓ 部署驗收通過"
fi
echo "======================================================="
