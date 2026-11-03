# MRL_Video 接線與驗收 / Acceptance

origin_signature: MrLiouWord · canonical_authority: Mr.liou

## 固定工程來源

Repository: dofaromg/flow-tasks。Parent baseline: `608b66e0db23e7cc4eef21ea752668ac800620b3`。
保留 `main_ultimate.py`、`MRL_Bridge/server.js`、`MRL_Mother/root_sources/src/mrl_app.html` 與原始範本名稱。
錄影是工作流程參考；本次未上傳原始錄影、母體原始資料、憑證或實際客戶素材到 GitHub。
新增模組為 `MRL_Video`，對接既有 `MRL_VideoGen`。沒有自行替換 canonical parent。

## 交付層次

| Gate | 通過條件 | 本次狀態來源 |
|---|---|---|
| Source delivery | Expected_Delivery.json 全部檔案存在、非空、雜湊對上、相依齊全 | evidence/MRL_Video_Validation_20261103.json |
| Local automated acceptance | 測試、三比例實際渲染、解碼、ZIP 驗證及錯誤案例 | 同上；synthetic fixtures |
| GitHub CI | 本 PR exact head 的 workflow 成功 | Actions 實際執行紀錄；不可預先宣稱 |
| DL580 deployment | 本機依賴、私有綁定、工作程序及磁碟權限核對 | NOT_RUN |
| Mother roundtrip | Bridge 入列→worker製作→狀態查詢→成品下載及雜湊讀回 | NOT_RUN |
| iPhone acceptance | 私有入口、登入、播放、下載、子版本操作成功 | NOT_RUN |
| Publication | Owner 審查素材、標題、語意及對外授權 | NOT_REQUESTED |

## DL580 現場程序

1. 記錄實際 checkout commit、Python／FFmpeg／FFprobe／字體 SHA-256。確認套件已安裝。
2. 確認 data-root、source-root 為母體本地磁碟；服務帳號可寫 data-root，只給來源必需讀取權限。
3. 沿用 secret binding，key 不進 request／Git／log。API key 至少 24 字元。
4. 先跑 baseline FullCheck，啟動 `scripts/MRL_Start_Video.ps1`，檢查 loopback `/health` 的 worker_alive。
5. 使用已授權的合成測試來源建立 request，透過既有 Bridge `/MRL_exec` 執行 submit 短命令。
6. 用返回 job_id 查詢，必須看到 QUEUED→RUNNING→SUCCEEDED。對 FAILED 檢查錯誤，不改成 PASS。
7. 對完整 ZIP 執行 verify-package；把外部 receipt SHA-256 與下載讀回 SHA-256 比對。
8. 刪除／修改一份**測試副本**中的檔案，驗證封包拒絕；不動原始成品。
9. 以另一 request 建立子版本；父版本內容與 hash 不變，diff 反映修改。
10. 取消任務並重新啟動 worker，確認原任務不被錯誤宣告成功；執行中斷後標示 INTERRUPTED。
11. 驗證同一 root 第二 worker 被拒絕，第一 worker 結束後可接手；鎖檔保留但 OS 鎖釋放。
12. 經既有私有 TLS／Tailscale gateway 在手機實測登入、預覽、MP4 range、下載與 branch。
13. 再跑 FullCheck；前後服務異常依既有復原程序處理。此模組不啟停其他母體服務。

## 恢復與版本保護

SQLite 交易保存入列、claim 與事件；程序崩潰時 OS 釋放 worker 鎖。
下次啟動把 RUNNING 標為 INTERRUPTED，不刪除部分檔案，不重複寫同一版本。
QUEUED 任務繼續處理；已完成版本不可被原地替換。需要重做時 branch 成新版本。
檔案與 SQLite 不是跨檔案系統交易；SUCCEEDED 必須在檔案、稽核、封包及外部 receipt 全部完成後才寫入。
若打包後但狀態完成前斷電，ZIP 留存，任務仍為 INTERRUPTED，不冒充接受成功。

## 證據與限制

文字字幕逐字對應來源，不表示來源本身已經外部查證；標題、圖片與圖形語意仍需 Owner 審查。
只讀載入版本、diff 與 branch 是本模組介面，不表示已修改整個 Wakeup Core 的 TimeMachine。
黑畫面掃描使用 750ms 閾值，逐幕樣本及完整解碼不能保證所有短暫視覺缺陷皆已排除。
母體 law.md 可選讀取並封存 hash；未提供時會如實顯示 NOT_CONFIGURED。
SHA-256 鏈提供可檢查的鏈結，不是身分簽章或司法公證。可信本地 storage／receipt 備份仍屬部署責任。
原始字幕、JSON、圖片與音訊的來源權利分別保留，不因 metadata 的 origin_signature 轉移第三方權利。
