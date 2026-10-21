# MRL_Product_v1 首頁文案聚焦規範（第一輪）
> origin_signature: MrLiouWord  
> phase: 第十包 · 首頁收斂  
> primary_category: product

---

## 目前首頁的文案架構

### Hero 區塊
```
eyebrow：產品 / 系統 / 決策 · 拆成能動手做的方案
h1：     把你的產品想法丟進來，我幫你整理成第一版可執行方案
sub：    想做第一版網站或產品卻不知從哪開始？卡在幾個方向不知怎麼選？
         丟進來，幫你拆成問題拆解、方案、步驟、優先順序，直接能動手做。
CTA：    整理我的第一版方案  →  /app.html?cat=product
```

### usecase 卡順序
```
1. 🌐 做網站 / 做產品  [主打]    →  /app.html?cat=product
2. 🔀 決策排序         [備選]    →  /app.html?cat=decision
3. ⚙️ 系統收斂                   →  /app.html?cat=system
4. 💡 商業模式                   →  /app.html?cat=business
5. 📄 內容整理                   →  /app.html?cat=content
```

### 底部 CTA
```
標題：先把你的問題丟進來看看
描述：想做產品或網站，不知道第一版怎麼切？先幫你整理出可執行的第一步。
CTA： 整理我的第一版方案  →  /app.html?cat=product
```

---

## 文案設計原則

### 1. h1 要說「什麼人的什麼問題」
現在的 h1 明確指向：有「產品 / 網站想法」的人
不是泛泛說「問題」

### 2. sub 要點出「兩種人」
- 做產品 / 網站但不知從哪開始 → primary_category = product
- 卡在幾個方向不知怎麼選 → secondary_category = decision
這樣兩種主要使用者都能感覺「這是給我的」

### 3. CTA 要用「動作 + 可預期的結果」
❌ 「立即開始」（太泛，不知道開始什麼）
✅ 「整理我的第一版方案」（知道會拿到什麼）

---

## 首頁優化判斷規則

### 何時改 h1
- 連續 2 週 home_to_app < 15%
- 且已確認 usecase 順序沒問題

### 何時改 CTA 文案
- CTA 點擊率低，但 usecase 卡點擊率高
- 表示人對情境感興趣，但主 CTA 沒有吸引力

### 何時改 usecase 卡順序
- `/admin/category` 顯示某 category 的 heat_score 持續比 product 高
- 且連續 2 週如此
- 此時更換 primary_category 並調整順序

### 不要因為這些原因改首頁
- 你覺得文案可以更好（先看數據）
- 一週的訪客數波動
- 有人說「這個首頁不夠酷」（酷不是目標，轉換是目標）

---

## usecase 卡的視覺規則

```css
/* 主打卡 */
.usecase-card--primary {
  border-color: rgba(232,184,75,0.3);   /* 金色邊框 */
  background: gradient → accent-dim;
  title 後有「主打」badge
}

/* 備選卡 */
.usecase-card--secondary {
  border-color: rgba(232,184,75,0.15);  /* 淡金邊框 */
  無 badge
}

/* 其他卡 */
.usecase-card {
  標準樣式
}
```

---

## 當前文案 vs 改版前對照

| 元素 | 改版前 | 改版後（第十包）|
|------|-------|----------------|
| h1 | 把你的問題丟進來，我幫你整理成可執行方案 | 把你的產品想法丟進來，我幫你整理成第一版可執行方案 |
| sub | 從混亂想法、卡住的決策，到產品... | 想做第一版網站或產品卻不知從哪開始？卡在幾個方向... |
| 主 CTA | 立即開始 | 整理我的第一版方案 |
| CTA URL | /app.html | /app.html?cat=product |
| usecase 第 1 | 做網站 / 做產品 | 做網站 / 做產品（主打 badge）|
| usecase 第 2 | 系統收斂 | 決策排序 |
| 底部 CTA | 立即試用 | 整理我的第一版方案 |

---

## 下次可調整的備選文案（待數據支持再換）

### h1 備選 A（decision 升為主打時）
```
把你卡住的決策丟進來，我幫你排出先做什麼
```

### h1 備選 B（更強力 product 聚焦）
```
你的產品想法，需要的不是建議，而是一份能執行的方案
```

### CTA 備選
```
→ 「拆解我的產品第一步」
→ 「先整理，再開始做」
→ 「把混亂變成步驟」
```

---

*origin_signature: MrLiouWord*
