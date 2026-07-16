# MRL_Delivery_Template_Product_v1
> origin_signature: MrLiouWord  
> template_id: MRL_Delivery_Template_Product_v1  
> phase: 第十三包  
> category: product

---

## 一、模板目標

把一個使用者對「做產品 / 做網站」的混亂問題，
轉化成一份可以直接開始執行的**第一版產品方案**。

這個模板不生成通用建議，它生成：
- 核心判斷（先做什麼）
- 第一版範圍（包含 / 不包含什麼）
- 執行順序（Step by Step）
- 先做 vs 先不做（排除項）
- 下一步建議（完成後往哪走）

---

## 二、模板 ID 與基本資訊

```
template_id: MRL_Delivery_Template_Product_v1
category:    product
version:     1.0
origin:      MrLiouWord
description: 第一版產品 / 網站方案交付模板
```

---

## 三、各 Section 定義

| Section key | 標籤 | AI 來源 | 說明 |
|------------|------|--------|------|
| `core_judgment` | 核心判斷 | `summary` | 一句話說清楚「第一版真正該做的事」 |
| `problem_breakdown` | 問題拆解 | `breakdown` | 三個讓第一版卡住的真正原因 |
| `first_version_scope` | 第一版範圍建議 | `directions` | 包含什麼、不包含什麼 |
| `execution_steps` | 執行順序 | `steps` | 先做 A → 再做 B → 再接 C |
| `do_vs_not_do` | 先做 vs 先不做 | `priorities` | 排除項同等重要 |
| `next_actions` | 下一步建議 | `supplements` | 完成後往哪走 |
| `common_failures` | 常見失敗原因 | `warning` | 第一版最常失敗的原因 |
| `delivery_footer` | （靜態）| null | 「這份方案可以直接拿去用」 |

---

## 四、前端呈現對應

| Section | Style Role | 前端 CSS class | 視覺效果 |
|---------|-----------|--------------|---------|
| `core_judgment` | `accent` | `result-block--accent` | 金色左邊框 + 背景色 |
| `problem_breakdown` | `doc_section` | `result-block` | 標準文件區塊 |
| `first_version_scope` | `doc_section` | `result-block` | 標準 |
| `execution_steps` | `step_list` | `result-block` + numbered | 有序清單 |
| `do_vs_not_do` | `contrast_warning` | `result-block--warn` | 橘色左邊框 |
| `next_actions` | `doc_section` | `result-block` | 標準 |
| `common_failures` | `failure_warning` | `warning-block--product` | 金色左邊框 + ⚠ 標記 |
| `delivery_footer` | `footer_cta` | `product-result-footer` | 交付說明 footer |

---

## 五、Partial vs Full 顯示規則

| 顯示模式 | 顯示的 sections |
|--------|---------------|
| Partial（未付款）| `core_judgment` + `problem_breakdown` + `first_version_scope`（只給第一個）|
| Full（付款後）| 所有 sections |

---

## 六、為什麼這樣設計會有交付感

1. **標頭讓人知道拿到的是什麼**：「你的第一版產品方案」比「分析結果」更像商品
2. **結構固定可預期**：每次拿到的東西格式相同，不像聊天
3. **核心判斷在最前**：給人「被看穿了」的感覺，建立信任
4. **先不做的事單獨列出**：這是傳統建議書沒有的內容，是真正的產品顧問思維
5. **Footer 說明這份東西能拿去做什麼**：降低「看完然後呢」的疑慮

---

*origin_signature: MrLiouWord*
