# MRL_Product_v1 指標定義與解讀
> origin_signature: MrLiouWord

---

## 事件定義

| 事件名稱 | 觸發時機 | 追蹤位置 |
|---------|---------|---------|
| `page_view_home` | 使用者訪問首頁 | `routes/page.js` middleware |
| `page_view_app` | 使用者訪問 app.html | `routes/page.js` middleware |
| `page_view_pricing` | 使用者訪問 pricing.html | `routes/page.js` middleware |
| `analyze_started` | 前端點擊「開始分析」，API 收到請求 | `routes/api.js` POST /analyze |
| `analyze_success` | AI 分析完成，partial_result 產生 | `routes/api.js` POST /analyze |
| `analyze_failed` | AI 分析失敗 | `routes/api.js` POST /analyze |
| `pay_click_once` | 點擊單次解鎖，建立 Stripe checkout | `routes/payment.js` POST /once |
| `pay_click_sub` | 點擊月費訂閱，建立 Stripe checkout | `routes/payment.js` POST /subscription |
| `payment_success` | Stripe webhook 確認付款成功 | `modules/translator.js` |
| `unlock_success` | full_result 成功解鎖 | `modules/translator.js` |
| `result_full_view` | 使用者成功取得 full_result | `routes/api.js` GET /result/:id |

---

## 漏斗 KPI 定義

```
首頁訪問（page_view_home）
    ↓ [首頁→App 率]
App 訪問（page_view_app）
    ↓ [App→分析 率]
分析成功（analyze_success）
    ↓ [分析→付款 率]
付款成功（payment_success）
    ↓ [付款→解鎖 率]
結果解鎖（unlock_success）
```

### 各轉換率計算

```
首頁→App 率 = page_view_app / page_view_home
App→分析 率 = analyze_success / page_view_app
分析→付款 率 = payment_success / analyze_success
付款→解鎖 率 = unlock_success / payment_success
整體轉換率  = unlock_success / page_view_home
```

### 參考基準（第一個月）

| 轉換率 | 偏低 | 正常 | 良好 |
|--------|------|------|------|
| 首頁→App | < 15% | 15–35% | > 35% |
| App→分析 | < 20% | 20–50% | > 50% |
| 分析→付款 | < 2% | 2–10% | > 10% |
| 付款→解鎖 | < 95% | 95–99% | 100% |

> 注意：早期流量少時，轉換率波動很大，不要過度解讀單日數字。看 7 日趨勢比較有意義。

---

## 商業指標

| 指標 | 說明 | 計算 |
|------|------|------|
| 日營收 | 當日成功付款總額 | SUM(payments.amount) WHERE date = today |
| 週營收 | 近 7 日付款總額 | SUM(payments.amount) WHERE date >= today-7 |
| 平均客單 | 每筆付款平均金額 | AVG(payments.amount) |
| 訂閱數 | 當前有效訂閱 | COUNT(subscriptions WHERE status='active') |
| MRR（月訂閱收入）| 訂閱數 × NT$499 | active_subs × 499 |

---

## 異常訊號

### 🔴 需要立即處理

| 訊號 | 可能原因 | 動作 |
|------|---------|------|
| `payment_success` 有，`unlock_success` 沒有 | webhook 未到 / confirmation 失敗 | 執行 `/admin/reconcile` |
| `pay_click_once` 多，`payment_success` 少 | Stripe 設定問題 / 使用者放棄 | 檢查 Stripe Dashboard |
| Health check 失敗 | 容器崩潰 | `docker compose restart` |
| 0 首頁訪問（但昨天有）| 網域/DNS 問題 | 檢查 nginx / Cloudflare |

### 🟡 需要觀察

| 訊號 | 可能原因 | 動作 |
|------|---------|------|
| App 進入率持續 < 10% | 首頁文案不夠清楚 | 優化 Hero CTA |
| 分析→付款率 < 2% | partial_result 太弱 or 定價太高 | 調整 partial 或測試降價 |
| 有流量但 0 分析 | app.html 互動有問題 | 手動測試分析流程 |

---

## API 查詢速查

```bash
DOMAIN=http://localhost
KEY=YOUR_ADMIN_KEY

# 今日 + 7 日 metrics
curl -s "$DOMAIN/admin/metrics" -H "X-Admin-Key: $KEY"

# 漏斗轉換率
curl -s "$DOMAIN/admin/funnel?days=7" -H "X-Admin-Key: $KEY"

# 近 30 筆事件
curl -s "$DOMAIN/admin/events?limit=30" -H "X-Admin-Key: $KEY"

# 近期訂單
curl -s "$DOMAIN/admin/orders?limit=20" -H "X-Admin-Key: $KEY"

# 帳本
curl -s "$DOMAIN/admin/ledger?limit=20" -H "X-Admin-Key: $KEY"

# 系統狀態
curl -s "$DOMAIN/admin/health" -H "X-Admin-Key: $KEY"

# 整體統計
curl -s "$DOMAIN/admin/stats" -H "X-Admin-Key: $KEY"

# 對帳
curl -s -X POST "$DOMAIN/admin/reconcile" -H "X-Admin-Key: $KEY"
```

---

*origin_signature: MrLiouWord*
