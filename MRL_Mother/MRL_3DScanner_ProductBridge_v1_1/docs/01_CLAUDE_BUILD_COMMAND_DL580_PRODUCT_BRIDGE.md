# Claude DL580 建構命令：MRL_3DScanner_iOS_DL580_ProductBridge_v1

你現在進入 MRL_Engineering_Execution_Mode。

任務：在 DL580 / Windows Server 上，建立可運行的 iOS 3D 掃描資料上傳與 MRL 3D 重建橋接服務。

部署路徑：

```powershell
D:\MRL_3DScanner_ProductBridge_v1
```

## 一、不得刪減

1. 不得刪除 `included/` 內任何既有包。
2. 不得把 `MRL_3D_AI_Reconstruction_Product_Grade_v1.zip` 改名或覆蓋。
3. 不得把缺少 COLMAP / OpenMVS 說成 PASS。
4. 不得把 upload 成功說成 reconstruction 完成。
5. 不得刪除既有 storage / jobs / uploads / outputs。

## 二、建立目錄

```powershell
mkdir D:\MRL_3DScanner_ProductBridge_v1 -Force
Copy-Item -Recurse * D:\MRL_3DScanner_ProductBridge_v1
cd D:\MRL_3DScanner_ProductBridge_v1
```

## 三、安裝

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\MRL_install_bridge.ps1
```

## 四、啟動

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\MRL_start_bridge.ps1
```

## 五、驗收

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\MRL_acceptance_check_bridge.ps1
```

## 六、驗收標準

PASS 條件：

1. Node backend npm install PASS。
2. backend port 3050 health PASS。
3. `/api/scans/upload` 可收檔並寫 storage。
4. `/api/reconstruction/jobs` 可建立 job。
5. `/api/reconstruction/jobs/:id` 可讀狀態。
6. runner 若缺 mrl3d / COLMAP，必須回 failed + reason，不得假 completed。
7. reports 寫入 `backend/MRL_3D_Reconstruction_Server/storage/reports`。

最後只輸出：

1. install PASS / FAIL
2. backend start PASS / FAIL
3. health PASS / FAIL
4. upload PASS / FAIL
5. job create PASS / FAIL
6. runner PASS / FAIL
7. failed reason
8. created files
