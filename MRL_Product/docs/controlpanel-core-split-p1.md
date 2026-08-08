# MRL_ControlPanel + MRL_Core_Generator 分層架構
> origin_signature: MrLiouWord  
> phase: 第十四包

---

## 四層架構總覽

```
┌─────────────────────────────────────────────────────┐
│          MRL_ControlPanel（前端殼）                   │
│  index / app / pricing / product / success / admin   │
│  app.js / delivery-renderer.js                       │
└──────────────────────┬──────────────────────────────┘
                       │ HTTP API
┌──────────────────────▼──────────────────────────────┐
│          MRL_Core_Generator（後端生成核）              │
│  PromptBuilder / AnalyzeEngine / ResultNormalizer    │
│  TemplateSelector / Composer                         │
└──────────────────────┬──────────────────────────────┘
                       │ 讀寫狀態
┌──────────────────────▼──────────────────────────────┐
│          MRL_World_Gateway_v1（交易狀態層）            │
│  order / payment_entry / confirmation / ledger       │
│  rules / subscription / reconciliation               │
└──────────────────────┬──────────────────────────────┘
                       │ 模板合約
┌──────────────────────▼──────────────────────────────┐
│          MRL_Delivery_Template（交付模板層）           │
│  product-template.js / template-schema               │
│  delivery-renderer.js（前端側）                      │
└─────────────────────────────────────────────────────┘
```

---

## 一、MRL_ControlPanel（前端殼）

**本質：操作與顯示層**

**包含：**
- `frontend/index.html` — 首頁
- `frontend/app.html` — 任務輸入 + 結果顯示
- `frontend/pricing.html` — 定價視圖
- `frontend/product.html` — product 線入口頁
- `frontend/success.html` / `cancel.html` — 交易結果頁
- `frontend/admin.html` — 監看殼
- `frontend/assets/app.js` — 互動邏輯
- `frontend/assets/delivery-renderer.js` — template 渲染

**不應承擔：**
- AI analyze 核心決策
- template 資料生成
- 商業邏輯（付款 / 帳本）
- prompt 組裝

---

## 二、MRL_Core_Generator（後端生成核）

**本質：生成與組裝層**

**包含：**
```
backend/core/generator/
├── index.js          ← 統一入口
├── prompt-builder.js ← system prompt 組裝
├── result-normalizer.js ← AI output → template data
├── template-selector.js ← category → template_id
└── composer.js       ← 組裝最終 response payload
```

**職責：**
- 接收 ControlPanel 的 analyze 請求
- 組裝 prompt → 呼叫 AI → normalize → 選 template → compose
- 回傳標準化 payload 給 ControlPanel

---

## 三、MRL_World_Gateway_v1（交易狀態層）

**本質：狀態切換與唯一真相記錄層**

**包含：**
```
backend/modules/
├── order.js
├── payment_entry.js
├── confirmation.js
├── ledger.js
├── rules.js
├── subscription.js
└── reconciliation.js
```

**原則：**
- ledger 只寫不改
- confirmation 是唯一認定付款成立的入口
- 所有解鎖都必須經過 Gateway

---

## 四、MRL_Delivery_Template（交付模板層）

**本質：交付結構定義層**

**包含：**
```
backend/templates/
└── product-template.js  ← schema + normalize + mapping

frontend/assets/
└── delivery-renderer.js ← template renderer registry
```

**原則：**
- template schema 在後端定義
- renderer 在前端執行
- 兩邊以 template_id 對接

---

## 五、四層接線方式

```
ControlPanel（前端）
  → POST /api/analyze
  → Core_Generator.analyze({ problemText, category })
     → PromptBuilder.buildSystemPrompt(category)
     → AI 模型
     → ResultNormalizer.normalizeResult(raw, category)
     → TemplateSelector.selectTemplate(category)
     → Composer.composeAnalyzeResponse(...)
  → response: { analysis_id, category, template_id, result, ... }
  → delivery-renderer.js
     → templateIdFromCategory(category) → template_id
     → renderDeliveryTemplate(template_id, result, isPartial)
     → 渲染到 DOM
```

---

*origin_signature: MrLiouWord*
