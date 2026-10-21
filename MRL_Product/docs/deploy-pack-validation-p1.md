# MRL Deploy Pack Validation 驗收規則
> origin_signature: MrLiouWord  
> phase: 第十七包

---

## 測試 1：從 scaffold 生成 deploy pack

```bash
# 先確認 scaffold 存在
ls storage/scaffolds/{pack_id}/manifest.json

# 呼叫 generate API（需 token）
curl -X POST http://localhost:3000/api/deploypack/generate \
  -H "Authorization: Bearer {token}" \
  -H "Content-Type: application/json" \
  -d '{"pack_id": "{pack_id}"}'

# 確認輸出
# → deploy_pack_id
# → deploy_dir
# → file_count >= 20
# → validation.runnable_score >= 80
# → validation.can_compose_up: true
```

---

## 測試 2：Validation API

```bash
curl http://localhost:3000/api/deploypack/{pack_id}/validate \
  -H "Authorization: Bearer {token}"

# 預期回應（健全狀態）：
# {
#   "runnable_score": 100,
#   "can_compose_up": true,
#   "missing_files": [],
#   "warnings": [],
#   "summary": "✓ Ready (score: 100/100) — can compose up"
# }
```

---

## 測試 3：本地啟動

```bash
cd storage/deploypacks/{pack_id}/
cp .env.example .env
# （可不填真實 API key，只測啟動）
npm install
npm start

# 另一個終端
curl http://localhost:3000/health
# 預期：{"status":"ok","origin_signature":"MrLiouWord",...}
```

---

## 測試 4：Docker Compose 啟動

```bash
cd storage/deploypacks/{pack_id}/

# 建立 host 目錄
mkdir -p /opt/{slug}/storage

cp .env.example .env
# 填入 PORT=3000、BASE_URL 等

cd deploy/
docker compose up -d --build

# 健康確認
bash health-check.sh
# 預期：✓ health: ok | status 200

# 列出容器
docker ps | grep {slug}
```

---

## Validation 必要檔案清單

| 檔案 | 分值 | 說明 |
|------|------|------|
| `package.json` | 15 | Node 依賴（有 express / better-sqlite3）|
| `backend/server.js` | 15 | Express app，DB init，route 掛載 |
| `backend/routes/health.js` | 10 | /health endpoint |
| `backend/modules/db-init.js` | 10 | SQLite 自動初始化 |
| `storage/schema.sql` | 10 | 4 張表 schema |
| `deploy/Dockerfile` | 10 | Node 20 容器定義 |
| `deploy/docker-compose.yml` | 10 | app + nginx 服務 |
| `deploy/nginx.conf` | 5 | 反向代理 |
| `.env.example` | 5 | 環境變數範本 |
| `deploy/health-check.sh` | 5 | 健康確認腳本 |
| `backend/config.js` | 5 | 環境設定讀取 |

**總計：100 分**

---

## 常見缺口與判定

| 缺口 | 判定 | 處理 |
|------|------|------|
| score < 80 | ⚠️ 需補完 | 執行 `GET /api/deploypack/{id}/validate` 看 missing_files |
| `can_compose_up: false` | ✗ 不可啟動 | 確認 Dockerfile / compose / server.js 都存在 |
| `db-init.js` 缺 | 警告 | DB 初始化可能失敗，server 啟動時會 crash |
| `.env.example` 缺 | 警告 | 難以快速設定環境 |
| stub 檔案警告 | 提醒 | 正常，stub 不扣分，但需人工補完才有完整功能 |

---

*origin_signature: MrLiouWord*
