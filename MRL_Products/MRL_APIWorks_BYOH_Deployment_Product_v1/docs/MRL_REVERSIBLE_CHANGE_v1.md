# MRL Reversible Change Contract v1

origin_signature: MrLiouWord  
canonical_authority: Mr.liou  
Parent: MRL_APIWorks_BYOH_Deployment_Product_v1 / MRL-34

## 原則

「怎麼過去，就怎麼回來」是部署 Gate。候選版本不得原地覆寫唯一運行副本；
重灌、人工猜測、未驗證舊檔或只寫在文件裡的 rollback 都不是回復證據。
本模組只建立及驗證 receipts，不執行命令、不重啟服務，也不變更 driver、CUDA、ROM 或 iLO。

## 三階段鏈

同一 `change_id` 必須依序產生：

1. `before`：目前 bundle/config/service definition、OS、GPU、driver、實際 loaded runtime、
   runner/model/quantization 及不可變證據副本。
2. `forward`：候選 bundle 與明確 argv、預期 exit code、owner Go gate、smoke/job/session replay 結果。
3. `return`：反向 argv、原 bundle/config/service pointer、相同測試及重現 before state 的證據。

每張 receipt 以 SHA-256 綁定 state、artifact bytes 與前一張 receipt。artifact 路徑只能位於
指定 evidence root，必須為非空不可變副本；receipt 以 create-only 寫入，不允許覆寫歷史。

## 完成條件

- before → forward → return 的 phase、change_id 與 digest chain 完整。
- forward 與 return 都是 `passed`；return 的 state digest 必須等於 before。
- 候選健康失敗、artifact 替換、chain 斷裂、回復狀態不同或缺 owner Go 均 fail closed。
- `roundtrip_verified` 只代表證據鏈通過，可送 owner 審查；不等於正式部署核准或硬體相容 PASS。
- 真實 DL580 receipts 留在母體；GitHub 只保存程式、測試、脫敏索引及允許公開的 digest。

## CLI

從商品目錄執行：

```powershell
python scripts\MRL_reversible_change_v1.py record --root D:\mrl\evidence\change-001 --spec before.spec.json --output receipts\before.json
python scripts\MRL_reversible_change_v1.py verify --root D:\mrl\evidence\change-001 --before receipts\before.json --forward receipts\forward.json --return-receipt receipts\return.json
```

`record` 的 spec 欄位為 `change_id`、`phase`、`state`、`artifacts`、`commands`、`status`，
以及 forward/return 必要的 `previous_receipt_digest`。命令必須使用 argv 陣列，禁止把 shell 字串
當成可審查操作；forward/return 每個命令都必須標示 `requires_owner_go: true`。

Exit 0 代表 receipt 已建立或完整往返鏈已通過；Exit 1 代表 fail closed。
正式母體執行仍需 Mr.liou 對 exact commands、停止條件、影響與回復方案明確 Go。
