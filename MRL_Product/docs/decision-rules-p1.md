# MRL_Product_v1 第一輪決策收斂規則
> origin_signature: MrLiouWord  
> phase: 第九包 · 數據驅動決策  
> 用途：每週決策依據，不靠感覺

---

## 核心原則

```
先看趨勢（7 天），不看單點（今天）
先看轉換（有沒有付錢），不只看流量（有沒有人來）
先收斂主打（選 1–2 個），不要平均發展
```

---

## 一、category 熱度判讀

**數據來源：** `/admin/category` → `analyzes` 欄 + `heat_score`

| heat_score | 解讀 | 行動 |
|-----------|------|------|
| ≥ 70 | 這類問題需求最強 | 作為主要導流方向 |
| 40–69 | 有需求，值得投入 | 持續發內容 |
| 20–39 | 有一些人用，但不夠多 | 先觀察，不主打 |
| < 20 | 太少人用 | 暫不主打 |

**注意**：heat_score 是相對值，會隨其他 category 成長而變化。

---

## 二、unlock_rate 判讀（partial → 付款點擊）

**數據來源：** `/admin/category` → `click_rate`

| click_rate | 解讀 | 行動 |
|-----------|------|------|
| ≥ 10% | Partial 很吸引人 | 不要動，保持 |
| 5–9.9% | 尚可，有優化空間 | 可嘗試改鎖定文案 |
| 2–4.9% | Partial 不夠吸引 | 需改 directions[0] 力度 |
| < 2% | Partial 幾乎沒用 | 需重新檢視 partial 切法 |

**注意**：click_rate 低不一定是文案問題，也可能是問題類型本身的付費意願低。

---

## 三、payment_rate 判讀（付款點擊 → 解鎖）

**數據來源：** `/admin/category` → `unlock_rate`（實際是解鎖 / 點擊）

| unlock_rate | 解讀 | 行動 |
|------------|------|------|
| ≥ 80% | 付款流程正常 | — |
| 50–79% | 有流失，可接受 | 確認 Stripe 沒報錯 |
| < 50% | 嚴重流失 | 立即確認 webhook / success 流程 |

**注意**：unlock_rate 低通常是技術問題，不是文案問題，先查 `/admin/errors`。

---

## 四、主打 category 決策邏輯

### 規則 A：選出主打候選

系統自動標記 `recommendation = '主打候選'` 的條件：
```
heat_score ≥ 40
AND click_rate ≥ 5%
```

人工確認：
- 這個 category 的問題類型，你有能力持續產製導流內容嗎？
- 這個 category 的 partial_result 質量，你覺得夠好嗎？
- 如果是，確認為主打，加碼發內容

---

### 規則 B：需優化才能成為主打

系統標記 `'需優化 partial'` 的條件：
```
heat_score ≥ 40
AND click_rate < 5%
```

行動順序：
1. 看這個 category 的 partial_result 質量（自己試幾次）
2. 調整 `backend/modules/ai.js` 的 SYSTEM_PROMPT，讓 directions 更有力
3. 改 `frontend/app.html` 的鎖定區塊文案
4. 等一週再看 click_rate 是否上升

---

### 規則 C：低流量高潛力 category

系統標記 `'需增加流量'` 的條件：
```
heat_score < 40
AND click_rate ≥ 10%
```

解讀：這類問題雖然人少，但進來的人更容易付錢。  
行動：把導流資源往這個 category 移，多發對應內容。

---

### 規則 D：放棄或延後 category

系統標記 `'暫不主打'` 的條件：
```
heat_score < 20
```

行動：
- 保留 category，不要刪除
- 不投入導流資源
- 三週後再看一次，若仍低則確認放棄主打

---

## 五、漏斗最大流失點決策

**數據來源：** `/admin/funnel` → `_diagnosis`

| 最大流失點 | 應優先改 | 不要動 |
|----------|---------|--------|
| 首頁 → App | index.html Hero / CTA | app.html |
| App → 分析 | category chips / example prompts | index.html |
| 分析 → 付款 | partial_result 切法 / 鎖定文案 | pricing.html |
| 付款 → 解鎖 | webhook / confirmation 技術流程 | 前端文案 |

---

## 六、第一輪收斂決策樹

```
第一批數據來了（≥ 7 天，≥ 20 次分析）
│
├── 有「主打候選」category？
│   ├── 有 → 主打它，加碼導流
│   └── 沒有 → 找 heat_score 最高的 category
│                └── click_rate < 5% → 先優化 partial
│
├── funnel 最大流失點在哪？
│   ├── 首頁 → App → 改首頁 CTA
│   ├── App → 分析 → 改 example prompts
│   ├── 分析 → 付款 → 改 partial / 鎖定文案
│   └── 付款 → 解鎖 → 查技術問題
│
└── 本週只做一件事（從上面選）
    等一週再看數據
    重複
```

---

## 七、數據不足時的判斷基準

若 7 天內訪客 < 20 人，數據統計意義不大。此時：

```
不看轉換率（太少樣本）
只看：有沒有人 analyze？有沒有人付款？
```

**行動：**
- 有付款 → 系統正常，加強導流
- 無付款但有分析 → partial 可能需要調整
- 無分析 → 先確認系統正常，再看導流入口

---

## 八、不要做的事

```
❌ 每天看數字然後亂改
❌ 同一週改多個地方然後不知道哪個有用
❌ 因為一兩次付款就認定某 category 是主打
❌ 因為流量少就認為產品沒用
❌ 在數據不足時做大改版決定
```

```
✅ 每週只做一個改動
✅ 改完等一週再看
✅ 只根據連續趨勢做判斷
✅ 先確認技術正常，再談文案優化
```

---

*origin_signature: MrLiouWord*
