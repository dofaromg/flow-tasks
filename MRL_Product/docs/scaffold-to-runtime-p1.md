# Scaffold → Runtime 升級說明
> origin_signature: MrLiouWord  
> phase: 第十七包

---

## 哪些 Stub 被升級為 Runnable

| 檔案 | Scaffold 狀態 | Deploy Pack 狀態 |
|------|-------------|----------------|
| `package.json` | 基本 stub（name 可能是 `-`）| runnable（正確 name/deps/engines）|
| `backend/server.js` | stub（TODO 路由）| runnable（DB init + health + route 掛載）|
| `backend/config.js` | stub | runnable（讀取所有必要 env）|
| `backend/routes/api.js` | stub | runnable stub（/session 有效，/analyze 回 501）|
| `storage/schema.sql` | 簡易 stub | runnable（4 張表 + index）|
| `deploy/Dockerfile` | 基本 stub | runnable（可 build，有 HEALTHCHECK）|
| `deploy/docker-compose.yml` | 基本 stub | runnable（volume / healthcheck / depends_on）|
| `deploy/nginx.conf` | 基本 stub | runnable（所有路徑正確 proxy）|
| `.env.example` | 基本 stub | runnable（包含所有必要變數）|
| `README.md` | scaffold 說明 | deploy 啟動說明（含 compose 指令）|

---

## 新增的 Runnable 檔案（scaffold 沒有）

| 檔案 | 說明 |
|------|------|
| `backend/routes/health.js` | `/health` endpoint，回傳 deploy_pack_id + timestamp |
| `backend/modules/db-init.js` | SQLite 自動初始化，找不到 DB 時自動建表 |
| `deploy/health-check.sh` | `curl /health` 驗收腳本，exit 0 = pass |
| `docs/deploy-pack-notes.md` | 架構說明 + endpoint 狀態 + 下一步指引 |

---

## 仍需人工補完的地方

| 檔案 | 需要做什麼 |
|------|----------|
| `backend/routes/api.js` | 接上 Core_Generator（analyze / result）|
| `backend/routes/payment.js` | 接上 Stripe checkout |
| `backend/routes/webhook.js` | 接上 Stripe webhook + confirmation |
| `backend/modules/ai.js`（不在 scaffold）| 加入 Anthropic SDK |
| `frontend/*.html` | 補充實際文案與樣式 |
| `.env` | 填入真實 API keys |

---

## 最快補完路線（用 MRL_Product_v1）

```bash
SRC=/home/claude/MRL_Product_v1
DST=storage/deploypacks/{pack_id}

# 複製成熟模組
cp $SRC/backend/modules/ai.js              $DST/backend/modules/
cp $SRC/backend/modules/order.js           $DST/backend/modules/
cp $SRC/backend/modules/ledger.js          $DST/backend/modules/
cp $SRC/backend/modules/confirmation.js    $DST/backend/modules/
cp -r $SRC/backend/core/generator/         $DST/backend/core/
cp -r $SRC/backend/templates/              $DST/backend/templates/

# 複製完整 routes
cp $SRC/backend/routes/api.js              $DST/backend/routes/
cp $SRC/backend/routes/payment.js          $DST/backend/routes/
cp $SRC/backend/routes/webhook.js          $DST/backend/routes/

# 複製前端資源
cp -r $SRC/frontend/assets/               $DST/frontend/assets/
# 並替換各頁面文案為你的產品

# 重新驗收
curl http://localhost:3000/health
```

---

*origin_signature: MrLiouWord*
