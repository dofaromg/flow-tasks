# MRL_Core_Generator 各子模組職責
> origin_signature: MrLiouWord  
> phase: 第十四包

---

## 入口：`core/generator/index.js`

```
Generator.analyze({ problemText, category, isPartial, ... })
  → { rawResult, payload }
```

統一串接以下五個子模組，api.js 只需要呼叫這一個。

---

## 1. PromptBuilder

**位置：** `backend/core/generator/prompt-builder.js`

**職責：** 組裝 system prompt

| 輸入 | 輸出 |
|------|------|
| `{ category, extraContext? }` | `string` (system prompt) |

**核心 API：**
```js
buildSystemPrompt({ category })
getCategoryAddon(category)
getSupportedCategories()
```

**設計原則：**
- `BASE_PROMPT` 定義固定結構（JSON 格式 + 規則）
- `CATEGORY_ADDONS` 各類別的額外偏重指引
- 兩者拼接成最終 prompt，保持可讀性

---

## 2. AnalyzeEngine（ai.js）

**位置：** `backend/modules/ai.js`

**職責：** 呼叫 AI 模型，取得 raw output

| 輸入 | 輸出 |
|------|------|
| `(problemText, category)` | `Promise<object>` (raw AI result) |

**設計原則：**
- ai.js 只負責模型呼叫
- prompt 組裝委託給 PromptBuilder
- 解析 JSON，回傳 parsed object

---

## 3. ResultNormalizer

**位置：** `backend/core/generator/result-normalizer.js`

**職責：** 將 AI raw output 映射為 template 標準欄位

| 輸入 | 輸出 |
|------|------|
| `(rawResult, category)` | `normalizedData | null` |

**核心 API：**
```js
normalizeResult(rawResult, category)
hasNormalizer(category)
getNormalizedCategories()
```

**映射規則：**
```
AI field       → Template section
summary        → core_judgment
breakdown      → problem_breakdown
directions     → first_version_scope
steps          → execution_steps
priorities     → do_vs_not_do
supplements    → next_actions
warning        → common_failures
```

---

## 4. TemplateSelector

**位置：** `backend/core/generator/template-selector.js`

**職責：** 根據 category 選出對應的 template_id

| 輸入 | 輸出 |
|------|------|
| `{ category, mode?, planType? }` | `string | null` |

**核心 API：**
```js
selectTemplate({ category })
isTemplateAvailable(templateId)
getAvailableTemplates()
getCategoryTemplateMap()
```

**擴充方式：**
```js
CATEGORY_TEMPLATE_MAP = {
  product:  'MRL_Delivery_Template_Product_v1',
  decision: 'MRL_Delivery_Template_Decision_v1',  // ← 加這行
}
```

---

## 5. Composer

**位置：** `backend/core/generator/composer.js`

**職責：** 組裝最終 response payload，供前端 renderer 使用

| 輸入 | 輸出 |
|------|------|
| `{ analysisId, problemText, rawResult, normalizedResult, templateId, isPartial, category, meta }` | `payload object` |

**標準 payload 格式：**
```json
{
  "analysis_id":    "...",
  "category":       "product",
  "template_id":    "MRL_Delivery_Template_Product_v1",
  "is_partial":     false,
  "requires_payment": false,
  "problem_text":   "...",
  "result":         { ...normalized data... },
  "meta": {
    "generated_at": "2026-...",
    "plan_type":    "subscription"
  }
}
```

---

## 各子模組職責邊界

```
PromptBuilder     → 只管 prompt 文字
AnalyzeEngine     → 只管 AI 呼叫
ResultNormalizer  → 只管 raw → template data 的映射
TemplateSelector  → 只管 category → template_id 的決策
Composer          → 只管 response payload 的組裝

api.js            → 只管 HTTP 請求 / DB / events / 追蹤
                    不再含 prompt 邏輯 / normalize 邏輯 / template 選擇邏輯
```

---

*origin_signature: MrLiouWord*
