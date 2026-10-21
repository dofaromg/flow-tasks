# Pack → Scaffold → Deploy 橋接說明
> origin_signature: MrLiouWord  
> phase: 第十六包

---

## 三層的差異

```
ProductPack JSON           Scaffold               Deploy Pack
──────────────────        ──────────────────     ──────────────────
「說明書」                「骨架」               「可執行包」

描述要做什麼              生成檔案結構           填充商業邏輯後
pages / flows /           stub 程式碼           可直接 docker compose up
pricing / deployment      人工補完區域標示

storage/packs/*.json      storage/scaffolds/     （第十七包目標）
                          {pack_id}/
```

---

## 目前的進度

| 層 | 狀態 | 說明 |
|---|------|------|
| ProductPack | ✅ 第十五包 | JSON spec，含 pages / flows / pricing / deployment |
| Scaffold | ✅ 第十六包 | 26–27 個檔案骨架，manifest + stub 程式碼 |
| Deploy Pack | 🔜 第十七包 | Scaffold + 完整商業邏輯填充 = 真正可啟動包 |

---

## Scaffold → Deploy Pack 需要做什麼（第十七包方向）

### 填充後端模組
```
scaffold/backend/modules/ai.js          ← 填入 Core_Generator 邏輯
scaffold/backend/modules/order.js       ← 填入 Gateway order CRUD
scaffold/backend/modules/ledger.js      ← 填入 Gateway ledger
scaffold/backend/modules/confirmation.js ← 填入 Gateway confirmation
```

可直接複製 MRL_Product_v1 的對應模組，依需求調整。

### 填充路由
```
scaffold/backend/routes/api.js           ← 填入 analyze / result / session
scaffold/backend/routes/payment.js       ← 填入 Stripe checkout
scaffold/backend/routes/webhook.js       ← 填入 Stripe webhook
```

### 填充前端
```
scaffold/frontend/*.html                 ← 填入實際文案 / 樣式
scaffold/frontend/assets/app.js          ← 填入完整互動邏輯
scaffold/frontend/assets/style.css       ← 可直接使用 MRL_Product_v1 的 style.css
```

### 填入 .env 真實值
```
.env 填入：ANTHROPIC_API_KEY / STRIPE_* / JWT_SECRET / BASE_URL
```

---

## 自動化填充的路線（未來）

目前是人工補完。未來可在 scaffold-builder 加一個新策略：

**Strategy A：從 MRL_Product_v1 複製成熟模組**
```js
// scaffold-filler.js（未來）
function fillFromMRL(scaffoldDir) {
  copyModule('ai.js');
  copyModule('order.js');
  copyModule('ledger.js');
  copyModule('confirmation.js');
  copyAssets();
}
```

**Strategy B：依 pack 客製化填充**
```js
// 依 pack.mode / pack.pricing_model 選擇填充策略
// website mode  → 填入標準收費流程
// payment mode  → 強化 pricing 頁 + 付款路由
// converge mode → 簡化頁面，突出核心功能
```

---

## 快速從 Scaffold 到第一次啟動

```bash
# 1. 複製 scaffold 到工作目錄
cp -r storage/scaffolds/mrl_pack_xxx/ ./my-product/
cd my-product/

# 2. 填入金鑰
cp .env.example .env
nano .env  # 填入 ANTHROPIC_API_KEY / STRIPE_* 等

# 3. 安裝依賴
npm install

# 4. 啟動（dev）
npm run dev

# 5. 確認健康
curl http://localhost:3000/health
# → {"status":"ok","service":"my-product"}

# 6. Docker 部署到 DL580
cd deploy/
docker compose up -d --build
```

---

## 完整路徑總覽

```
使用者描述問題
  → /api/analyze（Core_Generator）
  → MRL_Delivery_Template_Product_v1（顯示方案）
  → 付款解鎖 full_result
  → 生成 ProductPack（/api/pack/generate）
     → storage/packs/{pack_id}.json
  → 生成 Scaffold（/api/scaffold/generate）
     → storage/scaffolds/{pack_id}/（26+ 個檔案）
  → 人工填充商業邏輯（或未來自動填充）
  → Docker 部署到 DL580
     → docker compose up -d --build
```

---

*origin_signature: MrLiouWord*
