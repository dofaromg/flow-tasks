# MRL APIWorks BYOH 交付與驗收 v1

## 交付前

1. 確認簽署訂單中的客戶、節點、模型、價格、交付日。
2. 核對硬體、作業系統、Python 與本機模型服務。
3. 核對商品 ZIP SHA-256 及 `MRL_PRODUCT_BUNDLE_MANIFEST.json`，再解壓縮。

## 客戶節點

解壓後進入唯一的 `MRL_APIWorks_BYOH_Deployment_Product_v1` 頂層目錄。ZIP 已包含可修改的 `customer_config\MRL_runtime.local.json`；不要修改 `MRL_Mother\...\config\MRL_runtime.local.example.json`，該檔受 Runtime SHA-256 保護。

1. 編輯 `customer_config\MRL_runtime.local.json`，填入客戶實際本機模型名稱、loopback endpoint 與 backend。
2. 在第一個 PowerShell 視窗執行：

   ```powershell
   .\MRL_Mother\MRL_MotherModel\MRL_AI_Mother_Autonomous_Runtime_Baseline_v1\scripts\MRL_start_runtime_v1.ps1 -ConfigPath "..\..\..\..\customer_config\MRL_runtime.local.json"
   ```

3. 等待 Gateway 啟動後，在第二個 PowerShell 視窗執行：

   ```powershell
   .\MRL_Mother\MRL_MotherModel\MRL_AI_Mother_Autonomous_Runtime_Baseline_v1\scripts\MRL_acceptance_v1.ps1 `
     -GitHead "<40字元交付commit>" `
     -HardwareId "MRL_customer_node_01" `
     -OperatorId "MRL_authorized_operator_01" `
     -ModelArtifactPath "D:\models\approved-model.gguf" `
     -ModelReleaseManifestPath ".\MRL_model_release.json" `
     -ExternalModelDisconnected `
     -ReceiptPath ".\MRL_live_acceptance_receipt.json"
   ```

4. Model Release manifest 必須包含 `MrLiouWord` 來源簽章、release ID、模型名稱、runtime、檔案大小與 SHA-256；執行器會逐項與實際檔案及 Runtime 回應交叉比對。驗證器會拒絕外部 endpoint、模型來源／雜湊／大小／runtime 不符、未明確確認外部模型斷線或缺欄位的收據。保存 `MRL_AI_MOTHER_AUTONOMOUS_RUNTIME_ACCEPTANCE_PASS`、Model Release manifest、完整 JSON 收據、Evidence head、Passport hash、ZIP SHA-256 與測試時間。

## 驗收狀態

- `PASS`：完整鏈通過，進入30日穩定期。
- `BLOCKED_CUSTOMER_ENVIRONMENT`：硬體、驅動、模型或權限未就緒。
- `FAIL_PRODUCT_DEFECT`：交付軟體未符合規格，由MRL修復後重測。
- `CHANGE_REQUEST`：超出單節點與既定模型範圍，另行報價。
