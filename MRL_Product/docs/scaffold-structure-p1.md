# MRL Scaffold 目錄結構說明
> origin_signature: MrLiouWord  
> phase: 第十六包

---

## 完整目錄結構

```
storage/scaffolds/{pack_id}/
│
├── manifest.json           ← Scaffold 元資料（pack_id / scaffold_id / pages / stack）
├── README.md               ← 快速啟動說明（含 pack 的核心方向 / 執行順序 / 待補清單）
├── package.json            ← Node.js 依賴清單（express / better-sqlite3 / stripe / anthropic）
├── .env.example            ← 環境變數範本（需人工填入真實金鑰）
├── .gitignore              ← 標準 gitignore（排除 .env / node_modules / db 檔）
│
├── frontend/               ← 前端頁面（依 pack.pages 動態生成）
│   ├── index.html          ← 首頁（Hero + CTA placeholder）
│   ├── app.html            ← 分析入口（input 區塊 stub）
│   ├── pricing.html        ← 定價（雙方案卡 stub）
│   ├── success.html        ← 付款成功
│   ├── cancel.html         ← 付款取消
│   ├── product.html        ← 主打入口（若 mode ≠ converge）
│   └── assets/
│       ├── style.css       ← 基礎樣式 stub（dark theme 骨架）
│       └── app.js          ← 互動邏輯 stub（session / apiFetch）
│
├── backend/                ← 後端骨架
│   ├── server.js           ← Express app + health endpoint
│   ├── config.js           ← 環境變數讀取
│   ├── routes/
│   │   ├── api.js          ← analyze / result / session stub
│   │   ├── payment.js      ← Stripe checkout stub
│   │   └── webhook.js      ← Stripe webhook stub
│   └── modules/
│       ├── ai.js           ← Anthropic SDK stub
│       ├── order.js        ← order CRUD stub
│       ├── ledger.js       ← 帳本寫入 stub（唯一真相層）
│       └── confirmation.js ← 付款確認 stub
│
├── storage/
│   └── schema.sql          ← SQLite schema（users / analyses / orders / ledger）
│
├── deploy/                 ← 容器化部署
│   ├── Dockerfile          ← Node 20 + 系統依賴
│   ├── docker-compose.yml  ← app + nginx，volume 掛載位置標示
│   ├── nginx.conf          ← 反向代理設定（動態依 slug 生成）
│   └── .env.example        ← 同根目錄（deploy 專用路徑）
│
└── docs/
    └── scaffold-notes.md   ← 頁面清單 / 使用者流程 / 定價 / 部署目標
```

---

## 各類檔案說明

### ✅ 可直接使用（不用改動）
- `manifest.json` — 元資料，不需手動修改
- `deploy/Dockerfile` — 基本可用，視 Node 版本調整
- `deploy/docker-compose.yml` — 確認 volume 路徑後可用
- `deploy/nginx.conf` — 基礎反代，HTTPS 需補 SSL 設定

### 📝 需填入真實值
- `.env.example` → 複製為 `.env`，填入：
  - `ANTHROPIC_API_KEY`
  - `STRIPE_SECRET_KEY` / `STRIPE_WEBHOOK_SECRET`
  - `STRIPE_PRICE_ONCE` / `STRIPE_PRICE_SUB`
  - `JWT_SECRET` / `ADMIN_KEY`
  - `BASE_URL`（你的網域）

### 🔧 需人工補完的程式碼
| 檔案 | 補完內容 |
|------|---------|
| `backend/routes/api.js` | analyze API 接上 Core_Generator |
| `backend/routes/payment.js` | Stripe checkout session 建立邏輯 |
| `backend/routes/webhook.js` | Stripe 事件驗證 + confirmation 觸發 |
| `backend/modules/ai.js` | Anthropic SDK 呼叫 + prompt |
| `backend/modules/order.js` | SQLite CRUD |
| `backend/modules/ledger.js` | 帳本寫入邏輯（只增不刪）|
| `backend/modules/confirmation.js` | 付款確認核心（Gateway）|
| `frontend/*.html` | 實際文案 / 樣式 / 互動邏輯 |
| `frontend/assets/app.js` | 完整互動邏輯 |

### 🤖 未來可自動化的地方
- `backend/modules/*` — 可從 MRL_Product_v1 直接複製成熟版本
- `frontend/assets/style.css` — 可從 MRL_Product_v1 複製
- `storage/schema.sql` — 可直接使用此骨架加欄位

---

## 與 MRL_Product_v1 的關係

Scaffold 是 MRL_Product_v1 的「精簡版骨架」：

```
MRL_Product_v1（完整版）
  → 16 包的成熟實作
  → 可直接部署到 DL580

Scaffold（骨架版）
  → 依具體需求生成的客製化起點
  → 需人工補完商業邏輯
  → 未來可自動填充（第十七包方向）
```

---

*origin_signature: MrLiouWord*
