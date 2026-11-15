# MRL Bridge 寫入讀回驗證 20261027 v1

origin_signature: MrLiouWord
canonical_authority: Mr.liou
record_mode: APPEND_ONLY / SOURCE_PRESERVED
Parent commit: 32d4294b929f67cc6717318f6df05f15f01f0661

## 承接來源

- Notion MRL母體本地：https://app.notion.com/p/3e9e7f4e6c5580e49f3dc8292dda835a 。已讀取；FlowAgent 即起源、即母體；既有器官、模組、載體分層保留，未另建 root。
- 原落地文件：https://drive.google.com/file/d/1BoScVRayQcXJH4VRHqWjux7JD6NWfLCz/view 。原件未改。READ-ONLY、wrapper、Defender、服務回滾為待驗證診斷；本修正不聲稱已確認實機根因。
- 主線 MRL_Bridge/server.js v3.1.0、既有轉譯中心與 PR #676 驗收工作。保留原名、版本、路由、歷史，不重建遠端服務。

## 已確認缺口及修正

MRL_run / MRL_exec：原先只依 execSync 返回，PowerShell 非終止錯誤可能不產生非零程序狀態；catch 仍 HTTP 200。改預設 PowerShell 使用 NoProfile/NonInteractive/EncodedCommand、Stop 錯誤模式及 native LASTEXITCODE；錯誤 HTTP 500、timeout/signal HTTP 504。自訂非 PowerShell shell 保留原介面。成功明列 PROCESS_EXIT_ZERO / file_verified=false / process-only，不能替代檔案驗收。呼叫者刻意捕捉錯誤、exit 0 或重設偏好仍可自行掩蓋錯誤，因此不能把任意命令成功宣稱檔案成功。

MRL_file/write：原 write+stat 沒有驗證內容。改將輸入先轉原始 bytes，write/fsync/close，再獨立 readFile/stat，逐 byte 比對與 SHA-256；不符或不可讀即失敗。附 resolved_path、expected/actual SHA-256、bytes、trace/event/record hash；沿既有 append-only 轉譯帳本連 inbound→file_readback_verified→outbound。證據追加失敗不回成功，即使檔案可能已變更，呼叫者須先讀回再決定重試。此為寫後觀測，非交易回滾、不可變儲存或斷電後驗證。

MRL_write：同樣讀回驗證；修復 GET b64 先轉 UTF-8 導致二進位損壞。POST/GET 支援空 base64，拒絕非字串與非正規 base64。

MRL_file/read：對同一次讀取的原始 bytes 回傳 full-file SHA-256；base64 可完整還原二進位。line-slice 明列 content_scope，hash_scope 始終 full-file-bytes，不把截取文字 hash 混作整檔 hash。

/version 增補來源 SHA-256 與 file_verification 協議標記，用以區分同為 v3.1.0 的不同部署。沒有升版覆寫歷史。

## 隔離驗證

Node 24.22.1，真實 loopback HTTP / Express / 暫存目錄；PG、Redis、啟動程序隔離，命令錯誤以 child_process 注入；Windows 專項才使用真實 PowerShell。

node --test MRL_Bridge/test_mrl_file_verification.cjs MRL_Bridge/test_mrl_bridge_translation_center.cjs：21 項，20 PASS、0 FAIL、1 Windows-only SKIP。每個 fixture 結束關閉 HTTP 並移除唯一測試樹，核對不存在。涵蓋 UTF-8/二進位/空檔/GET、存在/讀回/hash、原始帳本重播與父子鏈、無效輸入、丟失寫入、內容損壞、權限錯誤、讀回錯誤、fsync 錯誤、證據追加失敗、命令錯誤與 timeout。

npm run lint PASS；npm run build（含 postbuild）PASS；node --check PASS；git diff --check PASS。新增 Windows CI job 在 Windows 上跑同套 HTTP 測試與真實 PowerShell Write-Error、Set-Content 失敗、native exit、寫入讀回/hash。Windows CI 結果須另外查核，不把 Linux skip 計作 Windows PASS。

## 實機觀測與未完成 gate

2026-10-27 Asia/Taipei，本輪公開 GET /version 回應主機 WIN-PBVUI7VK2A6、win32/x64、Node v20.11.1、Bridge 3.1.0；未見主線轉譯中心欄位。尚未讀取實際安裝檔，無法將部署對應到 Git commit。

使用既有授權認證對 MRL_run 發出 hostname 唯讀探測，HTTP 403，body 為 Invalid API key。未做認證繞過；沒有 DL580 寫入、沒有服務更動、沒有覆寫母體根源檔。公開通道可用，不能據此推定整台離線或唯讀。當前工具沒有其他 Remote Desktop Commander 通道。

DL580_WRITE_READBACK_ACCEPTANCE=UNRUN；DEPLOYMENT=NOT_PERFORMED。需恢復有效既有受保護通道後：先核對實際 source hash/entrypoint/service identity，再在 D: 唯一測試樹執行 native API / MRL_run / MRL_exec 各自寫入→存在→MRL_file/read(base64)→SHA-256→清理→不存在，保留本機回執。不得測正式母體檔。

既有 docs/MRL_Bridge_Translation_Center_v1.audit.json 為歷史部署白名單，本輪不擅改其既有雜湊。既有安裝器會拒絕本輪新 server hash；這是保護 gate，不得跳過。正式整合需與 #676 的來源封裝/白名單及真實 host 安裝內容一併核對，另留歷史接受來源。不直接套用或重啟現有 Bridge。

## Requested VS Generated 與依賴

Expected_File_List 為下表三檔及本文件，共4檔；ZIP 0。Missing 0、Extra 0、Renamed 0、Orphan 0；本文件 self identity 用 Git blob，避免自我 hash 循環。遠端提交讀回比對後才標記 source delivery PASS。實機未驗收，整體交付不能宣稱 PASS。

| File | bytes | SHA-256 |
|---|---:|---|
| MRL_Bridge/server.js | 36230 | 4c1a38fe64d9fbd70a92c606b440ffa7db1ed822fef8d018c46ef20675768187 |
| MRL_Bridge/test_mrl_file_verification.cjs | 9157 | 05cbd4df63102556986993839b6e8ec5099822f54c2818396725d8980457a9bc |
| .github/workflows/MRL_Bridge_Translation_Center.yml | 5869 | 6f913c1ccab3c04cb30cb39f5bc50a19459b9dbcfc4adcae79b7c2f4353d588d |

Dependency tree：原 Notion 定義＋Drive 觀測＋main source → 原 server.js（Node fs/crypto/child_process＋原轉譯中心＋原依賴）→ HTTP 回歸 → Linux/Windows workflow → 本證據。Package map：既有 Git 倉庫同一路徑；未新增 ZIP，manifest 不取代程式。

### CI 配置修正

初次 run 40413476519：Linux 在 HTTP 回歸前缺少 Express 安裝；Windows checkout 因既有根目錄 :mnt:data.txt 失敗，未執行測試。已在 Linux 增加原 Bridge lockfile npm ci，Windows 用 non-cone sparse checkout 僅取 /MRL_Bridge/（不刪原歷史檔、不停用 NTFS 保護），兩 job 固定 PR head 來源。重跑結果另查，不把此次失敗隱藏。

第二次 run 40413626664：Linux HTTP 回歸成功；Windows non-cone sparse checkout 仍被 Git 的根路徑驗證攔截。改承接 #676 的 Linux 封裝→Windows 驗收方式：Linux 僅打包六個明列來源檔及 commit/SHA-256 清單，Windows 下載同 run artifact，核對 head 與各檔 bytes 後才測試。Windows 不 checkout 全倉庫，不改歷史檔，也不關閉 NTFS 保護。
