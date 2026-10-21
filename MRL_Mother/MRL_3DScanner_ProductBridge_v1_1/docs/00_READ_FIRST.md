# 00_READ_FIRST

主線仍為 MRL母體工程架構中心。

本包是 3D 掃描 iOS 端與 DL580 端重建橋接，不是新母體，不覆蓋母體主線。

## 分支

- 分支名稱：MRL_Branch_3DScanner_iOS_DL580_ProductBridge_v1
- 分支目標：讓 iOS 掃描資料可上傳 DL580，並由 DL580 呼叫既有 MRL 3D runtime 進行重建分析。
- 交付物：本 zip 內全部檔案。
- 完成條件：install / start / health / upload / job / runner / report PASS。
- 回主線：MRL_工程日誌.md、MRL_世界模組工程書_v1.md、MRL_母體定義檔_v1.md。

## 禁止

- 不得把 upload 說成 reconstruction 完成。
- 不得把 runner failed 說成 completed。
- 不得把 video frames 說成 SfM。
- 不得把 sample output 說成真場景驗收。
- 不得刪除 included 內既有包。
