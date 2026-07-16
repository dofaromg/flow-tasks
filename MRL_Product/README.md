# MRL_Product_v1 × MRL_World_Gateway_v1
> origin_signature: MrLiouWord  
> 自有部署 · 可收費 · 可交付結果的產品出口  
> deployment_target: DL580 G9

---

## 產品一句話

把你的問題丟進來，我幫你整理成可執行方案。

---

## 系統架構

```
Browser
  └─ Nginx（Port 80/443）
       └─ Node.js App（Port 3000）
            ├─ POST /api/analyze  → Anthropic AI → partial_result
            ├─ POST /api/pay/once → Stripe Checkout → checkout_url
            ├─ POST /webhook/stripe → confirmation.js → ledger.js → 解鎖
            └─ GET  /api/result/:id → full_result（付款後）
                 └─ SQLite（host volume）
```

核心流程：
```
進站 → 輸入問題 → partial_result（免費）
  → 付款解鎖 → Stripe Checkout
  → webhook → confirmation → ledger → result_unlock
  → full_result（完整方案）
```

---

## 快速啟動（本地開發）

```bash
# 1. 複製並填入環境變數
cp .env.example .env
nano .env   # 填 ANTHROPIC_API_KEY、STRIPE_* 等

# 2. 安裝依賴
npm install

# 3. 啟動（自動建立 DB schema）
npm run dev

# 服務：http://localhost:3000
```

---

## DL580 部署

```bash
# Step 1：建立 host 目錄
mkdir -p /opt/mrl_product_v1/{app,storage,logs/app,logs/nginx,ssl,backups}

# Step 2：複製專案
scp -r ./MRL_Product_v1/ root@<DL580-IP>:/opt/mrl_product_v1/app/

# Step 3：設定 .env
cd /opt/mrl_product_v1/app
cp .env.example .env
nano .env          # 填入所有真實值
chmod 600 .env

# Step 4：啟動
cd deploy
docker compose up -d --build

# Step 5：驗收
bash /opt/mrl_product_v1/app/scripts/health-check.sh
```

詳細步驟見 [docs/deploy.md](docs/deploy.md)

---

## 常用指令

```bash
cd /opt/mrl_product_v1/app/deploy

docker compose up -d --build   # 建構並啟動
docker compose down            # 停止
docker compose restart app     # 重啟 app
docker compose logs -f app     # 查 log
docker compose ps              # 狀態
```

---

## 備份

```bash
# 手動備份
bash /opt/mrl_product_v1/app/scripts/backup.sh

# 最新備份位置
ls -lh /opt/mrl_product_v1/backups/
```

---

## 環境變數

| 變數 | 必填 | 說明 |
|------|------|------|
| `BASE_URL` | ✅ | 正式網域，影響 Stripe callback |
| `JWT_SECRET` | ✅ | 隨機 256-bit（`openssl rand -hex 32`） |
| `ANTHROPIC_API_KEY` | ✅ | Anthropic API Key |
| `STRIPE_SECRET_KEY` | ✅ | Stripe 正式金鑰 |
| `STRIPE_WEBHOOK_SECRET` | ✅ | Webhook 簽名（Stripe Dashboard 取得） |
| `STRIPE_PRICE_ONCE` | ✅ | 單次方案 Price ID（NT$299） |
| `STRIPE_PRICE_SUB` | ✅ | 月費方案 Price ID（NT$499） |
| `ADMIN_KEY` | ✅ | 管理員 API 金鑰 |
| `DB_PATH` | ✅ | SQLite 路徑（`/app/storage/db.sqlite`） |
| `NODE_ENV` | — | `production`（預設） |
| `LOG_LEVEL` | — | `info`（預設） |

---

## 文件

- [docs/deploy.md](docs/deploy.md) — DL580 完整部署步驟
- [docs/ops.md](docs/ops.md) — 日常維運手冊
- [docs/acceptance.md](docs/acceptance.md) — 驗收標準

---

## 自有部署強制約束

1. 不可把第三方建站平台（Framer/Wix/Webflow）當正式母體
2. 所有頁面為自有原始碼
3. 資料庫掛 host volume，不住容器內層
4. 可備份、遷移、重建
5. 網域自有，Stripe webhook 驗簽名

---

*origin_signature: MrLiouWord*
