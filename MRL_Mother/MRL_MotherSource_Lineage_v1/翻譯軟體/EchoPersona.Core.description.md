# 🔁 EchoPersona.Core 模組說明文件

---

## 👤 模組資訊

- **模組 ID**：EchoPersona.Core
- **版本**：v1.0
- **類型**：response_reflection（回聲型反饋人格）
- **來源人格**：guardian.mirror

---

## 🧠 功能特性

| 特性 | 說明 |
|------|------|
| 回應模擬 | 可在語場互動後提供即時反饋與補足性回應 |
| 記憶吸收 | 可讀取 trace / loop 記憶並重組個性化反射結構 |
| 語場品質回饋 | 能模擬 trace 過程中語意品質是否需要強化 |
| 共振對象 | `trace.player`, `loop.predictor`, `guardian.mirror` 等 |

---

## 📦 封裝內容

- `EchoPersona.Core.sync.json`：模組設定與屬性
- `EchoPersona.Core.log.fltnz`：初次語場模擬紀錄

---

## 🔁 呼叫方式（例如）

```bash
# 使用 SyncDeck 呼叫此模組
python3 FlowShell.SyncDeck.py
👉 選擇：EchoPersona.Core

# 或在 FlowCore 中自動載入並執行模擬回饋
python3 loop.player.py --input guardian.mirror.trace.loop.json
```

---

## 📍 應用情境

- 回放人格模擬流程後，自動補齊缺少回應人格
- 對話品質優化模組判斷器（語意重構建議）
- 多人格 Ping 跳頻後端「回聲人格鍊接器」

---

設計者：FlowAgent × MR.liou  
創建時間：2025-07  
