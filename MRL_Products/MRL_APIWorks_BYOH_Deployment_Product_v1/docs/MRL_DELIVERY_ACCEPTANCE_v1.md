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
   .\MRL_Mother\MRL_MotherModel\MRL_AI_Mother_Autonomous_Runtime_Baseline_v1\scripts\MRL_acceptance_v1.ps1
   ```

4. 保存 `MRL_AI_MOTHER_AUTONOMOUS_RUNTIME_ACCEPTANCE_PASS`、Evidence head、Passport hash、ZIP SHA-256 與測試時間。

## 保存磁碟核對回執與重啟後重播

既有 PowerShell 驗收之後，在實際節點、交付 ZIP 的頂層目錄執行下列命令。
`--data-dir` 必須指向 Gateway 真正使用的資料目錄；下例是既有啟動器的預設位置。
`D:\MRL_Acceptance` 是私人驗收回執目錄，不得位於受 SHA 保護的商品來源或 Runtime 資料內。

```powershell
python .\MRL_Products\MRL_APIWorks_BYOH_Deployment_Product_v1\scripts\MRL_capture_node_evidence_v1.py `
  --data-dir .\MRL_Mother\MRL_MotherModel\MRL_AI_Mother_Runtime_Data `
  --output D:\MRL_Acceptance\MRL_node_before_restart.json
```

工具會執行一次本機推論，核對 API 重播與磁碟 Memory 相同，驗證 Memory、Evidence、Passport
的 SHA-256 鏈及交叉引用，保存回執後再讀回。失敗退出碼為 1，失敗回執不授予 PASS。
回執含模型輸出與節點資訊，只保存本機，不自動上傳；同名檔案不覆寫。

在維護窗口中，依實際節點的既有服務管理方式只重啟此 Gateway，保留其設定與資料目錄；
不得為了驗收而重啟或替換既有推論服務。重啟後執行：

```powershell
python .\MRL_Products\MRL_APIWorks_BYOH_Deployment_Product_v1\scripts\MRL_capture_node_evidence_v1.py `
  --data-dir .\MRL_Mother\MRL_MotherModel\MRL_AI_Mother_Runtime_Data `
  --replay-receipt D:\MRL_Acceptance\MRL_node_before_restart.json `
  --output D:\MRL_Acceptance\MRL_node_after_restart.json
```

重播不重新推論；必須找回原回執的同一個 session、兩筆 Memory、Evidence 與 Passport。
工具輸出 `LIVE_LOOP_EVIDENCE_PASS` 或 `PERSISTED_REPLAY_EVIDENCE_PASS`，均不等於
`CUSTOMER_NODE_ACCEPTANCE_PASS`。它不能自行證明真實模型權重或觀測到服務重啟；
需另附服務重啟前後的 PID／啟動時間、實際模型身份、來源包 SHA、原 PowerShell 驗收結果，
並完成交付人員審核。模擬模型的整合測試不得提升為 DL580 或客戶實機驗收。

## 驗收狀態

- `PASS`：完整鏈通過，進入30日穩定期。
- `BLOCKED_CUSTOMER_ENVIRONMENT`：硬體、驅動、模型或權限未就緒。
- `FAIL_PRODUCT_DEFECT`：交付軟體未符合規格，由MRL修復後重測。
- `CHANGE_REQUEST`：超出單節點與既定模型範圍，另行報價。
