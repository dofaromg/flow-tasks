# MRL_ProductPack_v1 定義
> origin_signature: MrLiouWord  
> phase: 第十五包

---

## 一、ProductPack 是什麼

ProductPack 是一個針對**某個具體問題**所生成的最小產品交付包。

它不是程式碼，是**結構化規格**：

```
一個問題
  → 一份分析（Core_Generator）
  → 一個 Pack（Pack_Generator）
     ├── 核心判斷（用一句話說清楚）
     ├── 第一版範圍（包含 / 不包含什麼）
     ├── 頁面清單（每頁名稱 / 用途 / 優先級）
     ├── 使用者流程（Step 1 → Step 2 → ...）
     ├── 執行順序（先做什麼）
     ├── 先做 vs 先不做
     ├── 收費模式草案
     └── 部署配置草案
```

---

## 二、ProductPack 的層

| 層 | 名稱 | 狀態 |
|---|------|------|
| Layer A | Pack Spec（結構化描述）| ✅ 第十五包完成 |
| Layer B | Pack Scaffold（前後端骨架）| 🔜 第十六包 |

---

## 三、Pack Schema 欄位

| 欄位 | 類型 | 說明 |
|------|------|------|
| `pack_id` | string | `mrl_pack_` + 12 位 hex |
| `analysis_id` | string | 來源 analysis |
| `pack_type` | string | 'product' |
| `template_id` | string | 'MRL_Delivery_Template_Product_v1' |
| `category` | string | 'product' |
| `mode` | string | website / mvp / payment / converge |
| `title` | string | 從 core_judgment 推導 |
| `summary` | string | 一句話摘要 |
| `core_judgment` | string | 第一版真正該做的事 |
| `first_version_scope` | array | 第一版包含什麼 |
| `execution_steps` | array | 先做 A → 再做 B |
| `do_vs_not_do` | array | 優先 / 暫緩 |
| `next_actions` | array | 完成後的建議 |
| `common_failures` | string | 常見失敗原因 |
| `pages` | array | 頁面清單（name / purpose / priority） |
| `flows` | array | 使用者旅程（8 步）|
| `pricing_model` | object | 收費模式草案 |
| `deployment` | object | 部署配置草案（target / stack / env / volumes）|
| `result` | object | 來源 normalized result |
| `meta` | object | generated_at / problem_text / session_id |

---

## 四、ProductPack vs Delivery Template 的差異

| 面向 | Delivery Template | ProductPack |
|------|------------------|-------------|
| 本質 | 輸出**呈現**規則 | 輸出**規格**文件 |
| 位置 | 前端 renderer | 後端 storage/packs/ |
| 用途 | 讓使用者看到方案 | 讓實作者按圖施工 |
| 格式 | DOM fragment | JSON 檔 |
| 包含 | 視覺區塊 | 頁面 / 流程 / 部署配置 |

---

## 五、支援的 Modes

| Mode | 說明 | 預設頁面重點 |
|------|------|------------|
| `website` | 做第一版網站 | index + app + pricing + success 均為 high |
| `mvp` | 做第一版產品 | 同上 |
| `payment` | 做收費入口 | pricing 升為 critical |
| `converge` | 產品收斂 | product 頁降為 low |

---

*origin_signature: MrLiouWord*
