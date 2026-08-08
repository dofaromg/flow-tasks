# MRL_Product_v1 DL580 實際部署指南
> origin_signature: MrLiouWord  
> target: DL580 G9（96 核 / 3TB RAM / 6×V100）  
> phase: 第十八包

---

## 前置確認清單

在開始部署前，確認以下項目全部 ✓：

```
[ ] DL580 可 SSH 連線
[ ] Docker + Docker Compose 已安裝（docker compose version）
[ ] curl 已安裝
[ ] .env 已填入真實金鑰（見下方）
[ ] /opt/mrl_product_v1/ 目錄有寫入權限
[ ] 80 / 443 port 未被佔用
```

---

## Step 1：SSH 進入 DL580

```bash
ssh your-user@dl580-ip
# 或透過 Named Tunnel
# ssh your-user@dl580.internal
```

---

## Step 2：取得專案

```bash
# 選項 A：從 Git
cd /opt
git clone https://github.com/dofaromg/mrl-product-v1.git mrl_product_v1
cd mrl_product_v1

# 選項 B：從 Deploy Pack 直接複製
# scp -r ./storage/deploypacks/{pack_id}/ user@dl580:/opt/mrl_product_v1/
```

---

## Step 3：建立 host 目錄

```bash
sudo mkdir -p /opt/mrl_product_v1/storage
sudo mkdir -p /opt/mrl_product_v1/logs/app
sudo mkdir -p /opt/mrl_product_v1/logs/nginx
sudo mkdir -p /opt/mrl_product_v1/backups
sudo chown -R $(whoami):$(id -gn) /opt/mrl_product_v1
```

---

## Step 4：設定環境變數

```bash
cd /opt/mrl_product_v1
cp .env.example .env
nano .env
```

必填項目：

```bash
NODE_ENV=production
PORT=3000
BASE_URL=https://your-domain.com        # 或 http://dl580-ip

JWT_SECRET=<openssl rand -hex 32 的輸出>

SQLITE_PATH=/app/storage/db.sqlite      # 容器內路徑（固定）

ANTHROPIC_API_KEY=sk-ant-...
ANTHROPIC_MODEL=claude-haiku-4-5-20251001

STRIPE_SECRET_KEY=sk_live_...
STRIPE_WEBHOOK_SECRET=whsec_...
STRIPE_PRICE_ONCE=price_...
STRIPE_PRICE_SUB=price_...

ADMIN_KEY=<自定義 admin key>
LOG_LEVEL=info
```

---

## Step 5：Pre-deploy 檢查

```bash
cd deploy/
bash pre-deploy-check.sh
# 預期：所有 [ OK ]，無 [FAIL]
```

若有 `[FAIL]`：
- `ANTHROPIC_API_KEY set` FAIL → .env 裡的 key 不是 `sk-ant-` 開頭，確認正確貼入
- `docker compose available` FAIL → `sudo apt install docker-compose-plugin`

---

## Step 6：啟動

```bash
# 方法 A：一鍵腳本（推薦）
bash setup.sh

# 方法 B：手動
cd deploy/
docker compose up -d --build
```

---

## Step 7：確認服務健康

```bash
# 健康確認
bash deploy/health-check.sh
# 預期：✓ health: ok | status 200

# 部署後完整驗收
bash scripts/post-deploy-verify.sh
# 預期：Pass 全部通過，Fail 0
```

---

## Step 8：確認容器運行

```bash
docker ps
# 預期：mrl-app (healthy), mrl-nginx (running)

docker compose logs -f app
# 預期：[mrl-product-v1] running on :3000 (env=production)
#        [db-init] DB initialized
```

---

## 維運指令速查

```bash
# 查看 log
docker compose -f /opt/mrl_product_v1/deploy/docker-compose.yml logs -f app

# 重啟服務
docker compose -f /opt/mrl_product_v1/deploy/docker-compose.yml restart app

# 停止全部
docker compose -f /opt/mrl_product_v1/deploy/docker-compose.yml down

# 更新代碼後重新部署
cd /opt/mrl_product_v1 && git pull
docker compose -f deploy/docker-compose.yml up -d --build

# 回滾
bash scripts/rollback.sh

# 每日健康確認（加進 crontab）
# 0 8 * * * bash /opt/mrl_product_v1/scripts/daily-check.sh
```

---

## 確認 Stripe webhook 路徑

Stripe Dashboard → Webhooks → Add endpoint：

```
https://your-domain.com/webhook/stripe
```

Events to listen：
- `checkout.session.completed`
- `customer.subscription.created`
- `customer.subscription.deleted`

---

## 排障指引

| 症狀 | 排查指令 | 解法 |
|------|---------|------|
| health 200 但頁面 502 | `docker ps` 查 nginx 狀態 | `docker compose restart nginx` |
| DB init 失敗 | `docker compose logs app` | 確認 SQLITE_PATH 和 volume 掛載一致 |
| Stripe webhook 失敗 | Stripe Dashboard → 查 webhook 事件 | 確認 STRIPE_WEBHOOK_SECRET 正確 |
| 容器一直重啟 | `docker compose logs app \| tail -20` | 看 FATAL 錯誤，通常是 .env 缺項 |
| AI analyze 失敗 | `docker compose logs app \| grep AI` | 確認 ANTHROPIC_API_KEY 有效 |

---

## 部署後第一次測試

```bash
# 測試首頁
curl -I http://localhost/
# → HTTP/1.1 200 OK

# 測試 health
curl http://localhost/health
# → {"status":"ok","origin":"MrLiouWord",...}

# 測試 API session
curl -X POST http://localhost/api/session \
  -H "Content-Type: application/json"
# → {"token":"...","sessionId":"..."}
```

---

*origin_signature: MrLiouWord*
