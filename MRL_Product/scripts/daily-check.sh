#!/bin/bash
# scripts/daily-check.sh
# origin_signature: MrLiouWord
# 每日健康檢查：確認系統存活、API 可用、DB 可寫
# 使用方式：bash /opt/mrl_product_v1/app/scripts/daily-check.sh

set -e

DOMAIN="${1:-http://localhost}"
TIMESTAMP=$(date '+%F %H:%M:%S')
PASS=0
FAIL=0
WARN=0

# 讀取 ADMIN_KEY（從 .env）
ADMIN_KEY=$(grep "^ADMIN_KEY=" /opt/mrl_product_v1/app/.env 2>/dev/null | cut -d= -f2)
[ -z "$ADMIN_KEY" ] && ADMIN_KEY=$(grep "^ADMIN_KEY=" .env 2>/dev/null | cut -d= -f2)

echo ""
echo "╔══════════════════════════════════════════════════╗"
echo "║  MRL_Product_v1 每日健康檢查                      ║"
echo "║  origin_signature: MrLiouWord                   ║"
echo "╚══════════════════════════════════════════════════╝"
echo "  時間：$TIMESTAMP"
echo "  目標：$DOMAIN"
echo ""

# ── Check helper ──────────────────────────────────────────────────
ok()   { echo "  ✅  $1"; PASS=$((PASS+1)); }
fail() { echo "  ❌  $1"; FAIL=$((FAIL+1)); }
warn() { echo "  ⚠️   $1"; WARN=$((WARN+1)); }

# ── 1. 容器狀態 ────────────────────────────────────────────────────
echo "[ 容器 ]"
if docker inspect mrl-app --format '{{.State.Status}}' 2>/dev/null | grep -q "running"; then
  ok "mrl-app 運行中"
else
  fail "mrl-app 未運行"
fi

if docker inspect mrl-nginx --format '{{.State.Status}}' 2>/dev/null | grep -q "running"; then
  ok "mrl-nginx 運行中"
else
  fail "mrl-nginx 未運行"
fi

echo ""
echo "[ API ]"

# ── 2. Health endpoint ──────────────────────────────────────────────
HEALTH=$(curl -sf "$DOMAIN/health" 2>/dev/null)
if echo "$HEALTH" | grep -q '"status":"ok"'; then
  ok "Health endpoint 正常"
else
  fail "Health endpoint 異常"
fi

# ── 3. 首頁 ──────────────────────────────────────────────────────────
HTTP=$(curl -s -o /dev/null -w "%{http_code}" "$DOMAIN/" 2>/dev/null)
if [ "$HTTP" = "200" ]; then
  ok "首頁 HTTP $HTTP"
else
  fail "首頁 HTTP $HTTP"
fi

# ── 4. App 頁 ────────────────────────────────────────────────────────
HTTP=$(curl -s -o /dev/null -w "%{http_code}" "$DOMAIN/app.html" 2>/dev/null)
if [ "$HTTP" = "200" ]; then
  ok "App 頁 HTTP $HTTP"
else
  fail "App 頁 HTTP $HTTP"
fi

# ── 5. Session API ──────────────────────────────────────────────────
SESSION=$(curl -sf -X POST "$DOMAIN/api/session" -H "Content-Type: application/json" 2>/dev/null)
if echo "$SESSION" | grep -q '"token"'; then
  ok "Session API 正常"
else
  fail "Session API 異常"
fi

echo ""
echo "[ 資料 ]"

# ── 6. SQLite 存在 ──────────────────────────────────────────────────
if [ -f "/opt/mrl_product_v1/storage/db.sqlite" ]; then
  SIZE=$(du -sh /opt/mrl_product_v1/storage/db.sqlite | cut -f1)
  ok "SQLite 存在（$SIZE）"
else
  fail "SQLite 不存在"
fi

# ── 7. Logs 可寫 ────────────────────────────────────────────────────
if [ -d "/opt/mrl_product_v1/logs/app" ]; then
  ok "App logs 目錄存在"
else
  warn "App logs 目錄不存在"
fi

# ── 8. 今日統計（若有 ADMIN_KEY）───────────────────────────────────
if [ -n "$ADMIN_KEY" ]; then
  echo ""
  echo "[ 今日數據 ]"
  METRICS=$(curl -sf "$DOMAIN/admin/metrics" -H "X-Admin-Key: $ADMIN_KEY" 2>/dev/null)
  if echo "$METRICS" | grep -q '"today"'; then
    HOME_V=$(echo "$METRICS" | python3 -c "import sys,json;d=json.load(sys.stdin);print(d['today'].get('home_views',0))" 2>/dev/null || echo "?")
    ANALYZE=$(echo "$METRICS" | python3 -c "import sys,json;d=json.load(sys.stdin);print(d['today'].get('analyzes',0))" 2>/dev/null || echo "?")
    PAYMENT=$(echo "$METRICS" | python3 -c "import sys,json;d=json.load(sys.stdin);print(d['today'].get('payments',0))" 2>/dev/null || echo "?")
    REVENUE=$(echo "$METRICS" | python3 -c "import sys,json;d=json.load(sys.stdin);print(d['today'].get('revenue_twd',0))" 2>/dev/null || echo "?")
    echo "  首頁訪問：$HOME_V"
    echo "  分析成功：$ANALYZE"
    echo "  付款成功：$PAYMENT"
    echo "  今日營收：NT\$$REVENUE"
  else
    warn "無法取得今日數據（admin key 或 API 異常）"
  fi
fi

# ── 結果 ────────────────────────────────────────────────────────────
echo ""
echo "──────────────────────────────────────────────────"
echo "  結果：✅ $PASS 通過  ❌ $FAIL 失敗  ⚠️  $WARN 警告"
echo ""

if [ "$FAIL" -gt 0 ]; then
  echo "  🔴 發現問題，請檢查："
  echo "     docker compose logs app --tail=50"
  echo ""
  exit 1
else
  echo "  🟢 系統正常。MRL_Product_v1 運行中。"
  echo "     origin_signature: MrLiouWord"
  echo ""
  exit 0
fi
