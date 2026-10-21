# MRL_Product_v1 維運手冊
> origin_signature: MrLiouWord

---

## 日常維運

### 查看系統狀態
```bash
cd /opt/mrl_product_v1/app/deploy

# 容器狀態
docker compose ps

# 即時 log
docker compose logs -f app

# 資源使用
docker stats mrl-app mrl-nginx
```

### 查看帳本（最近 20 筆）
```bash
docker compose exec app sh -c \
  "sqlite3 /app/storage/db.sqlite 'SELECT event_type, order_id, amount, created_at FROM ledger ORDER BY created_at DESC LIMIT 20;'"
```

### 查看訂單
```bash
docker compose exec app sh -c \
  "sqlite3 /app/storage/db.sqlite 'SELECT id, plan_type, amount, status, created_at FROM orders ORDER BY created_at DESC LIMIT 20;'"
```

### 查看付款
```bash
docker compose exec app sh -c \
  "sqlite3 /app/storage/db.sqlite 'SELECT id, order_id, provider_tx_id, amount, status FROM payments ORDER BY created_at DESC LIMIT 20;'"
```

---

## 備份

### 手動備份 SQLite
```bash
# 備份到 backups 目錄（含時間戳）
cp /opt/mrl_product_v1/storage/db.sqlite \
   /opt/mrl_product_v1/backups/db-$(date +%F-%H%M%S).sqlite

echo "備份完成："
ls -lh /opt/mrl_product_v1/backups/
```

### 定期自動備份（cron）
```bash
# 編輯 crontab
crontab -e

# 每天凌晨 3 點備份
0 3 * * * cp /opt/mrl_product_v1/storage/db.sqlite /opt/mrl_product_v1/backups/db-$(date +\%F-\%H\%M\%S).sqlite

# 保留最近 30 份（避免占滿磁碟）
30 3 * * * find /opt/mrl_product_v1/backups/ -name "db-*.sqlite" -mtime +30 -delete
```

---

## 回復

### 從備份回復 SQLite
```bash
# 停止 app（讓 SQLite 乾淨關閉）
cd /opt/mrl_product_v1/app/deploy
docker compose stop app

# 確認備份檔案
ls -lh /opt/mrl_product_v1/backups/

# 替換 db（例如回復到昨天的備份）
cp /opt/mrl_product_v1/backups/db-2026-03-23-030000.sqlite \
   /opt/mrl_product_v1/storage/db.sqlite

# 重新啟動
docker compose start app

# 確認正常
docker compose logs app --tail=20
```

---

## Stripe Webhook 測試

### 用 Stripe CLI 本地測試
```bash
# 安裝 stripe CLI
# https://stripe.com/docs/stripe-cli

# 登入
stripe login

# 轉發 webhook 到本地（測試用）
stripe listen --forward-to localhost:3000/webhook/stripe

# 觸發測試事件
stripe trigger checkout.session.completed
```

### 確認 webhook 到帳本流程
```bash
# 1. 觸發事件後，查看帳本是否寫入
docker compose exec app sh -c \
  "sqlite3 /app/storage/db.sqlite \
   'SELECT event_type, status, created_at FROM ledger ORDER BY created_at DESC LIMIT 5;'"

# 預期看到：
# payment_success|ok|2026-...
# order_paid|ok|2026-...
# result_unlock|ok|2026-...
```

---

## 對帳（Reconciliation）

若有付款成功但未解鎖的異常訂單：

```bash
curl -X POST http://localhost/admin/reconcile \
  -H "X-Admin-Key: YOUR_ADMIN_KEY" \
  | python3 -m json.tool
```

---

## 更新 .env

```bash
# 編輯 .env
nano /opt/mrl_product_v1/app/.env

# 重啟 app 讓新設定生效
cd /opt/mrl_product_v1/app/deploy
docker compose restart app
```

---

## 常見問題

### App 啟動失敗
```bash
docker compose logs app --tail=50
# 找 [ERROR] 或 Error 字樣
```

常見原因：
- `.env` 未填完整（缺 `ANTHROPIC_API_KEY` 或 `STRIPE_SECRET_KEY`）
- `DB_PATH` 對應目錄不存在
- Port 3000 被佔用

### Stripe Webhook 驗證失敗
```
Webhook Error: No signatures found matching the expected signature
```
原因：`STRIPE_WEBHOOK_SECRET` 填錯，或用了測試 secret 接正式 webhook。

### SQLite 資料庫鎖定
若同時有多個操作造成 `SQLITE_BUSY`，重啟 app：
```bash
docker compose restart app
```

---

*origin_signature: MrLiouWord*
