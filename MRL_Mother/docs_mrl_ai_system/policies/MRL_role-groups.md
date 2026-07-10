# MRL Resolution Role Groups

本文件為對 Mozilla `role-groups.md` 的去重、蒸餾與系統化整合版本，用於 MRL AI System 內部的治理、事件調查、合規判定與決議流程。

來源參考：
- Mozilla Inclusion: `code-of-conduct-enforcement/investigation/working-group/role-groups.md`
- Source URL: https://github.com/mozilla/inclusion/blob/master/code-of-conduct-enforcement/investigation/working-group/role-groups.md

## 1. 目的

本文件定義在處理行為規範、合規事件、社群衝突、系統濫用或其他需要正式決議的案件時，應納入共識流程的角色群組，以及各角色在決策中的責任分工。

目標是：
- 明確決策責任
- 降低角色重疊與責任模糊
- 讓案件能被一致、可追蹤、可審計地處理
- 支援跨社群、跨專案、跨系統事件的協作

## 2. 決策模型（RASCI）

案件處理採用 RASCI 模型：

- **R — Responsible（執行責任）**：負責推動流程、彙整資訊、協調溝通
- **A — Accountable（最終���板）**：負責最終決議與投票
- **S — Supportive（支援）**：提供法務、人資、制度或專業支援
- **C — Consulted（諮詢）**：提供情境、影響面與專案背景
- **I — Involved（涉入/需納入）**：與案件相關但不屬於上述類別者

### 標準角色映射

- **R**：Case Coordinator
- **A**：CCRM / CPGP
- **S**：Legal, HR
- **C**：Stakeholders
- **I**：Other involved individuals, including Reporters where appropriate

## 3. 決策原則

1. **任何 RASCI 角色皆可提出建議**。
2. **最終決議由 Accountable（A）角色投票或共識決定**。
3. **Case Coordinator 不應單獨決定案件結果**，其核心責任是確保流程完整推進。
4. **涉及法律、僱傭、賄賂、利益衝突或資安風險時，必須升級相應支援角色**。
5. **工作小組應隨案件需要動態擴張或收斂**，避免不必要暴露案件資訊。
6. **所有角色參與應遵循最小必要知悉原則**。

## 4. 角色定義

### 4.1 Case Coordinator（案件協調人）

**角色分類**：Responsible

**核心職責**：
- 推動案件從受理到結案
- 確保流程、諮詢與溝通按規範進行
- 協調參與者、時間線、材料彙整與決議紀錄
- 確保利害關係人被適當通知
- 維持案���追蹤、版本與交接清晰

**不應負責**：
- 單方裁決案件
- 取代 Accountable 角色進行最終拍板

### 4.2 CCRM（Community Conflict Report Managers）

**角色分類**：Accountable

**核心職責**：
- 代表相關社群、專案或管理面承擔最終決策責任
- 判斷案件是否成立、風險等級與處置方案
- 參與投票或共識形成
- 提供案件發生場域的治理背景

**適用情境**：
- 當事件發生於特定社群、專案、產品或維運範圍內
- 當需要由該領域管理責任人承擔決策責任

### 4.3 CPGP（Policy / Program Accountable Role）

**角色分類**：Accountable

**核心職責**：
- 與 CCRM 一同作為最終決議責任方
- 代表政策、規範或執行計畫面提供決策依據
- 確保處置與制度要求一致

**說明**：
原始文件中與 CCRM 並列於 Accountable（A）角色；在 MRL 系統中可對應為政策治理或規範計畫責任角色。

### 4.4 Reporter（通報者）

**角色分類**：Involved

**核心職責**：
- 提供案件初始資訊、證據與脈絡
- 在需要時補充說明

**處理原則**：
- 同一衝突事件可能存在多位通報者
- 每一份通報應被獨立對待與記錄
- 通報者不自動成為最終決��者

### 4.5 Legal Investigator（法務調查角色）

**角色分類**：Supportive

**介入條件**：
- 涉及利益衝突
- 涉及反賄賂或不當利益交換
- 涉及違法疑慮
- 涉及重大法律風險，例如詐欺、挪用、威脅或其他法規問題

**核心職責**：
- 提供法律風險判讀
- 協助界定可採取與不可採取的措施
- 支援證據保全、升級與外部處置建議

### 4.6 HR Investigator（人資調查角色）

**角色分類**：Supportive

**介入條件**：
- 案件涉及員工或受僱關係
- 法務調查要求 HR 協同
- 涉及職場行為、勞務關係或內部政策執行

**核心職責**：
- 提供人事與雇傭面支援
- 協助評估內部措施、保護機制與程序正義
- 確保與組織內部 HR 規範一致

### 4.7 Stakeholders（專案/組織利害關係人）

**角色分類**：Consulted

**核心職責**：
- 提供案件對專案、社群、產品或系統的影響評估
- 補充情境脈絡與歷史背景
- 協助判斷處置的次生風險與落地影響

**注意事項**：
- 利害關係人提供意見，但不當然擁有最終裁決權
- 若存在利益衝突，應限制其參與範圍

### 4.8 RWG（Resolution Working Group，決議工作組）

**角色分類**：跨角色臨時工作組

**組成方式**：
通常由以下角色按案件需要組成：
- Community Manager / CCRM
- Enforcement / Policy 代表
- 相關 Investigator（Legal / HR / Security 等）
- Case Coordinator

**核心職責**：
- 協助整理事實與選項
- 促進諮詢、討論與決議收斂
- 將案件推進至可執行的 resolution
- 形成具體建議供 Accountable 角色裁決

**運作原則**：
- 為臨時性群組
- 可依案件複雜度擴張或收斂
- 參與人數應受最小必要知悉原則約束

### 4.9 Safety / Security Consultation（安全/資安諮詢）

**角色分類**：Consulted 或 Supportive（視案件而定）

**介入條件**：
- 案件涉及系統被使用、濫用、破壞、入侵、繞過或槓桿利用
- 事件牽涉平台安全、帳號濫用、資料暴露、供應鏈或營運風險

**核心職責**：
- 提供安全事件分析與技術風險判讀
- 協助界定影響範圍、證據保存與風險緩解
- 在必要時加入工作組共同推動處置

## 5. MRL 系統內建議落地方式

在 MRL AI System 中，建議將上述角色對映到以下治理流程：

- **Coordinator** → 事件編排 / case orchestration owner
- **Accountable** → 合規治理決策者 / policy owner / domain owner
- **Legal / HR / Security** → 專業升級通道
- **Stakeholders** → 受影響模組、產品、社群或運營負責人
- **RWG** → 單一案件的臨時決策工作組

可用於：
- 行為規範違反案件
- 模型濫用或代理濫用調查
- 合規事件與審計例外處理
- 跨模組衝突與責任歸屬判定
- 安全與治理交叉事件

## 6. 最小作業流程

1. **受理案件**：建立 case，指派 Case Coordinator
2. **初步分類**：判定是否涉及社群、政策、法務、HR、資安
3. **建立角色矩陣**：填入 R / A / S / C / I
4. **組建 RWG**：只納入必要角色
5. **蒐集資訊與諮詢**：形成處置建議
6. **A 角色決議**：投票或共識拍板
7. **執行與通知**：落地處置並通知相關方
8. **結案與留痕**：保存決策依據、時間線與後續建議

## 7. 簡化模板

```md
Case ID:
Title:
Coordinator (R):
Accountable (A):
Supportive (S):
Consulted (C):
Involved (I):
Working Group Members:
Decision Summary:
Actions:
Audit Notes:
```

## 8. 備註

本文件不是 Mozilla 原文逐字轉錄，而是基於其角色結構進行：
- 去重
- 蒸餾
- 語義整理
- 針對 MRL AI System 內部治理場景的適配

如需嚴格法務或正式政策採納，應再由實際 Legal / HR / Governance owner 審閱。