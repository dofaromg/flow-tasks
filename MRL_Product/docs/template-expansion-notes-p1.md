# MRL Template 擴展筆記（第一版）
> origin_signature: MrLiouWord  
> phase: 第十三包

---

## 一、Product 模板做對了什麼（可沿用的）

### 1. 三層分離
- Data Layer（schema）存在 `backend/templates/`
- Render Layer 存在 `frontend/assets/delivery-renderer.js`
- Style Role 解耦，CSS 改了不影響 template 定義

### 2. 可沿用的 sections
以下 section 在幾乎所有 category 都有意義：

| Section key | 在其他 category 能用嗎 |
|------------|-------------------|
| `problem_breakdown` | ✅ 全部 category |
| `execution_steps` | ✅ 全部 category |
| `next_actions` | ✅ 全部 category |
| `common_failures` | ✅ 全部 category（warning） |
| `delivery_footer` | ✅ 全部（文字可調整）|
| `core_judgment` | ✅ 可沿用，但標籤改 |
| `first_version_scope` | ❌ product 特有 |
| `do_vs_not_do` | ⚠️ product / system 適用，其他 category 標籤需改 |

### 3. 可沿用的 style roles
全部 style roles 都設計成通用的，不限 product：
- `accent` / `doc_section` / `step_list` / `contrast_warning` / `failure_warning` / `footer_cta`

---

## 二、各 Category 建議的 Template 差異

### Decision Template（`MRL_Delivery_Template_Decision_v1`）
```
sections:
  core_judgment       → '核心選擇'（label 改）
  problem_breakdown   → '決策卡點'
  options_comparison  → '選項比較'（新增）
  recommended_option  → '建議選項'（新增）
  execution_steps     → '驗證步驟'
  tradeoff_summary    → '代價總結'（新增）
  next_actions        → '下一步'
  common_failures     → '常見錯誤'
  delivery_footer     → 靜態（文字改為決策場景）
```

### System Template（`MRL_Delivery_Template_System_v1`）
```
sections:
  core_judgment       → '核心阻塞點'
  problem_breakdown   → '系統問題拆解'
  module_structure    → '模組建議'（新增）
  cleanup_priority    → '先砍什麼'（新增）
  execution_steps     → '整理順序'
  do_vs_not_do        → '先動 vs 先不動'
  next_actions        → '穩定後的下一步'
  common_failures     → '常見過度設計點'
  delivery_footer     → 靜態
```

### Business Template（`MRL_Delivery_Template_Business_v1`）
```
sections:
  core_judgment       → '核心商業判斷'
  problem_breakdown   → '商業卡點拆解'
  target_audience     → '最可能付錢的客群'（新增）
  pricing_direction   → '定價建議'（新增）
  first_product       → '第一版賣什麼'（新增）
  execution_steps     → '最快收到第一筆錢的步驟'
  next_actions        → '驗證後的下一步'
  common_failures     → '常見商業化失敗原因'
  delivery_footer     → 靜態
```

---

## 三、擴展時的步驟

```
1. 在 backend/templates/ 建立新 template schema
   → 定義 sections / ai_field_map / labels / style_roles / block_types

2. 更新 ai.js CATEGORY_ADDONS
   → 新 category 的 prompt 對齊模板欄位

3. 在 delivery-renderer.js 建立新 renderer
   → 參考 renderProductDeliveryTemplate 架構

4. 在 TEMPLATE_REGISTRY 加入新 renderer
   TEMPLATE_REGISTRY['MRL_Delivery_Template_Decision_v1'] = renderDecisionDeliveryTemplate;

5. 在 templateIdFromCategory 加入映射
   decision: 'MRL_Delivery_Template_Decision_v1'

6. renderResult 不需要改。
```

---

## 四、未來 Generator 接入點

當系統進入「pack generator / core generator」階段時，
delivery-renderer.js 的 registry 可以改為：

```js
// 從後端動態載入 template 定義
async function loadTemplate(templateId) {
  const def = await fetch(`/api/template/${templateId}`).then(r => r.json());
  return def;
}
```

這樣前端不再硬編碼 template 定義，
而是從後端 API 取得 → 真正的 template-as-data。

第十三包是這條路的起點。

---

*origin_signature: MrLiouWord*
