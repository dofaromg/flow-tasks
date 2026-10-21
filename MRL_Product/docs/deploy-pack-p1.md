# MRL Deploy Pack 定義
> origin_signature: MrLiouWord  
> phase: 第十七包

---

## Deploy Pack 是什麼

Deploy Pack = Scaffold 基礎上補齊最小 runtime 能力後，可真正啟動的部署包。

它是整條 pipeline 的最後一層：

```
分析結果    →  ProductPack  →  Scaffold     →  Deploy Pack
(AI 方案)     (JSON 規格)    (檔案骨架)      (可啟動包)
```

---

## 與 Pack / Scaffold 的差異

| 面向 | ProductPack | Scaffold | Deploy Pack |
|------|------------|---------|-------------|
| 本質 | JSON 規格文件 | 骨架（stub 為主）| 可啟動包（runnable 為主）|
| server.js | 無 | stub（有 TODO）| runnable（可啟動）|
| DB init | 無 | 無 | ✅ `db-init.js`（自動建表）|
| /health | 無 | inline（不完整）| ✅ 獨立 route |
| Dockerfile | 無 | 基本 stub | ✅ 可 build |
| docker-compose | 無 | 基本 stub | ✅ 可 compose up |
| schema.sql | 無 | 極簡 stub | ✅ 4 張表（sessions/analyses/orders/ledger）|
| health-check.sh | 無 | 無 | ✅ curl /health 驗收腳本 |
| Validation | 無 | 無 | ✅ runnable_score + can_compose_up |

---

## Runnable Score 說明

| Score | 意義 |
|-------|------|
| 100 | 所有必要檔案完整，可立即 compose up |
| 80–99 | 輕微缺失，可啟動但有部分功能未完整 |
| 50–79 | 中等缺失，需補充後才可啟動 |
| < 50 | 嚴重缺失，不可啟動 |

---

## 啟動後可用的 endpoints

| 路徑 | 狀態 | 說明 |
|------|------|------|
| `GET /health` | ✅ runnable | 系統健康確認 |
| `POST /api/session` | ✅ runnable | JWT token |
| `POST /api/analyze` | ⚠️ stub | 需接 Core_Generator |
| `POST /payment/once` | ⚠️ stub | 需配 Stripe |
| `POST /webhook/stripe` | ⚠️ stub | 需配 Stripe |

---

## 存放位置

```
storage/deploypacks/{pack_id}/
├── manifest.json           ← deploy pack 元資料
├── README.md               ← 啟動說明
├── package.json            ← runnable 版依賴
├── .env.example            ← 環境變數範本
├── backend/
│   ├── server.js           ← runnable Express app
│   ├── config.js           ← 環境設定
│   ├── routes/health.js    ← /health (runnable)
│   ├── routes/api.js       ← stub
│   ├── modules/db-init.js  ← DB 自動初始化 (runnable)
├── storage/schema.sql      ← runnable schema
├── deploy/
│   ├── Dockerfile          ← runnable
│   ├── docker-compose.yml  ← runnable
│   ├── nginx.conf          ← runnable
│   └── health-check.sh     ← 可執行驗收腳本
└── docs/deploy-pack-notes.md
```

---

*origin_signature: MrLiouWord*
