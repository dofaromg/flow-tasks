# MRL_Product_v1 × DL580 部署指南
> origin_signature: MrLiouWord  
> gateway: MRL_World_Gateway_v1  
> target: DL580 G9 自有部署

---

## 前置確認

在 DL580 上確認以下已就緒：

```bash
# Docker Engine
docker --version      # >= 24.0
docker compose version # >= 2.20

# 磁碟空間
df -h /opt             # 建議 > 20GB 可用
```

---

## Step 1：建立 host 目錄結構

```bash
# 所有 MRL 產品目錄
mkdir -p /opt/mrl_product_v1/{app,storage,logs/app,logs/nginx,ssl,backups}

# 確認
ls -la /opt/mrl_product_v1/
```

預期結構：
```
/opt/mrl_product_v1/
├── app/          ← 專案原始碼
├── storage/      ← SQLite db.sqlite（由 Docker volume 掛載）
├── logs/
│   ├── app/      ← Node.js app logs
│   └── nginx/    ← Nginx access/error logs
├── ssl/          ← SSL 憑證（有 HTTPS 時放這）
└── backups/      ← 手動或定期備份
```

---

## Step 2：複製專案到 DL580

**方法 A：從本地 scp 傳**
```bash
# 在本機執行
scp -r ./MRL_Product_v1/ root@<DL580-IP>:/opt/mrl_product_v1/app/
```

**方法 B：git clone（若有 repo）**
```bash
# 在 DL580 執行
cd /opt/mrl_product_v1/app
git clone https://github.com/dofaromg/MRL_Product_v1.git .
```

**方法 C：zip 傳輸**
```bash
# 本機打包
zip -r MRL_Product_v1.zip ./MRL_Product_v1/ -x "*/node_modules/*" -x "*/.env"

# 傳到 DL580
scp MRL_Product_v1.zip root@<DL580-IP>:/opt/mrl_product_v1/

# 在 DL580 解壓
cd /opt/mrl_product_v1
unzip MRL_Product_v1.zip -d app/
```

---

## Step 3：設定環境變數

```bash
cd /opt/mrl_product_v1/app

# 從範本複製
cp .env.example .env

# 編輯（填入真實值）
nano .env
```

**必填項目清單：**

| 變數 | 說明 | 範例 |
|------|------|------|
| `BASE_URL` | 正式網域，影響 Stripe callback | `https://mrl.yourdomain.com` |
| `JWT_SECRET` | 隨機 256-bit | `openssl rand -hex 32` |
| `ANTHROPIC_API_KEY` | Anthropic API Key | `sk-ant-api03-...` |
| `STRIPE_SECRET_KEY` | Stripe 正式金鑰 | `sk_live_...` |
| `STRIPE_WEBHOOK_SECRET` | Webhook 簽名秘鑰 | `whsec_...` |
| `STRIPE_PRICE_ONCE` | 單次方案 Price ID | `price_...` |
| `STRIPE_PRICE_SUB` | 月費方案 Price ID | `price_...` |
| `ADMIN_KEY` | 管理員 API 金鑰 | `openssl rand -hex 24` |

**安全確認：**
```bash
# 確認 .env 不可被他人讀取
chmod 600 /opt/mrl_product_v1/app/.env

# 確認 .env 沒有被 git 追蹤（應在 .gitignore）
grep ".env" /opt/mrl_product_v1/app/.gitignore
```

---

## Step 4：Stripe 設定

### 4.1 建立 Webhook Endpoint

1. 進入 Stripe Dashboard → Developers → Webhooks
2. 點 **Add endpoint**
3. URL 填入：`https://your-domain.com/webhook/stripe`
4. 選擇以下事件：
   - `checkout.session.completed`
   - `invoice.payment_succeeded`
   - `customer.subscription.deleted`
   - `payment_intent.payment_failed`
5. 取得 **Signing secret**（`whsec_...`），填入 `.env` 的 `STRIPE_WEBHOOK_SECRET`

### 4.2 建立 Price（商品定價）

**單次方案 NT$299：**
1. Stripe Dashboard → Products → Add product
2. 名稱：`完整分析報告（單次解鎖）`
3. 定價：TWD 299，One time
4. 取得 Price ID（`price_...`），填入 `STRIPE_PRICE_ONCE`

**月費方案 NT$499：**
1. 同上建立
2. 定價：TWD 499，Monthly recurring
3. 取得 Price ID，填入 `STRIPE_PRICE_SUB`

---

## Step 5：建構並啟動容器

```bash
cd /opt/mrl_product_v1/app/deploy

# 建構 image 並啟動（首次）
docker compose up -d --build

# 查看啟動狀態
docker compose ps

# 查看 app 啟動 log
docker compose logs app --tail=50
```

**預期輸出：**
```
[MRL] ── 啟動序列 ───────────────────────────────────
[MRL] origin_signature: MrLiouWord
[MRL] gateway: MRL_World_Gateway_v1
[MRL] env: production
[MRL] db:  /app/storage/db.sqlite
[MRL] DB 不存在，正在初始化 schema...
[MRL] DB 初始化完成
[MRL] ── 啟動 Node.js app ──────────────────────────
{"ts":"...","level":"info","msg":"MRL_Product_v1 started","port":3000,...}
```

---

## Step 6：驗證服務

```bash
# 健康檢查
curl -s http://localhost:3000/health | python3 -m json.tool

# 預期回應：
# {
#   "status": "ok",
#   "service": "MRL_Product_v1",
#   "gateway": "MRL_World_Gateway_v1",
#   "origin": "MrLiouWord",
#   "ts": "2026-..."
# }

# Nginx 健康確認
curl -s http://localhost/health | python3 -m json.tool

# 測試靜態資源
curl -I http://localhost/assets/style.css
```

---

## Step 7：網域設定（DNS）

在你的 DNS 設定（Cloudflare / 一般 DNS）：

```
A 紀錄：mrl.yourdomain.com → <DL580 公網 IP>
```

或透過 Cloudflare Tunnel：
```bash
# 已有 Named Tunnel 可用
cloudflared tunnel route dns <tunnel-name> mrl.yourdomain.com
```

---

## Step 8：HTTPS 設定（有網域後）

**方法 A：Let's Encrypt（certbot）**
```bash
# 在 DL580 安裝 certbot
apt-get install certbot

# 取得憑證（需先暫停 nginx 的 80 port 或用 webroot 模式）
certbot certonly --standalone -d mrl.yourdomain.com

# 憑證位置
# /etc/letsencrypt/live/mrl.yourdomain.com/fullchain.pem
# /etc/letsencrypt/live/mrl.yourdomain.com/privkey.pem

# 複製到 mrl ssl 目錄
cp /etc/letsencrypt/live/mrl.yourdomain.com/fullchain.pem /opt/mrl_product_v1/ssl/
cp /etc/letsencrypt/live/mrl.yourdomain.com/privkey.pem   /opt/mrl_product_v1/ssl/
```

**方法 B：Cloudflare Tunnel（推薦，無需管理憑證）**
```bash
# 用 Named Tunnel（已有 DL580 tunnel 可用）
# 在 Cloudflare Dashboard 設定：
# mrl.yourdomain.com → localhost:80
```

啟用 HTTPS 後，編輯 `nginx.conf`：
1. 取消 HTTPS server block 的註解
2. 在 HTTP server block 改為 `return 301 https://$host$request_uri;`
3. `docker compose restart nginx`

---

## Step 9：驗收確認

```bash
# 完整驗收腳本（在 DL580 執行）
DOMAIN="http://localhost"   # 換成正式網域

# 1. 首頁
echo "=== 1. 首頁 ==="
curl -s -o /dev/null -w "%{http_code}" $DOMAIN/
echo ""

# 2. app 頁
echo "=== 2. app 頁 ==="
curl -s -o /dev/null -w "%{http_code}" $DOMAIN/app.html
echo ""

# 3. Health
echo "=== 3. Health ==="
curl -s $DOMAIN/health
echo ""

# 4. Session 建立
echo "=== 4. Session ==="
curl -s -X POST $DOMAIN/api/session -H "Content-Type: application/json"
echo ""

# 5. Analyze API（需要有效 ANTHROPIC_API_KEY）
echo "=== 5. Analyze ==="
curl -s -X POST $DOMAIN/api/analyze \
  -H "Content-Type: application/json" \
  -d '{"problem_text":"我想做一個可收費網站，第一版應該怎麼規劃？"}' \
  | python3 -m json.tool | head -20
echo ""

# 6. SQLite 確認
echo "=== 6. SQLite ==="
ls -lh /opt/mrl_product_v1/storage/db.sqlite

# 7. Logs 確認
echo "=== 7. Logs ==="
ls -la /opt/mrl_product_v1/logs/app/
ls -la /opt/mrl_product_v1/logs/nginx/
```

---

## 常用維運指令

```bash
# 進入 deploy 目錄
cd /opt/mrl_product_v1/app/deploy

# 啟動（重建 image）
docker compose up -d --build

# 啟動（不重建）
docker compose up -d

# 停止
docker compose down

# 重啟 app（不重建）
docker compose restart app

# 重啟 nginx
docker compose restart nginx

# 查看所有容器狀態
docker compose ps

# 即時追蹤 app log
docker compose logs -f app

# 即時追蹤 nginx log
docker compose logs -f nginx

# 進入 app 容器
docker compose exec app sh

# 查看 SQLite（在容器內）
docker compose exec app sh -c "sqlite3 /app/storage/db.sqlite '.tables'"

# 查看最近帳本
docker compose exec app sh -c "
  sqlite3 /app/storage/db.sqlite 'SELECT * FROM ledger ORDER BY created_at DESC LIMIT 10;'
"

# 查看最近訂單
docker compose exec app sh -c "
  sqlite3 /app/storage/db.sqlite 'SELECT * FROM orders ORDER BY created_at DESC LIMIT 10;'
"
```

---

## 更新部署

```bash
cd /opt/mrl_product_v1/app

# 更新原始碼（git pull 或重新 scp）
git pull  # 或重新上傳

# 重建並重啟
cd deploy
docker compose up -d --build

# 確認啟動成功
docker compose ps
docker compose logs app --tail=20
```

---

## 驗收標準清單

- [ ] `docker compose ps` 顯示 `app` 和 `nginx` 均為 `healthy`/`Up`
- [ ] `curl http://localhost/health` 回傳 `{"status":"ok",...}`
- [ ] 首頁 `http://localhost/` 可開啟
- [ ] app 頁 `http://localhost/app.html` 可輸入問題
- [ ] POST `/api/analyze` 可得到 `partial_result`
- [ ] POST `/api/pay/once` 可得到 Stripe checkout URL
- [ ] `/opt/mrl_product_v1/storage/db.sqlite` 存在且有資料
- [ ] `/opt/mrl_product_v1/logs/app/` 有 log 寫入
- [ ] Stripe webhook 可觸發（用 Stripe CLI 測試）

---

*origin_signature: MrLiouWord*
