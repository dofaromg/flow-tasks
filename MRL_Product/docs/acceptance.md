# MRL_Product_v1 驗收標準
> origin_signature: MrLiouWord  
> gateway: MRL_World_Gateway_v1

---

## A. 部署驗收

| 項目 | 驗收指令 | 通過標準 |
|------|---------|---------|
| 容器啟動 | `docker compose ps` | `app` 和 `nginx` 均顯示 `Up` |
| 健康檢查 | `curl http://localhost/health` | `{"status":"ok",...}` |
| DB 存在 | `ls /opt/mrl_product_v1/storage/db.sqlite` | 檔案存在，大小 > 0 |
| Logs 可寫 | `ls /opt/mrl_product_v1/logs/app/` | 目錄存在，有 log 檔 |
| Nginx 代理 | `curl -I http://localhost/` | HTTP 200 |
| Volume 掛載 | `docker inspect mrl-app` | 確認 `/app/storage` 掛到 host |

---

## B. 功能驗收

### B1 首頁與靜態頁面
```bash
DOMAIN=http://localhost

curl -s -o /dev/null -w "首頁: %{http_code}\n"    $DOMAIN/
curl -s -o /dev/null -w "app:  %{http_code}\n"    $DOMAIN/app.html
curl -s -o /dev/null -w "pricing: %{http_code}\n" $DOMAIN/pricing.html
curl -s -o /dev/null -w "CSS: %{http_code}\n"     $DOMAIN/assets/style.css
```

**通過標準：** 全部回傳 200

---

### B2 Session 建立
```bash
curl -s -X POST $DOMAIN/api/session \
  -H "Content-Type: application/json" \
  | python3 -m json.tool
```

**通過標準：** 回傳含 `token` 和 `sessionId` 的 JSON

---

### B3 問題分析（需有效 ANTHROPIC_API_KEY）
```bash
TOKEN=$(curl -s -X POST $DOMAIN/api/session \
  -H "Content-Type: application/json" \
  | python3 -c "import sys,json; d=json.load(sys.stdin); print(d['token'])")

curl -s -X POST $DOMAIN/api/analyze \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"problem_text":"我想做一個可收費的分析服務，第一版怎麼規劃？"}' \
  | python3 -m json.tool | head -30
```

**通過標準：**
- 回傳含 `analysis_id`、`result`、`is_partial: true`
- `result` 包含 `summary`、`breakdown`
- `requires_payment: true`

---

### B4 付款入口建立（需有效 Stripe 設定）
```bash
ANALYSIS_ID="<從 B3 取得的 analysis_id>"

curl -s -X POST $DOMAIN/api/pay/once \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d "{\"analysis_id\":\"$ANALYSIS_ID\"}" \
  | python3 -m json.tool
```

**通過標準：** 回傳含 `checkoutUrl`（https://checkout.stripe.com/...）

---

### B5 Webhook → Confirmation → Ledger 流程
```bash
# 安裝 Stripe CLI 後
stripe listen --forward-to $DOMAIN/webhook/stripe &
stripe trigger checkout.session.completed

# 驗證帳本
sleep 3
docker compose exec app sh -c \
  "sqlite3 /app/storage/db.sqlite \
  'SELECT event_type, status FROM ledger ORDER BY created_at DESC LIMIT 5;'"
```

**通過標準：** 帳本有 `payment_success`、`order_paid`、`result_unlock` 三筆事件

---

### B6 解鎖確認（付款後）
```bash
curl -s $DOMAIN/api/result/$ANALYSIS_ID \
  -H "Authorization: Bearer $TOKEN" \
  | python3 -m json.tool | head -20
```

**通過標準：** `is_partial: false`，`result` 包含 `steps`、`priorities`、`supplements`

---

### B7 重複解鎖防護
```bash
# 嘗試對同一訂單再次觸發 confirmation
# 預期：帳本無重複 result_unlock 事件

docker compose exec app sh -c \
  "sqlite3 /app/storage/db.sqlite \
  'SELECT COUNT(*) FROM ledger WHERE event_type=\"result_unlock\" AND order_id=\"<ORDER_ID>\";'"
```

**通過標準：** 計數為 1，不會重複

---

## C. 核心原則驗收

| 原則 | 驗收方式 | 通過標準 |
|------|---------|---------|
| **沒有 confirmation 不可解鎖** | 直接呼叫 `GET /api/result/:id`（未付款） | 回傳 `isPartial: true`，無法取得 full_result |
| **沒有 ledger 不算成立** | 付款後查帳本 | `result_unlock` 事件存在 |
| **同一訂單不可重複解鎖** | 觸發兩次 webhook | 帳本只有一筆 `result_unlock` |
| **webhook 簽名驗證** | 偽造 webhook 請求 | 回傳 400，無帳本寫入 |
| **SQLite 掛到 host** | `docker compose down && up` | db 資料不消失 |
| **重啟不丟資料** | 重啟 app 後查訂單 | 歷史訂單仍存在 |

---

## D. 維運驗收

```bash
# 停止並重新啟動，確認資料完整性
cd /opt/mrl_product_v1/app/deploy
docker compose down
docker compose up -d

# 等待健康檢查通過
sleep 20
docker compose ps

# 確認 DB 資料仍在
docker compose exec app sh -c \
  "sqlite3 /app/storage/db.sqlite 'SELECT COUNT(*) FROM orders;'"
```

**通過標準：** 重啟後訂單數量不變，服務正常啟動

---

## E. 最終上線確認

全部通過以下五件事，第一階段正式成立：

- [ ] 陌生人能進站看到首頁
- [ ] 能輸入問題看到 partial_result
- [ ] 能進入 Stripe 付款流程
- [ ] 付款成功後能取得 full_result
- [ ] DL580 重啟後資料不遺失

---

*origin_signature: MrLiouWord*
