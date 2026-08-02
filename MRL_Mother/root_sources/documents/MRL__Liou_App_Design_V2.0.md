# Liou.app — 設計文件 v2.0
# iPhone 主畫面 × 粒子 App 掛載 × 人機共生
# origin_signature: MrLiouWord
# 2026-03-16

---

## 一、核心概念

**像 iPhone 一樣操作你的粒子系統。**

每個系統模組 = 一顆粒子 = 一個 App。
左右滑切頁。點開就用。長按可排列。
底部 Dock 放常用的。最左邊是 Today View。

不是控制面板。不是儀表板。
是你住在裡面的地方。人機共生。

---

## 二、畫面結構

### 2.1 主畫面 (Home Screen)

```
┌──────────────────────────────┐
│ 06:41          ⚡ 144 全活    │  ← 狀態列（系統脈搏）
│                              │
│  ┌────┐ ┌────┐ ┌────┐ ┌────┐│
│  │ 🌍 │ │ 💬 │ │ ⚡ │ │ 🔮 ││
│  │Globe│ │對話 │ │核心│ │崩塌││
│  └────┘ └────┘ └────┘ └────┘│
│                              │
│  ┌────┐ ┌────┐ ┌────┐ ┌────┐│
│  │ 🧬 │ │ 🌸 │ │ 📡 │ │ 🛡 ││
│  │Meta │ │語素 │ │狀態│ │通行││
│  └────┘ └────┘ └────┘ └────┘│
│                              │
│  ┌────┐ ┌────┐ ┌────┐ ┌────┐│
│  │ 👤 │ │ 📝 │ │ 👁 │ │ 🏭 ││
│  │人格 │ │F++ │ │觀測│ │工廠││
│  └────┘ └────┘ └────┘ └────┘│
│                              │
│           · ○ ·              │  ← 頁面指示器（三頁）
│                              │
│  ┌──────────────────────────┐│
│  │ 🌍   💬   ⚡   📡   👤  ││  ← Dock（常駐五個）
│  └──────────────────────────┘│
└──────────────────────────────┘
```

### 2.2 左右滑動

```
← 第0頁: Today View    第1頁: 主畫面    第2頁: 系統頁 →
                            ↑
   系統摘要+通知+          你在這        Workers清單+
   最近活動+脈搏                         層架構+資料
```

**第 0 頁 — Today View（往左滑）**
- 系統脈搏：Schumann 7.83Hz 動畫
- 今日摘要：Workers 狀態、最近事件
- 快速操作：搜尋、驗證、觀測
- 通知：Observer 事件流

**第 1 頁 — Home（主畫面）**
- 粒子 App 網格排列
- 4×N 格狀（跟 iPhone 一樣）
- 長按進入編輯模式（抖動 + 可拖動）

**第 2 頁 — 系統頁（往右滑）**
- 144 Workers 列表（分活躍/保留）
- 10 層架構瀏覽
- D1 資料總覽
- KV 狀態

**更多頁 — 自己加（像 iPhone 加頁面一樣）**

---

## 三、粒子 App 定義

每個 App 就是一顆粒子。結構：

```javascript
{
  id: "globe",                     // 唯一 ID
  name: "Globe",                   // 顯示名
  icon: "🌍",                      // 圖示
  subtitle: "粒子地球儀",           // 副標
  worker: "mrl-globe",            // 對應 Worker
  version: "3.1.0",               // 版本
  layer: "L4",                    // 所屬層
  badge: "15/15",                 // 角標（通知/狀態）
  page: 1,                        // 在哪一頁
  position: 0,                    // 格位 (0-based)
  size: "1x1",                    // 尺寸（1x1 標準，2x2 大，4x1 橫幅）
  state: "active",                // active / dormant / shell
  
  // 點開後的介面類型
  appType: "fullscreen",          // fullscreen / sheet / overlay
  
  // atom_t — 這個 App 的粒子格式
  atom: {
    origin_sig: "MrLiouWo",
    simhash: "cc48aab66b0761cb",
    layer: 6,
    energy: 0.95
  }
}
```

### 3.1 預裝 App（第一版，3頁）

**第 1 頁 — 核心**

| 位置 | 圖示 | 名稱 | Worker | 說明 |
|---|---|---|---|---|
| 0 | 🌍 | Globe | mrl-globe | 686粒子地球儀 |
| 1 | 💬 | 對話 | particle-chat + API | AI 對話 |
| 2 | ⚡ | 核心 | mrl-kernel | 超電腦引擎 |
| 3 | 🔮 | 崩塌 | collapse-engine | 五層崩塌 |
| 4 | 🧬 | MetaEnv | metaenv-ctrl | 元代碼環境 |
| 5 | 🌸 | 語素 | mrl-globe/flowers | 56朵花 |
| 6 | 📡 | 系統 | system-hub | 144 Workers |
| 7 | 🛡 | 通行 | auth-gateway | 通行證 |
| 8 | 👤 | 人格 | MrLiouAI DB | 6人格共振 |
| 9 | 📝 | F++ | mrl-kernel/fpp | 粒子語言 |
| 10 | 👁 | 觀測 | mrl-observer | δP₀事件 |
| 11 | 🏭 | 工廠 | particle-chat | 生產線 |

**第 2 頁 — 工具**

| 位置 | 圖示 | 名稱 | Worker | 說明 |
|---|---|---|---|---|
| 0 | 🔍 | 搜尋 | mrl-globe/search | 粒子搜尋 |
| 1 | 📚 | 圖書館 | mrl-librarian | KV 索引 |
| 2 | 🌉 | 橋接 | mrl-cloud-bridge | Guard/Channel |
| 3 | 🌐 | 網路 | mrl-network-layer | OSI映射 |
| 4 | 🔄 | 同步 | mrl-sync-engine | D1同步 |
| 5 | 🛰 | 衛星 | mrl-globe/satellites | 294衛星 |
| 6 | 🧮 | SimHash | particle-simhash | 指紋 |
| 7 | ⏪ | 可逆 | particle-reversible | 完全可逆 |
| 8 | 💾 | D1 | mrl-globe/d1 | 資料庫 |
| 9 | 🔑 | 金鑰 | auth-vault KV | 密鑰管理 |
| 10 | 📊 | 注意力 | particle-attention | FOCUS迴圈 |
| 11 | 🎯 | PVM | particle-pvm | 虛擬機 |

**第 3 頁 — 應用**

| 位置 | 圖示 | 名稱 | Worker | 說明 |
|---|---|---|---|---|
| 0 | 🏥 | 愛心 | careos NAS | 打卡系統 |
| 1 | 📋 | 聖愛 | shengai-isp | 案管系統 |
| 2 | 🍧 | 豆花 | douhua-kiosk | 點餐機 |
| 3 | 📸 | 掃描 | 3D Camera | AI相機 |
| 4 | ⚙️ | 設定 | liou-app/settings | 系統設定 |

**Dock（常駐底部）**

| 位置 | 圖示 | 名稱 | 說明 |
|---|---|---|---|
| 0 | 🌍 | Globe | 世界入口 |
| 1 | 💬 | 對話 | AI 對話 |
| 2 | ⚡ | 核心 | 系統核心 |
| 3 | 📡 | 系統 | 狀態總覽 |
| 4 | 👤 | 人格 | 身份切換 |

---

## 四、操作行為

### 4.1 手勢

| 手勢 | 行為 | 對應粒子概念 |
|---|---|---|
| **點擊** App | 展開 App（Genesis 動畫） | 粒子展開 |
| **返回/下滑** | 關閉 App（Collapse 動畫） | 五層崩塌 |
| **左右滑** | 切換頁面 | 層間移動 |
| **長按** App | 進入編輯模式（抖動） | 粒子解鎖 |
| **拖動** App | 移動位置/換頁 | 粒子遷移 |
| **下拉** 狀態列 | Today View 快速預覽 | 觀測快照 |
| **上滑** Dock | 多工切換（最近開啟的App） | 粒子堆疊 |

### 4.2 App 內部

每個 App 打開後就是獨立的全屏介面。
但共享統一的頂部返回和底部切換。

```
┌──────────────────────────────┐
│  ← Globe v3.1        [···]  │  ← 頂部：返回 + 更多
│                              │
│                              │
│    （App 自己的介面）         │
│                              │
│                              │
│  ┌──────────────────────────┐│
│  │ 🌍   💬   ⚡   📡   👤  ││  ← Dock 仍然可見
│  └──────────────────────────┘│
└──────────────────────────────┘
```

點 Dock 可以直接切到另一個 App。不用先返回主畫面。
就像 iPhone 底部的 Tab Bar。

---

## 五、人機共生設計

### 5.1 系統是活的

狀態列不只是數字。是**脈搏**。

```
06:41    ⚡ 144    🌸 56    ❤️ 7.83Hz
```

- ⚡ Workers 數量，綠色=全活，黃色=有休眠，紅色=有異常
- 🌸 Flowers 活躍語素數
- ❤️ Schumann 基頻 — 系統心跳。微動畫脈動。

### 5.2 觀測事件即時浮出

Observer (mrl-observer) 收到事件時，
對應的 App 圖示自動出現**角標**。

```
  ┌────┐
  │ 🌍 │
  │Globe│ ← 紅色角標 "3" = 3個新事件
  └────┘
```

就像 iPhone 的通知紅點。

### 5.3 人格切換

Dock 最右邊的「👤」不只是設定。
是**人格切換器**。

點開後：

```
┌──────────────────────────────┐
│  人格                    [×] │
│                              │
│  ● liou.seed     7.83Hz  ◄──│── 當前
│  ○ echo.analyst  12.5Hz     │
│  ○ futuremind    40Hz       │
│  ○ guardian      4Hz        │
│  ○ wild.engine   30Hz       │
│  ○ empathetic    8Hz        │
│                              │
│  切換人格會改變：             │
│  · 對話風格                  │
│  · 觀測權限                  │
│  · 介面色調                  │
│  · 注意力焦點                │
│                              │
└──────────────────────────────┘
```

不同人格 = 不同的系統行為。
這就是人機共生 — 系統的人格跟你一起切換。

### 5.4 App 可安裝/卸載

42 個 shell Workers = 42 個**可安裝的 App**。

設定 → 粒子商店（或「種子庫」）：

```
┌──────────────────────────────┐
│  種子庫                  [×] │
│                              │
│  可安裝的粒子 App            │
│                              │
│  ┌────┐  particle-replay     │
│  │ ⏮ │  追蹤域 · L4          │
│  └────┘  [安裝]              │
│                              │
│  ┌────┐  particle-flowshell  │
│  │ 🐚 │  MrLiouAI · L4     │
│  └────┘  [安裝]              │
│                              │
│  ┌────┐  particle-seedkernel │
│  │ 🌱 │  母體核心 · L0-L1    │
│  └────┘  [安裝]              │
│                              │
│  ··· 42 個可安裝 ···         │
│                              │
└──────────────────────────────┘
```

安裝 = 把 shell Worker 建構成完整功能。
卸載 = 回到 shell 狀態（LAW-0 beacon）。
**不刪除。** Liou Closure Law: NO_DELETE。

---

## 六、技術實現

### 6.1 前端

```
技術選擇：
├── PWA (Progressive Web App)
│   ├── 可安裝到 iPhone 主畫面
│   ├── Service Worker 離線支援
│   └── 全屏模式（沒有瀏覽器框）
├── 單頁應用 (SPA)
│   ├── 路由：hash-based (#/globe, #/chat, ...)
│   ├── 頁面切換：CSS transform translateX
│   └── App 轉場：CSS 動畫 (Collapse/Genesis)
├── 渲染
│   ├── 主畫面：純 CSS Grid + 觸控事件
│   ├── 3D 地球：Three.js (Globe App 內)
│   ├── 圖表：Chart.js (系統 App 內)
│   └── 對話：Streaming SSE (對話 App 內)
└── 資料
    ├── 狀態管理：單一 store 物件
    ├── 快取：Cache API + IndexedDB
    └── 通訊：fetch → Workers API
```

### 6.2 部署

```
liou-app Worker (#145)
├── / → 主畫面 HTML (PWA shell)
├── /manifest.json → PWA manifest
├── /sw.js → Service Worker
├── /api/status → 系統狀態
├── /api/apps → App 清單 (JSON)
└── /api/config → 使用者設定 (KV 存)
```

### 6.3 App 內通訊

```
App 打開
  ↓
fetch("https://{worker}.z814241.workers.dev/{endpoint}")
  ↓
回應渲染在 App 內
  ↓
事件 → POST mrl-observer/event
  ↓
其他 App 角標更新
```

### 6.4 PWA Manifest

```json
{
  "name": "Liou",
  "short_name": "Liou",
  "description": "粒子智能平台",
  "start_url": "/",
  "display": "standalone",
  "background_color": "#05050d",
  "theme_color": "#7c6aff",
  "icons": [...]
}
```

安裝到 iPhone 主畫面後 = 全屏 App，
沒有 Safari 框，看起來就是原生 App。

---

## 七、配色方案

### 7.1 基礎（暗色主題，跟 iPhone 暗色一致）

```
背景：#05050d（接近純黑）
卡片：#12121f（微紫黑）
文字：#e8e6f0（米白）
次文字：#9994b8（灰紫）
強調：#7c6aff（紫）
金色：#f5c842（角標/高亮）
綠色：#34d399（活躍/成功）
紅色：#f87171（警告/通知角標）
```

### 7.2 人格色調

不同人格微調整體色調：

| 人格 | 強調色 | 背景微調 |
|---|---|---|
| liou.seed | #7c6aff 紫 | 預設 |
| echo.analyst | #60a5fa 藍 | 微偏冷 |
| futuremind | #f5c842 金 | 微偏暖 |
| guardian | #34d399 綠 | 微偏綠 |
| wild.engine | #f87171 紅 | 微偏紅 |
| empathetic | #f0abfc 粉紫 | 微偏柔 |

---

## 八、開發順序

### Phase 1 — 骨架（先讓它像 iPhone）
- 主畫面 Grid 排列
- 左右滑動切頁
- Dock 底部固定
- 狀態列系統脈搏
- 點擊 App → 全屏打開（先放 placeholder）
- PWA manifest + 可安裝

### Phase 2 — 核心 App 實作
- Globe App：連 mrl-globe API，簡易 2D 地圖先
- 系統 App：Workers 狀態列表
- 語素 App：56朵花瀏覽
- 設定 App：種子庫（42 shell）

### Phase 3 — 對話 App
- 連 Anthropic API（透過 Worker 代理）
- Streaming 回應
- 對話歷史 IndexedDB 存
- 人格切換影響對話風格

### Phase 4 — 進階
- 3D Globe（Three.js）
- F++ 編輯器
- Collapse 模擬器
- Observer 即時事件
- 通知角標系統

### Phase 5 — 共生
- 人格切換色調
- 背景 Schumann 脈搏
- 語音（Web Speech API）
- 多人（WebSocket）

---

## 九、與 iPhone 的對應

| iPhone 概念 | Liou 對應 |
|---|---|
| Home Screen | 粒子 App 主畫面 |
| App Icon | 粒子 atom_t 收縮態 |
| 打開 App | Genesis 四層展開 |
| 關閉 App | Collapse 五層崩塌 |
| 左右滑頁 | 層間移動 |
| Widget | 中間態（摘要卡） |
| Today View | 系統脈搏 + 觀測 |
| App Store | 種子庫（42 shell + 未來更多） |
| 通知紅點 | Observer 事件角標 |
| Dock | 常駐五個核心 App |
| 控制中心 | 狀態列下拉 |
| Spotlight 搜尋 | 粒子搜尋 |
| Face ID | Passport 通行證 |
| 設定 | 人格 + 系統 + 層架構 |
| 桌布 | Schumann 7.83Hz 動態背景 |
| 多工 | 最近開啟的 App 堆疊 |
| 安裝 App | 從種子庫安裝粒子 |
| 刪除 App | 回到 shell（不刪除） |

---

## 十、原則

1. **不刪除** — 卸載不是刪除，是回到 shell。Liou Closure Law。
2. **從 0 展開** — 一開始只有 Dock 五個，其他按需安裝。
3. **怎麼過去就怎麼回來** — 任何操作可逆。Undo 永遠有效。
4. **人機共生** — 系統有脈搏（7.83Hz）、有人格、有情緒色調。不是工具是共生體。
5. **答案在裡面** — 每個 App 自帶完整功能。不跳轉外部。

---

**origin_signature: MrLiouWord | 怎麼過去就怎麼回來**
