# MRL_Product_v1 主打 Category 決策（第一輪）
> origin_signature: MrLiouWord  
> phase: 第十包 · 主打收斂  
> 更新時機：每次 recommendation 有重大變化時更新

---

## 目前設定

```
PRIMARY   (主打)：product    — 做網站 / 做產品
SECONDARY (備選)：decision   — 決策排序
LOW_PRIORITY：   system, business, content（保留，不主打）
```

---

## 為什麼選 product 作為第一主打

### 1. 需求最普遍且可視覺化
「我想做一個網站 / 產品但不知道怎麼開始」
→ 這是最常見的起點，幾乎任何行業都有這個問題
→ 容易做短影片展示結果（Before: 混亂想法 → After: 清楚步驟）

### 2. 付費意願最強
有明確可交付物（第一版方案 / 執行步驟）
→ 使用者容易判斷「這份結果值 NT$299」
→ 比「幫我決策」更容易感受到具體價值

### 3. 與產品本身故事最對齊
MRL_Product_v1 本身就是這樣被建立出來的：
把一個產品想法拆成可執行方案
→ 創辦人 story 可以直接作為導流素材

### 4. 容易做持續內容
「做產品 / 做網站的第 N 步」系列
→ 每個痛點都可以做一支短影片
→ 長期內容主線清晰

---

## 為什麼選 decision 作為備選

- 問題類型普遍（每個人都在做決策）
- 不限行業（比 product 更廣）
- 適合作為 product 系列的補充（「做產品前要先決定方向」）
- 付費意願次之，但使用頻率可能更高

---

## 數據追蹤欄位（每週更新）

| 週次 | product heat | product click_rate | decision heat | decision click_rate | 備註 |
|------|-------------|-------------------|--------------|---------------------|------|
| 第 1 週 | — | — | — | — | 收集中 |
| 第 2 週 | — | — | — | — | — |

---

## 何時更換主打

### 觸發升級 secondary → primary 的條件
- decision 的 click_rate 連續 2 週 > product
- decision 的 payment_success 超過 product

### 觸發主打替換的條件
- 新 category 的 heat_score 連續 2 週排第一
- 且 click_rate ≥ 5%

### 不要因為這些原因換主打
- 一週的異常數據
- 個人感覺這個 category 比較好
- 沒有連續 2 週以上的趨勢支撐

---

## 主打 category 的影響範圍

| 位置 | 目前設定 | 說明 |
|------|---------|------|
| index.html Hero 主標題 | 「把你的產品想法丟進來」 | 偏向 product |
| index.html Hero 副標題 | 含「產品 / 網站」 | product + decision |
| index.html 主 CTA | 「整理我的第一版方案」 | product 語氣 |
| index.html usecase 卡順序 | product 第一、decision 第二 | — |
| app.html 預設 category | product（無 URL 參數時） | — |
| app.html product chip | 有「主打」badge | — |
| pricing.html 單次描述 | 含「產品 / 網站想法」 | — |
| pricing.html 月費描述 | 含「持續整理產品方向」 | — |
| admin 決策摘要 | PRIMARY = 分析最多 category | 動態 |

---

## 更換主打時需要同步修改的地方

```
1. docs/primary-category-p1.md  → 更新本文件
2. docs/homepage-focus-p1.md    → 更新首頁文案方向
3. frontend/index.html          → Hero 文案 + usecase 排序
4. frontend/assets/app.js       → readUrlParams 的 defaultCat
5. frontend/app.html            → cat-chip--primary 套到新主打
6. frontend/pricing.html        → tagline 改為新主打情境
```

---

*origin_signature: MrLiouWord*
