#!/bin/bash
# scripts/show-metrics.sh
# origin_signature: MrLiouWord
# 快速顯示營運 metrics：今日 + 近 7 日 + 漏斗
# 使用方式：bash /opt/mrl_product_v1/app/scripts/show-metrics.sh

DOMAIN="${1:-http://localhost}"

# 讀取 ADMIN_KEY
ADMIN_KEY=$(grep "^ADMIN_KEY=" /opt/mrl_product_v1/app/.env 2>/dev/null | cut -d= -f2)
[ -z "$ADMIN_KEY" ] && ADMIN_KEY=$(grep "^ADMIN_KEY=" .env 2>/dev/null | cut -d= -f2)

if [ -z "$ADMIN_KEY" ]; then
  echo "❌ 找不到 ADMIN_KEY，請確認 .env 存在"
  exit 1
fi

echo ""
echo "  MRL_Product_v1 · 營運數據摘要"
echo "  origin_signature: MrLiouWord"
echo "  $(date '+%F %H:%M')"
echo "  ────────────────────────────────────"

# 取 metrics
METRICS=$(curl -sf "$DOMAIN/admin/metrics" -H "X-Admin-Key: $ADMIN_KEY" 2>/dev/null)

if [ -z "$METRICS" ]; then
  echo "  ❌ 無法取得 metrics，請確認服務是否運行"
  exit 1
fi

# Python 解析（DL580 有 Python3）
python3 << PYEOF
import json, sys

data = json.loads('''$METRICS''')
t = data.get('today', {})
w = data.get('week', {})
f = data.get('funnel', {})
r = f.get('_rates', {})

print("  [ 今日 ]")
print(f"  首頁訪問   : {t.get('home_views',0)}")
print(f"  App 進入   : {t.get('app_views',0)}")
print(f"  分析成功   : {t.get('analyzes',0)}")
print(f"  付款成功   : {t.get('payments',0)}")
print(f"  結果解鎖   : {t.get('unlocks',0)}")
print(f"  今日營收   : NT\${t.get('revenue_twd',0)}")
print()
print("  [ 近 7 日 ]")
print(f"  首頁訪問   : {w.get('home_views',0)}")
print(f"  分析成功   : {w.get('analyzes',0)}")
print(f"  付款成功   : {w.get('payments',0)}")
print(f"  訂閱中     : {w.get('active_subs',0)}")
print(f"  週營收     : NT\${w.get('revenue_twd',0)}")
print()
print("  [ 漏斗轉換率（7日）]")
print(f"  首頁→App   : {r.get('home_to_app','n/a')}")
print(f"  App→分析   : {r.get('app_to_analyze','n/a')}")
print(f"  分析→付款  : {r.get('analyze_to_pay','n/a')}")
print(f"  付款→解鎖  : {r.get('pay_to_unlock','n/a')}")
print(f"  整體轉換   : {r.get('overall','n/a')}")
PYEOF

echo "  ────────────────────────────────────"
echo "  完整儀表板：$DOMAIN/admin.html"
echo ""
