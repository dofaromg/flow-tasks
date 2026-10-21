# MRL_Product_v1 第一輪日常營運觀測清單
> origin_signature: MrLiouWord  
> phase: 第九包 · 第一批真實流量判讀  
> 前提：已有真實訪客與分析事件

---

## 每日觀測（5 分鐘）

**開 `/admin.html` 看兩件事：**

### 1. 今日數據卡片
| 指標 | 正常 | 異常訊號 |
|------|------|---------|
| 首頁訪問 | > 0 | 連續 2 天 0 → 檢查 DNS / Nginx |
| App 進入 | > 0 | 有首頁訪問但 0 app → CTA 問題 |
| 分析成功 | ≥ 1 | 有 app 訪問但 0 分析 → input 問題 |
| 付款成功 | 任意值 | — |
| 錯誤數 | = 0 | > 0 → 看 `/admin/errors` |

### 2. 決策摘要區塊（Overview 最頂部）
- **主打候選**：今日哪個 category 被標記為主打
- **最大流失點**：目前哪個階段轉換最低
- **優先行動**：系統建議先改什麼

**每日只需要做一件事**：確認系統正常，有無付款異常。

```bash
# 或用腳本快速確認
bash /opt/mrl_product_v1/app/scripts/daily-check.sh
```

---

## 每 3 天觀測（10 分鐘）

**開 `/admin.html` → 問題分類 tab**

看 category 表格的這三列：

| 欄位 | 看什麼 |
|------|--------|
| 分析次數 | 哪個 category 最多人在用 |
| 點擊率 | 哪個 partial 最能讓人想付錢 |
| 建議 | 系統給的第一輪判斷 |

**判讀重點：**
- 有「主打候選」→ 這個 category 值得加碼導流內容
- 有「需優化 partial」→ 這個 category 的分析結果不夠吸引人
- 有「需增加流量」→ 這個 category 成交率高但人少，值得專注

---

## 每週決策（20 分鐘）

### Step 1：看 funnel 診斷
**開 `/admin.html` → 漏斗 tab**

| 最大流失在哪？ | 意思 | 先做什麼 |
|--------------|------|---------|
| 首頁 → App | 首頁無法驅動進入 | 改 Hero 文案 / CTA |
| App → 分析 | 進來了但不知道怎麼輸入 | 改 example prompts / category 文案 |
| 分析 → 付款 | Partial 沒吸引力 | 改鎖定區塊文案 / partial 切法 |
| 付款 → 解鎖 | 付款流程有問題 | 確認 webhook / success 頁流程 |

### Step 2：看 category 表現
**問題分類 tab**，找到最高熱度 category

- 是「主打候選」→ 這週多發一篇該 category 的導流內容
- 是「需優化 partial」→ 這週改一個 example prompt 或 partial 文案
- 是「需增加流量」→ 這週加一條指向該 category 的 URL 導流

### Step 3：只做一件事
從 Step 1 + Step 2 各選出最重要的一件，**只做一件**：

```
本週只做：
□ 改一個 category 的 example prompts
□ 改一段 partial 鎖定區塊文案
□ 多發一篇對應 category 的社群貼文
□ 修一個 funnel 流失點的頁面
```

不要一週亂改很多東西。

---

## 哪些情況該改首頁

| 症狀 | 指標 | 行動 |
|------|------|------|
| 首頁進入率持續 < 15% | `home_to_app < 15%` | 改 Hero 文案，讓第一句話更直接 |
| 有流量無點擊 | page_view_home 多但 app_view 少 | 改 CTA 按鈕文案，或改熱門情境卡順序 |
| 不同 category 來源流失相近 | 全部 category 都低 | 首頁問題，不是個別 category 問題 |

**改首頁的位置：** `frontend/index.html` → Hero 區塊 + 熱門情境卡

---

## 哪些情況該改 partial

| 症狀 | 指標 | 行動 |
|------|------|------|
| 分析多但付款少 | `analyze_success` 高但 `pay_click_once` 低 | partial 不夠吸引，改鎖定區塊文案 |
| 特定 category 點擊率特別低 | 某 category click_rate < 2% | 改該 category 的 AI prompt，讓 directions[0] 更有力 |
| 使用者進入後馬上離開 | app 停留時間短（若有記錄） | partial 質量問題，改 ai.js prompt |

**改 partial 的位置：**
- 文案：`frontend/app.html` → lock-block 區塊
- 切法：`backend/modules/partial_output.js`
- AI 輸出：`backend/modules/ai.js` → SYSTEM_PROMPT

---

## 哪些情況該加流量

| 症狀 | 指標 | 行動 |
|------|------|------|
| 某 category 解鎖率高但分析少 | unlock_rate 高但 analyzes 少 | 多做該 category 的導流內容 |
| 整體訪客少 | page_view_home < 20/天 | 增加社群貼文頻率 |
| 某 category 付款率最高 | payment_rate 最高 | 主攻該 category 的短影片 |

**加流量的方式：**
- 短影片：用 `docs/traffic-p1.md` 的 Script 模板
- 社群：用 `docs/traffic-p1.md` 的貼文模板
- URL：全部加 `?cat=XXX` 帶 category

---

*origin_signature: MrLiouWord*
