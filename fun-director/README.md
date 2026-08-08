# 爽度導演 FunDirector — 金字塔底層堆疊模組

> MrLiouWord 粒子系統哲學 × 遊戲爽度生成框架  
> 版本：1.1.0 ｜ 遵循 LAW-0 / LAW-1 / LAW-2

---

## 一、金字塔三層概念

```
           ┌─────────────────────────────┐
           │   Layer 3：人格導演層        │
           │  Persona Director            │
           │  HYPE / PRANK / SPOOKY       │
           └──────────────┬──────────────┘
                          │ 決定偏好與強度
           ┌──────────────▼──────────────┐
           │   Layer 2：反轉邏輯層        │
           │  Twist Logic                 │
           │  身分反轉 / 規則爆衝 / 搞笑連鎖 │
           └──────────────┬──────────────┘
                          │ 套用邏輯扭轉
           ┌──────────────▼──────────────┐
           │   Layer 1：回饋物理層        │
           │  Feel Physics                │
           │  命中停頓 / 震屏 / 擊退 /    │
           │  布娃娃 / 道具破壞 / 連鎖反應 │
           └─────────────────────────────┘
```

| 層次 | 職責 | 粒子類型 |
|------|------|----------|
| Layer 1 回饋物理層 | 提供最直接的打擊感、視覺特效與物理笑點 | `feelPhysics` |
| Layer 2 反轉邏輯層 | 打破預期規則，製造意外爆點（小兵才是魔王） | `twistLogic` |
| Layer 3 人格導演層 | 決定本次演出的情緒基調與強度偏好 | `personaDirector` |

---

## 二、檔案結構

```
fun-director/
├── fun/
│   ├── particles.json   # 粒子定義（feelPhysics / twistLogic / personaDirector）
│   ├── modules.json     # 模組規格（cooldown / duration / weight）
│   └── mapping.json     # 情緒向量映射（comfort / humor / thrill / power）
├── src/
│   └── director.js      # 導演核心實作（runDirector + runFunSequence）
├── tests/
│   ├── director.test.js # 自動測試（60 個斷言）
│   └── sequence.test.js # Sequence 自動測試（58 個斷言）v1.1.0 新增
└── README.md            # 本文件
```

Worker 整合：`particle-chat-v42/src/index.js` — `POST /api/fun/next` 與 `POST /api/fun/sequence` 端點

---

## 三、JSON Schema 欄位說明

### `fun/particles.json`

```jsonc
{
  "feelPhysics": [
    {
      "id": "HIT_STOP",           // 唯一識別碼
      "name": "命中停頓",          // 繁中名稱
      "description": "...",       // 說明
      "params": {
        "duration_ms": 80,        // 效果持續毫秒
        "intensity": 1.0          // 基礎強度（0.0 ~ 2.0+）
      }
    }
    // ... 共 6 個 feelPhysics 粒子
  ],
  "twistLogic": [
    {
      "id": "IDENTITY_FLIP",
      "name": "身分反轉",
      "params": {
        "probability": 0.15,      // 觸發機率
        "duration_s": 10          // 效果持續秒數
      }
    }
    // ... 共 3 個 twistLogic 粒子
  ],
  "personaDirector": [
    {
      "id": "HYPE",
      "name": "炒熱者",
      "bias": {
        "comfort": 0.2,           // 舒適感偏好 (0.0 ~ 1.0)
        "humor":   0.3,           // 幽默感偏好
        "thrill":  0.4,           // 刺激感偏好
        "power":   0.1            // 力量感偏好
      }
    }
  ]
}
```

### `fun/modules.json`

```jsonc
[
  {
    "id": "CHAIN_REACTION",
    "category": "feelPhysics",
    "cooldown_s": 5.0,    // 觸發後冷卻秒數
    "duration_s": 3.0,    // 效果持續秒數
    "weight": 6           // 隨機選取權重（越高越常被選）
  }
]
```

### `fun/mapping.json`

```jsonc
{
  "emotionVectors": {
    "humor": {
      "description": "幽默感 — 失控搞笑",
      "params": { "ragdoll_loose": 0.9, "chain_count": 5, "laugh_factor": 2.0 }
    }
  },
  "personaPresets": {
    "PRANK": {
      "funIntensity": 1.2,  // 全域爽度倍率
      "chaos": 1.8,         // 亂度倍率（越高越失控搞笑）
      "vfxScale": 1.0,      // 視覺特效縮放
      "sfxPunch": 1.0,      // 音效衝擊感倍率
      "slowMo": false        // 是否啟用慢動作終結演出
    }
  },
  "compressionScales": {
    "mobile":   { "vfxScale": 0.5,  "fragments": 4,  "chain_count": 2 },
    "desktop":  { "vfxScale": 1.0,  "fragments": 12, "chain_count": 3 },
    "showcase": { "vfxScale": 2.5,  "fragments": 30, "chain_count": 6 }
  }
}
```

---

## 四、API 端點用法

### `POST /api/fun/next`

回傳下一段（10 秒）的 twist recipe、參數與 eventLog。

**請求格式**

```json
{
  "playerState":  { "hp": 80, "combo": 5 },
  "roomState":    { "wave": 2, "enemyCount": 3 },
  "personaState": "HYPE",
  "seed":         42
}
```

| 欄位 | 類型 | 說明 | 預設 |
|------|------|------|------|
| `playerState` | object | 玩家狀態（hp, combo 等） | `{}` |
| `roomState` | object | 房間狀態（wave, enemyCount 等） | `{}` |
| `personaState` | string | 人格 ID：`HYPE` / `PRANK` / `SPOOKY` | `HYPE` |
| `seed` | string \| number | 隨機種子；相同 seed 產生相同輸出（LAW-2）| `Date.now()` |

**curl 範例**

```bash
# 基本呼叫
curl -X POST https://your-worker.workers.dev/api/fun/next \
  -H "Content-Type: application/json" \
  -d '{"personaState":"PRANK","seed":42}'

# 完整帶入狀態
curl -X POST https://your-worker.workers.dev/api/fun/next \
  -H "Content-Type: application/json" \
  -d '{
    "playerState":  {"hp": 80, "combo": 5},
    "roomState":    {"wave": 2, "enemyCount": 3},
    "personaState": "SPOOKY",
    "seed":         "my-reproducible-seed"
  }'
```

**回應範例**

```json
{
  "twistRecipe": [
    {
      "moduleId":   "RAGDOLL",
      "category":   "feelPhysics",
      "duration_s": 2.0,
      "cooldown_s": 3.0,
      "params": {
        "joint_loose":  0.93,
        "duration_ms":  2000,
        "slowMo":       false,
        "vfxScale":     0.91,
        "sfxPunch":     0.95
      }
    },
    {
      "moduleId":   "COMEDY_CHAIN_REACTION",
      "category":   "twistLogic",
      "duration_s": 4.0,
      "cooldown_s": 6.0,
      "params": {
        "trigger_count": 4,
        "laugh_factor":  2.48,
        "slowMo":        false,
        "vfxScale":      0.91,
        "sfxPunch":      0.95
      }
    }
  ],
  "duration_s":  10,
  "cooldown_s":  6.0,
  "persona":     "PRANK",
  "eventLog": { ... },
  "law":             "LAW-1: 記憶體守恆律 — 每次決策可追溯",
  "origin_signature":"MrLiouWord.FunDirector",
  "version":         "1.1.0"
}
```

### `POST /api/fun/sequence` *(v1.1.0 新增)*

一次生成 N 個連續 10 秒視窗，適合完整場次規劃。相同 `seed` 永遠回傳相同序列（LAW-2）。

**請求格式**

```json
{
  "windows":      6,
  "playerState":  { "hp": 100, "combo": 0 },
  "roomState":    { "wave": 1, "enemyCount": 5 },
  "personaState": "PRANK",
  "seed":         42
}
```

| 欄位 | 類型 | 說明 | 預設 |
|------|------|------|------|
| `windows` | number | 生成視窗數量（1–100，每個 10 秒） | `6` |
| `playerState` | object | 玩家狀態 | `{}` |
| `roomState` | object | 房間狀態 | `{}` |
| `personaState` | string | 人格 ID | `HYPE` |
| `seed` | string \| number | 基礎隨機種子 | `Date.now()` |

**curl 範例**

```bash
curl -X POST https://your-worker.workers.dev/api/fun/sequence \
  -H "Content-Type: application/json" \
  -d '{"windows":4,"personaState":"SPOOKY","seed":99}'
```

**回應範例**

```json
{
  "sessionId":      "ses_0000002a_m7x2k9",
  "windows": [
    { "twistRecipe": [...], "duration_s": 10, "cooldown_s": 3.0, "persona": "SPOOKY", "eventLog": {...} },
    { "twistRecipe": [...], "duration_s": 10, "cooldown_s": 5.0, "persona": "SPOOKY", "eventLog": {...} }
  ],
  "totalDuration_s": 40,
  "cooldown_s":      5.0,
  "law":             "LAW-2: 記憶體單調性律 — 相同 seed 序列永遠可重現",
  "origin_signature":"MrLiouWord.FunDirector.Sequence",
  "version":         "1.1.0"
}
```

---

## 五、eventLog 範例

```json
{
  "id":         "evt_0000002a_m7x2k9",
  "timestamp":  "2026-03-20T14:53:00.000Z",
  "seed":       "42",
  "persona":    "PRANK",
  "why":        "人格[惡作劇者]在第 2 波（玩家 HP=80）啟動保底爆點：布娃娃、搞笑連鎖",
  "what":       "RAGDOLL + COMEDY_CHAIN_REACTION",
  "duration_s": 10,
  "cooldown_s": 6.0,
  "intensity":  0.93,
  "inputs": {
    "playerState":  { "hp": 80, "combo": 5 },
    "roomState":    { "wave": 2, "enemyCount": 3 },
    "personaState": "PRANK",
    "seed":         "42"
  },
  "modules": [
    { "id": "RAGDOLL",               "category": "feelPhysics", "duration_s": 2.0, "cooldown_s": 3.0 },
    { "id": "COMEDY_CHAIN_REACTION", "category": "twistLogic",  "duration_s": 4.0, "cooldown_s": 6.0 }
  ]
}
```

---

## 六、保底規則說明

| 規則 | 說明 |
|------|------|
| **保底爆點** | 每次選出的第一個模組必定是高衝擊粒子（HIT_STOP / SCREEN_SHAKE / KNOCKBACK / RAGDOLL / CHAIN_REACTION / COMEDY_CHAIN_REACTION） |
| **不可預測性位置** | 隨機性落在「哪個爆點 + 參數強度」，不落在「有沒有爆點」 |
| **低懲罰保證** | 所有選出的模組設計以爽感/笑點為主，不引入高懲罰 |
| **冷卻上限** | `cooldown_s` = 所有選中模組的最大冷卻值 |
| **片段時長** | 固定 10 秒，方便前端計時器整合 |

---

## 七、LAW 遵循說明

| LAW | 說明 | 實作對應 |
|-----|------|----------|
| **LAW-0** 起源簽名律 | 所有輸出含 `origin_signature: "MrLiouWord.FunDirector"` | `runFunDirector()` 回傳值 |
| **LAW-1** 記憶體守恆律 | 每次決策產生完整可追溯的 `eventLog`（why / what / inputs / modules） | `eventLog` 欄位 |
| **LAW-2** 記憶體單調性律 | 相同 `seed` 永遠產生相同 `twistRecipe`（Mulberry32 PRNG） | `funMulberry32(funSeedToNumber(seed))` |

---

## 八、執行本地測試

```bash
cd fun-director

# 單視窗測試（60 個斷言）
node tests/director.test.js

# 序列測試（58 個斷言）v1.1.0 新增
node tests/sequence.test.js
```

預期輸出：
```
╔═══════════════════════════════════╗
║   FunDirector 測試套件 v1.0.0    ║
╚═══════════════════════════════════╝
...
✅ 通過：60  ❌ 失敗：0

╔══════════════════════════════════════════╗
║   FunDirector Sequence 測試套件 v1.1.0  ║
╚══════════════════════════════════════════╝
...
✅ 通過：58  ❌ 失敗：0
```

---

## 九、人格說明

| 人格 ID | 中文名 | 特色 | 推薦場景 |
|---------|--------|------|----------|
| `HYPE` | 炒熱者 | 全場爆炸，節奏快、爽感強，sfxPunch 1.5× | 清版高潮波段 |
| `PRANK` | 惡作劇者 | 亂度 1.8×，搞笑失控為主，連鎖笑點密集 | 物理搞笑清版 |
| `SPOOKY` | 驚恐者 | 刺激感 0.6×，意外反轉爆點，慢動作收尾 | 魔王關前 boss 揭曉 |

---

*由 MrLiouWord 粒子系統哲學驅動 — 複雜度越高，優勢越大。*
