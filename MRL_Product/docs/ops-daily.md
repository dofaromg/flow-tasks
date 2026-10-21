# MRL_Product_v1 每日運維流程
> origin_signature: MrLiouWord  
> 每日花 5–10 分鐘完成，不需要深度分析，只求發現異常

---

## 每日固定流程（建議早上 9:00 執行）

### Step 1：一鍵健康檢查（1 分鐘）

```bash
bash /opt/mrl_product_v1/app/scripts/daily-check.sh
```

**預期輸出：**
```
✅ mrl-app 運行中
✅ mrl-nginx 運行中
✅ Health endpoint 正常
✅ 首頁 HTTP 200
✅ App 頁 HTTP 200
✅ Session API 正常
✅ SQLite 存在
首頁訪問：XX   分析成功：XX   付款成功：X   今日營收：NT$XXX
🟢 系統正常
```

若出現 ❌ → 看 Step 1b。

---

### Step 1b：異常時檢查（問題追蹤）

```bash
# 查 app log
docker compose -f /opt/mrl_product_v1/app/deploy/docker-compose.yml logs app --tail=50

# 查 nginx log
tail -30 /opt/mrl_product_v1/logs/nginx/error.log

# 重啟（若 log 無明確錯誤）
cd /opt/mrl_product_v1/app/deploy
docker compose restart app
```

---

### Step 2：查看今日數據（2 分鐘）

```bash
bash /opt/mrl_product_v1/app/scripts/show-metrics.sh
```

**重點觀察：**
- 今日有無訪客？
- 有無分析被執行？
- 有無付款成功？
- 數字是否合理？

或直接開 admin 頁：`https://your-domain.com/admin.html`

---

### Step 3：Stripe webhook 確認（1 分鐘）

```bash
# 查看最近帳本事件
docker compose -f /opt/mrl_product_v1/app/deploy/docker-compose.yml \
  exec app sh -c "sqlite3 /app/storage/db.sqlite \
  'SELECT event_type, status, created_at FROM ledger ORDER BY created_at DESC LIMIT 5;'"
```

**正常的帳本序列（若有付款）：**
```
payment_success  | ok | 2026-...
order_paid       | ok | 2026-...
result_unlock    | ok | 2026-...
```

若 `payment_success` 有但 `result_unlock` 沒有 → 執行對帳：
```bash
curl -X POST http://localhost/admin/reconcile -H "X-Admin-Key: YOUR_ADMIN_KEY"
```

---

### Step 4：備份（2 分鐘，每日一次）

```bash
bash /opt/mrl_product_v1/app/scripts/backup.sh
```

---

## 每日判斷標準

| 狀況 | 動作 |
|------|------|
| 全部 ✅，有訪客，有分析 | 正常，繼續觀察 |
| 全部 ✅，但無訪客 | 正常，可加強導流 |
| 容器異常 | 查 log → 重啟 |
| 有付款但無解鎖 | 執行對帳 `/admin/reconcile` |
| SQLite 不存在 | 緊急！檢查 volume 掛載，從備份回復 |

---

## 自動化（可選）

```bash
# 加入 cron（每日 9:00 執行並記錄）
crontab -e

# 健康檢查 + 備份
0 9 * * * bash /opt/mrl_product_v1/app/scripts/daily-check.sh >> /opt/mrl_product_v1/logs/daily-check.log 2>&1
0 3 * * * bash /opt/mrl_product_v1/app/scripts/backup.sh >> /opt/mrl_product_v1/logs/backup.log 2>&1
```

---

*origin_signature: MrLiouWord*
