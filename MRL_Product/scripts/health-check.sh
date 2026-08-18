#!/bin/bash
# scripts/health-check.sh
# origin_signature: MrLiouWord
# 快速驗收腳本：在 DL580 執行，驗證所有關鍵端點

set -e

DOMAIN="${1:-http://localhost}"
PASS=0
FAIL=0

check() {
  local name="$1"
  local cmd="$2"
  local expected="$3"

  result=$(eval "$cmd" 2>/dev/null)

  if echo "$result" | grep -q "$expected"; then
    echo "  ✅ $name"
    PASS=$((PASS+1))
  else
    echo "  ❌ $name → 預期包含 '$expected'，實際：$(echo "$result" | head -1)"
    FAIL=$((FAIL+1))
  fi
}

echo ""
echo "MRL_Product_v1 健康驗收"
echo "origin_signature: MrLiouWord"
echo "目標：$DOMAIN"
echo "────────────────────────────────────────"

echo ""
echo "[ 服務層 ]"
check "Docker app 容器"  "docker inspect mrl-app --format '{{.State.Status}}'" "running"
check "Docker nginx 容器" "docker inspect mrl-nginx --format '{{.State.Status}}'" "running"
check "Health endpoint"  "curl -sf $DOMAIN/health" '"status":"ok"'

echo ""
echo "[ 頁面層 ]"
check "首頁"      "curl -s -o /dev/null -w '%{http_code}' $DOMAIN/"          "200"
check "app 頁"    "curl -s -o /dev/null -w '%{http_code}' $DOMAIN/app.html"  "200"
check "pricing"   "curl -s -o /dev/null -w '%{http_code}' $DOMAIN/pricing.html" "200"
check "style.css" "curl -s -o /dev/null -w '%{http_code}' $DOMAIN/assets/style.css" "200"

echo ""
echo "[ API 層 ]"
check "Session API" \
  "curl -sf -X POST $DOMAIN/api/session -H 'Content-Type: application/json'" \
  '"token"'

echo ""
echo "[ 資料層 ]"
check "SQLite 存在" \
  "ls /opt/mrl_product_v1/storage/db.sqlite 2>/dev/null && echo found" \
  "found"
check "Logs/app 存在" \
  "ls -d /opt/mrl_product_v1/logs/app 2>/dev/null && echo found" \
  "found"
# 不依賴 sqlite3 CLI；容器本身已使用 better-sqlite3。
check "DB 已建表" \
  "docker exec mrl-app node -e \"const Database=require('better-sqlite3'); const db=new Database(process.env.DB_PATH || '/app/storage/db.sqlite'); const rows=db.prepare('SELECT name FROM sqlite_master WHERE type=\\\"table\\\"').all(); console.log(rows.map(r=>r.name).join(' ')); db.close();\"" \
  "ledger"

echo ""
echo "────────────────────────────────────────"
echo "結果：✅ $PASS 通過　❌ $FAIL 失敗"
echo ""

if [ "$FAIL" -gt 0 ]; then
  echo "請查看失敗項目，並執行："
  echo "  docker compose logs app --tail=50"
  exit 1
else
  echo "所有項目通過。MRL_Product_v1 運行正常。"
  exit 0
fi
