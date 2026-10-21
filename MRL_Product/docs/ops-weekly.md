# MRL_Product_v1 每週運維流程
> origin_signature: MrLiouWord  
> 每週花 20–30 分鐘，整理數據、找出優化點、決定下週行動

---

## 每週固定流程（建議週一執行）

### Step 1：取得上週完整數據（5 分鐘）

```bash
# 完整數據摘要
bash /opt/mrl_product_v1/app/scripts/show-metrics.sh

# 漏斗細節
curl -s "http://localhost/admin/funnel?days=7" \
  -H "X-Admin-Key: YOUR_ADMIN_KEY" | python3 -m json.tool

# 近期訂單
curl -s "http://localhost/admin/orders?limit=20" \
  -H "X-Admin-Key: YOUR_ADMIN_KEY" | python3 -m json.tool
```

---

### Step 2：填寫本週週報（10 分鐘）

複製以下模板，每週填一份（可存成 md 文件）：

```markdown
# MRL_Product_v1 週報 YYYY-WW
> 週期：MM/DD – MM/DD

## 數據
| 指標 | 本週 | 上週 | 變化 |
|------|------|------|------|
| 首頁訪問 |  |  |  |
| App 進入 |  |  |  |
| 分析成功 |  |  |  |
| 付款成功 |  |  |  |
| 結果解鎖 |  |  |  |
| 週營收 NT$ |  |  |  |
| 訂閱人數 |  |  |  |

## 漏斗轉換率
- 首頁→App：__%
- App→分析：__%
- 分析→付款：__%
- 付款→解鎖：__%
- 整體轉換：__%

## 本週觀察
- 最常見的問題類型：
- 哪個環節流失最多：
- 有無 webhook 異常：
- 有無客訴或異常訂單：

## 下週優化決定（只選 1–2 件）
- [ ] 
- [ ] 

## 備忘
```

---

### Step 3：套用優化決策規則（5 分鐘）

根據漏斗數據做出**只選一個**的優化決定：

```
首頁訪問多，但 App 進入率 < 20%
→ 優化首頁 CTA 文案

App 進入多，但分析率 < 30%
→ 優化輸入框、placeholder、範例問題

分析多，但付款率 < 5%
→ 優化 partial_result 質量 or pricing 呈現

付款後，解鎖率 < 95%
→ 檢查 webhook / confirmation 流程

解鎖多，但無回訪
→ 考慮 email 跟進 or 引導再分析
```

---

### Step 4：執行一件優化（週內完成）

**優化 A：partial_result 質量**

調整 `backend/modules/ai.js` 的 SYSTEM_PROMPT，讓分析更有深度：
- summary 要讓人感到「問題被看透了」
- breakdown 要具體（不能是泛泛而談）
- directions[0]（唯一顯示的方向）要夠誘人

測試方式：自己輸入幾個真實問題，看 partial 是否讓你想付費解鎖。

**優化 B：首頁 CTA**

修改 `frontend/index.html` 的 Hero 區塊文案。
A/B 測試：改完後觀察一週，看 App 進入率是否上升。

**優化 C：pricing 呈現**

在 `frontend/pricing.html` 標記「推薦方案」（月費），讓使用者有錨點。

---

### Step 5：對帳檢查（2 分鐘）

```bash
# 確認有無 paid 但未解鎖的訂單
curl -X POST http://localhost/admin/reconcile \
  -H "X-Admin-Key: YOUR_ADMIN_KEY" | python3 -m json.tool
```

---

## 關鍵 KPI 目標（第一個月）

| KPI | 目標 | 現況 |
|-----|------|------|
| 每日首頁訪問 | ≥ 50 | — |
| App 進入率 | ≥ 30% | — |
| 分析成功率 | ≥ 50% | — |
| 付款率（分析→付款） | ≥ 5% | — |
| 第一筆付款 | 儘快 | — |
| 第一位陌生付款者 | 第一個月內 | — |
| 月費訂閱數 | ≥ 1（第一月） | — |

---

## 第一輪優化決策框架

```
觀察（1週數據）
    ↓
找出最大流失點（哪個環節轉換最低）
    ↓
只選一個優化方向（不同時做多個）
    ↓
執行（改 prompt / 改文案 / 改 UI）
    ↓
等一週再看數據
    ↓
重複
```

---

*origin_signature: MrLiouWord*
