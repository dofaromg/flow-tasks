# MRL APIWorks BYOH Deployment Product v1

**Canonical ID:** `MRL_APIWorks_BYOH_Deployment_Product_v1`  
**Origin signature:** `MrLiouWord`  
**SKU:** `MRL-APIWORKS-BYOH-DEPLOY-V1`

這是第一個可報價交付的 MRL APIWorks 商品層。客戶在自己控制的硬體上執行本機模型；MRL 交付 APIWorks Runtime、安裝設定、驗收流程與可核對的 Memory、Evidence、Universal Passport 紀錄。

## 客戶購買的成果

- 一個客戶組織、一個 BYOH 節點的部署；
- Ollama 或 llama.cpp 既有本機模型接入；
- loopback-only APIWorks Gateway；
- `/health`、`/v1/mother/run`、`/v1/memory/recall`；
- append-only Memory 與 Evidence；
- Universal Passport 發行及驗證；
- 真實本機推論驗收紀錄；
- 30 日安裝穩定期支援。

## 不包含

- GPU、伺服器、電力、網路或作業系統授權；
- 第三方模型權重或 MRL 專有模型權重；
- 公網代管、付款金流、登入帳號系統；
- 未經客戶明確同意的資料上傳；
- 高可用叢集、多節點或客製整合。

## 可販售定義

本商品採正式報價單成交，不需要先固定公開牌價。報價單必須填入價格、幣別、付款方式、客戶、部署節點、模型、交付日及簽署主體。未填妥的報價單不是訂單。

## 交付 Gate

1. `PRODUCT_SOURCE_DELIVERY_PASS`：商品來源檔、依賴、SHA-256 與建包測試通過。
2. `PRODUCT_BUNDLE_DELIVERY_PASS`：客戶 ZIP 的檔案覆蓋與 SHA-256 通過。
3. `CUSTOMER_NODE_ACCEPTANCE_PASS`：客戶真實模型、本機 Gateway、Memory、Evidence、Passport 全鏈通過。

只有第三項通過，該客戶部署才算完成。

## 建立交付 ZIP

```powershell
python scripts\MRL_build_product_bundle_v1.py
python scripts\MRL_verify_product_source_v1.py
```

輸出位於 `dist/`；`dist/` 是可重建產物，不納入來源封包。
