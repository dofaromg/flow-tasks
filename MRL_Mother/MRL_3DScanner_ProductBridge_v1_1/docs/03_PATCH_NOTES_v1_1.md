# 03_PATCH_NOTES_v1_1

## 修補項目

1. iOS multipart upload string literal 修正：所有 CRLF 改為 `\r\n`，`name="files"` 正確 escape。
2. iOS 入口補齊：新增 `Views/ScansListView.swift`，讓 `PhotogramApp.swift` 有可解析入口。
3. Combine import 補齊：`Scan.swift` 與 `MRLReconstructionClient.swift` 明確匯入 Combine。
4. Python runner 修正 mrl3d config schema：
   - `out_dir` 取代錯誤的 `output_dir`
   - `input.type` 取代錯誤的 top-level `mode`
   - mesh/video/colmap 分別使用 mrl3d 對應 adapter
5. runner 增加 adapter 驗證：預期 mesh 卻收到 simulate 時直接 failed。
6. backend job 狀態增強：job message 使用 `MRL_JOB_REPORT.json.reason`，report 鏡像到 `storage/reports`。
7. acceptance script 改為真 mesh `.obj` 驗收，不再用 `.txt` 造成無效 runner 測試。

## 驗收重點

- backend syntax: `node --check server.js`
- runner syntax: `python -m py_compile python/mrl3d_job_runner.py`
- health: `/api/health`
- upload: `/api/scans/upload`
- job: `/api/reconstruction/jobs`
- runner: mesh `.obj` 應產生 `mrl3d_output/*` 並回 completed
- no fake: mrl3d adapter mismatch 必須 failed
