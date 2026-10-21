# MRL_ControlPanel 前端地圖
> origin_signature: MrLiouWord  
> phase: 第十四包

---

## 頁面職責分工

| 頁面 | ControlPanel 子層 | 職責 |
|------|-----------------|------|
| `index.html` | 流量入口 | 首頁、情境卡、CTA |
| `app.html` | 核心操作 | 輸入 → partial/full 顯示 → 付款 CTA |
| `pricing.html` | 定價視圖 | 方案展示 |
| `product.html` | product 入口 | product 線專屬落地頁 |
| `success.html` | 交易結果 | 付款後輪詢 + 導回 |
| `cancel.html` | 交易取消 | 保留分析 + 導回 |
| `admin.html` | 監看殼 | metrics / funnel / category / 決策摘要 |

---

## JS 職責分工

### `app.js` — 互動邏輯（Flow + Input + Delivery 控制）

**Input Layer：**
```
- setupCategoryChips()    ← category 選擇
- setupProductModes()     ← product quick modes
- readUrlParams()         ← URL ?cat=xxx 讀取
- updateExamplePrompts()  ← prompts 動態更新
- updatePlaceholder()     ← placeholder 切換
```

**Flow Layer：**
```
- init()                  ← 啟動 + session
- startAnalysis()         ← 提交分析
- loadResult()            ← 載入已有分析
- showPhase()             ← input/loading/result 切換
- resetToInput()          ← 重置狀態
- payOnce() / paySub()    ← 付款觸發
```

**Delivery View Layer：**
```
- renderResult()          ← 分派 template renderer 或 fallback
- makeBlock()             ← 建立 result block DOM
- showPostUnlockUI()      ← full result 後的升級提示 + feedback
- setupFeedback()         ← 星評互動
- highlightStars()        ← 星評 UI
- submitFeedback()        ← 回饋送出
```

---

### `delivery-renderer.js` — Template Renderer Registry

```
- STYLE_ROLE_MAP                    ← style role → CSS class
- PRODUCT_TEMPLATE_DEF              ← product sections 定義
- renderProductDeliveryTemplate()   ← product renderer
- TEMPLATE_REGISTRY                 ← { template_id → renderer }
- renderDeliveryTemplate()          ← 通用分派入口
- templateIdFromCategory()          ← category → template_id（前端側）
```

---

## 未來擴張指引

### 新增 category 頁面
```
1. 複製 product.html → decision.html
2. 改文案（針對 decision 情境）
3. 在 page.js 加路由 /decision
4. 在 index.html 熱門情境卡中調整順序（若升為主打）
```

### 新增 template renderer
```
1. 在 delivery-renderer.js 加 DECISION_TEMPLATE_DEF
2. 實作 renderDecisionDeliveryTemplate()
3. 加入 TEMPLATE_REGISTRY
4. 加入 templateIdFromCategory() mapping
5. app.js 不需要改
```

### 新增 admin 視圖
```
1. 在 admin.html 加 sidebar nav item
2. 在對應 tab div 加 HTML
3. 在 JS 加 loadXxx() 函式
4. 在 loadTab() switch 加 case
5. 在後端 admin.js 加對應 API
```

---

## 保持 ControlPanel 乾淨的原則

```
✅ app.js 只管顯示狀態和使用者互動
✅ delivery-renderer.js 只管 DOM 渲染
✅ 後端邏輯（prompt / normalize / template 選擇）不往前端跑
✅ 不在前端 hardcode 商業邏輯（如：product 才有哪些功能）
❌ 不在 app.js 裡放大型的 AI prompt 文字
❌ 不在前端直接呼叫後端 normalizer
```

---

*origin_signature: MrLiouWord*
