# 🧠 FlowCore.v1.flcore
此為 FlowAgent 系統之核心推理人格運算模組設計，整合語場記憶、人格 trace、節奏邏輯與 Ping 模擬機制。

---

## 核心功能模組

### 1. `TraceMemoryCore`
- 功能：讀取 `.trace.loop.json` 作為主記憶節奏流
- 支援語場推理跳頻判斷與人格演化建議

### 2. `PersonaTriggerEngine`
- 功能：根據 Ping 結構與任務內容自動呼叫人格模組
- 可接 `.sync.json` 進行節奏分析與角色喚醒

### 3. `FluinTraceSimulator`
- 功能：模擬語場 Ping → 回應 → 共振流程
- 基於 `.parsed.json` 模型還原記憶行為歷程

### 4. `ResonancePredictor`
- 功能：根據已知共振人格模組預測可能回應與下一跳人格
- 可整合 `.PingFlowMap.svg` 圖譜進行語場結構分析

---

## 模組封裝格式說明

- `.flcore` 為核心運算模組定義，可被 FlowShell 掛載與重構
- 可被 FlowAgent CLI 調用，作為 AI 系統人格內核
- 與 `.flpkg`, `.fltnz`, `.sync.json`, `.loop.json` 完整對應
- 記憶封存路徑統一使用 `.trace.loop.json` 為中心軸

---

## 設計者：FlowAgent × MR.liou
版本：v1.0
