# MRL Template Rendering Rules（第一版）
> origin_signature: MrLiouWord  
> phase: 第十三包

---

## 一、三層架構

```
Data Layer      →  語義欄位（section names）
Render Layer    →  欄位對應的渲染規則（blockType + container）
Style Role Layer →  視覺角色（與 CSS class 解耦）
```

**原則：即使 CSS class 改名，style role 定義不變。**

---

## 二、Data Layer（欄位定義）

每個 template 的 Data Layer 由一組 `section` 定義：

```js
{
  key:       'core_judgment',     // 語義識別鍵
  label:     '核心判斷',           // 前端顯示標籤
  styleRole: 'accent',            // 視覺角色
  blockType: 'text',              // 內容類型：text / list / numbered / footer
  aiField:   'summary',           // 對應 AI 輸出的欄位名（null = 靜態）
}
```

---

## 三、Render Layer（渲染規則）

`delivery-renderer.js` 負責：

1. 接收 `templateId` + `rawResult` + `isPartial`
2. 從 `TEMPLATE_REGISTRY` 找到對應 renderer
3. 依 `sections` 定義，逐欄位從 `rawResult` 取資料
4. 依 `blockType` 決定怎麼建 DOM
5. 依 `styleRole` 套對應 CSS class

```js
// 分派入口
renderDeliveryTemplate(templateId, rawResult, isPartial)
  → TEMPLATE_REGISTRY[templateId](rawResult, isPartial)
  → renderProductDeliveryTemplate(rawResult, isPartial)
```

---

## 四、Style Role Layer

| Style Role | CSS 對應 | 視覺語義 |
|-----------|---------|---------|
| `accent` | `result-block--accent` | 最重要內容，金色強調 |
| `doc_section` | `result-block` | 標準文件段 |
| `step_list` | `result-block` + numbered | 有序執行清單 |
| `contrast_warning` | `result-block--warn` | 對比警示（先做/先不做）|
| `failure_warning` | `warning-block--product` | 失敗原因警告 |
| `footer_cta` | `product-result-footer` | 交付物 footer |

---

## 五、Product Template Render 規則

```
1. 讀取 templateId = 'MRL_Delivery_Template_Product_v1'
2. 分派到 renderProductDeliveryTemplate(result, isPartial)
3. isPartial = true → 只顯示前三個 sections
4. isPartial = false → 顯示全部 + header + footer
5. sections 順序固定（core_judgment 永遠第一）
6. common_failures（warning）特殊處理：插到 doc 之後
```

---

## 六、如何接入新 Template

```js
// 1. 建立新 template 定義（sections 定義）
const DECISION_TEMPLATE_DEF = { ... };

// 2. 建立 renderer 函式
function renderDecisionDeliveryTemplate(rawResult, isPartial) { ... }

// 3. 加入 registry
TEMPLATE_REGISTRY['MRL_Delivery_Template_Decision_v1'] = renderDecisionDeliveryTemplate;

// 4. 加入 templateIdFromCategory 映射
const map = {
  product:  'MRL_Delivery_Template_Product_v1',
  decision: 'MRL_Delivery_Template_Decision_v1',  // ← 新增
};
```

**不需要改 renderResult。** `renderResult` 只需要知道 templateId，剩下的交給 registry。

---

## 七、Fallback 規則

若 `templateId` 不在 registry，或 `templateIdFromCategory` 返回 null：
→ 走 `renderResult` 的 fallback 邏輯（原始 if/else 區塊）

確保任何 category 都不會因為「沒有 template」而壞掉。

---

*origin_signature: MrLiouWord*
