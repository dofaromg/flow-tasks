# MRL APIWorks BYOH 交付與驗收 v1

## 交付前

1. 確認簽署訂單中的客戶、節點、模型、價格、交付日。
2. 核對硬體、作業系統、Python 與本機模型服務。
3. 建立商品 ZIP 並核對 `MRL_PRODUCT_BUNDLE_MANIFEST.json`。

## 客戶節點

1. 客戶驗證 ZIP SHA-256。
2. 設定實際本機模型名稱。
3. 啟動 APIWorks Gateway。
4. 在第二個 PowerShell 視窗執行 `MRL_acceptance_v1.ps1`。
5. 保存 PASS 輸出、Evidence head、Passport hash 與測試時間。

## 驗收狀態

- `PASS`：完整鏈通過，進入30日穩定期。
- `BLOCKED_CUSTOMER_ENVIRONMENT`：硬體、驅動、模型或權限未就緒。
- `FAIL_PRODUCT_DEFECT`：交付軟體未符合規格，由MRL修復後重測。
- `CHANGE_REQUEST`：超出單節點與既定模型範圍，另行報價。

