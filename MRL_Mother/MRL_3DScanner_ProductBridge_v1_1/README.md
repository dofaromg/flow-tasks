# MRL_3DScanner_iOS_DL580_ProductBridge_v1_1

origin_signature: MrLiouWord
branch: MRL_Branch_3DScanner_iOS_DL580_ProductBridge_v1_1
scope: iOS capture app + DL580 reconstruction bridge + existing product-grade MRL 3D runtime package

## 交付定位

本包接續 `MRL_3D_AI_Reconstruction_Product_Grade_v1`，補上 iOS 掃描端與 DL580 後端橋接。

本包不刪除、不替代前包。前包已放在 `included/`，本包做 additive bridge。

## 已包含

- iOS SwiftUI 掃描端基準檔
- iOS 上傳到 DL580 的 client 與 job UI
- DL580 Node.js API server
- Python runner：呼叫 mrl3d CLI、COLMAP、OpenMVS
- Windows Server PowerShell scripts
- Claude 建構命令
- 驗收矩陣

## 執行順序

1. 先解壓本包到 DL580。
2. 執行 `scripts/MRL_install_bridge.ps1`。
3. 執行 `scripts/MRL_start_bridge.ps1`。
4. 執行 `scripts/MRL_acceptance_check_bridge.ps1`。
5. iOS 端設定 DL580 server URL，例如 `http://<DL580-IP>:3050`。

## 真實狀態規則

- `uploaded`：檔案真的上傳到 DL580 storage。
- `queued`：job 真的寫入 jobs storage。
- `running`：runner process 已啟動。
- `completed`：mrl3d / COLMAP / mesh / video pipeline 有產生報告。
- `failed`：缺少 COLMAP / OpenMVS / mrl3d / input，不得偽裝成功。



## v1.1 修補定位

此版保留 v1 additive bridge 結構，修補以下阻斷點：

- 修正 iOS multipart 上傳字串，避免 Swift unterminated string literal。
- 補上 iOS `ScansListView` 基準入口，避免 `PhotogramApp.swift` 找不到 view。
- 補上 Combine import，讓 `ObservableObject` / `@Published` 來源明確。
- 修正 Python runner 產生的 mrl3d YAML schema：使用 `out_dir` 與 `input.type`，避免 mesh/video/colmap 被 mrl3d 當成 simulate。
- runner 會驗證 mrl3d 回傳 adapter，不符合預期即 failed，不偽裝 completed。
- backend job message 讀取 `MRL_JOB_REPORT.json` reason，並把 report 鏡像寫入 `storage/reports`。
- PowerShell acceptance 改用實際 cube.obj mesh 檔，並輪詢 job 結果。
