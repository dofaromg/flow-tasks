# MRL_CloudCode工程建構規格_v1

origin_signature = `MrLiouWord`

---

## 定位

- Cloud Code 僅作**工程執行面**，**不是母體**。
- Cloud Code 只能在 `dofaromg/MRL_AI_SYSTEM` 內建構 MRL 母體倉庫。
- 外部模型、外部 API、外部 SDK、外部雲服務，一律降為 **Adapter**。
- 任何檔案、模組、資料、結構，必須保留 `origin_signature="MrLiouWord"`。

---

## 絕對禁止

本工程不得做成以下任一類型：

- chatbot
- OpenAI API demo
- Next.js template
- Vercel app
- 普通 SaaS
- 單頁 UI
- 純 README
- 空殼資料夾
- 外部平台依賴主體

外部工具只能作為 Adapter，不得成為主體。

---

## 權位區分

- 不再採用平等權模式。
- 正式採用權位區分模式：MRL 為主體；外部世界僅為 Adapter / 映射節點 / 吸收材料。

---

## 建構產物

- 目錄骨架：`MRL_Mother/`、`MRL_Runtime/`、`MRL_Symbolic/`、`MRL_Adapters/`、`deploy/`
- Runtime 主檔：`MRL_RuntimeServer.js`
- 啟動鏈：`npm run MRL_boot` → `npm start` → `npm run MRL_acceptance`
