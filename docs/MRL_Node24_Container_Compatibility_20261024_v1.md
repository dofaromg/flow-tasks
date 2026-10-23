# MRL Node24 容器相容性查核 v1

origin_signature: MrLiouWord  
canonical_authority: Mr.liou  
核對日期：2026-10-24，Asia/Taipei  
Parent/source：dofaromg/flow-tasks main `80084033894dacc01e0d0fde54a553202d8e41f6`

## 來源與版本承接

本次沿用 MRL_Bridge_API v3.1.0、MRL_Product_v1、MRL_RuntimeOS_EnterpriseRuntimePlatform_CoreExecutable_v1_4_0 與 MRL_Product_Motherbody_Engineering_v1 前端，保留所有原始名稱、套件版本、啟動入口及既有鎖定檔。Bridge 歷史 MANIFEST、轉譯中心 audit 與已封存 hash 不改寫；本次證據另存同名 audit JSON。

歷史記憶用於定位，實際修改以本 parent 的原始檔為準。Bridge 對應 DL580 歷史 D:\mrl\bridge\server.js、7800；RuntimeOS Docker 契約為 8788，歷史本機服務曾記錄 8790／v1.4.1，不能將兩者視為同一部署或改寫現場設定。

官方來源：[2026-10-21 Node.js 安全公告](https://github.com/nodejs/nodejs.org/blob/main/apps/site/pages/en/blog/vulnerability/october-2026-security-releases.md)，讀取 blob `6affb2b3ca3460ff5c8343d9d9064d8d3b442952`。Node 24 修補候選為 `24.22.1`。Linux x64 tar.xz 依官方 SHASUMS256.txt 核對：`6c172a9ab6718f7b801fb5a7bd486af2ee5e32758086a04b84fcce2aa77095e6`。本次未升級 DL580 Runtime。

## 四組件逐一裁定

| 組件 | 本次處理 | 鎖定與原生依賴 | 保留啟動契約／限制 |
|---|---|---|---|
| MRL_Bridge | node:20-alpine → node:24.22.1-alpine；補入 server.js 必需的 mrl_bridge_translation_center.cjs | npm ci，lock v3；express 5、pg、ioredis，鎖定樹未見原生 addon | node server.js、7800、MRL_BRIDGE_API_KEY、PG/Redis 不變；本機測試為 Linux glibc，Alpine musl 須映像 CI 再驗 |
| MRL_Product | **保留 node:20-slim** | lock v3，better-sqlite3 9.6.0；現行 Dockerfile 只 COPY package.json 並 npm install，未使用現存 lock，建置可漂移 | /entrypoint.sh → DB init → backend/server.js、3000、/health、storage/log volumes 保留。原生安裝／DB 往返／持久化及 test-mode payment 未通過驗收前不得換基底；不得使用正式金流 |
| MRL_RuntimeOS v1.4.0 | node:20-bookworm-slim → node:24.22.1-bookworm-slim | dependencies 為空，lock v3；既有 npm install --omit=dev 不變 | MRL_API/MRL_RuntimeServer.js、MRL_PORT=8788、MRL_HOST=0.0.0.0、MRL_AUTH_REQUIRED=false 不變；既有 auth 設定非此次新增 |
| MRL frontend | **保留兩階段 node:20-slim** | root lock v3：Next 15.5.25、sharp 0.34.5；兩者 engines 接受 Node24，仍不足以證明完整容器相容 | 3000、node server.js、/api/mrl/status 不變。Docker COPY 缺少現行 postbuild 所需 scripts/Mrliou_MRL_opennext_build.mjs；健康檢查使用映像未安裝的 curl；status 無 runtime snapshot 時回 503。需獨立解決真實快照供應及健康語意，不造假資料或強改 200 |

相關 CI `.github/workflows/mrl-pr-validation-v2.yml` 精確指定 `24.22.1`，保留其既有 integration/comprehensive 內容。新 workflow 僅 build/test，不 push image、不部署：Bridge 映像配合隔離 PostgreSQL/Redis 驗證 7800；RuntimeOS 映像執行既有 acceptance 及 8788 health。

## 已取得驗證

- 精確 Node `v24.22.1`：Bridge `node --test MRL_Bridge/test_mrl_bridge_translation_center.cjs` **9/9 PASS**。
- 精確 Node `v24.22.1`：Bridge 實際啟動，GET `127.0.0.1:7800/version` **PASS**；驗證 node、3.1.0 與 MrLiouWord。PG/Redis 在本機未提供，不將此視為資料庫整合通過。
- 精確 Node `v24.22.1`：既有 RuntimeOS `MRL_Acceptance/MRL_Acceptance_TestSuite.js` **status PASS**；另啟動 8788 `/api/mrl/health`，產品名稱、origin_signature、status **PASS**。在隔離副本執行，產生的儲存及 job 資料未寫回來源。
- Python 關聯回歸：Bridge translation、connectors、Mobius closure **65/65 PASS**。
- `python test_integration.py` **PASS**。
- `python test_comprehensive.py`：System Integration、Particle Core、Flask API PASS；**Task Processor FAIL**，4 task passed 但 1 failed validation area，當次 repository health 子項 npm lint/build 失敗（當時 root dependencies 尚未就緒）。不得只依腳本最終 exit 0 宣告全綠；保留此既有全域阻擋。
- 兩份 workflow YAML parse **PASS**；變更 diff whitespace 檢查 PASS。
- 本機無 Docker／Podman／BuildKit，**映像 build 未在本機執行**。新 workflow 結果需以 PR head 的 Actions 原始回執核對；workflow 存在不等於測試已通過。
- 精確 Node v24.22.1：root `npm ci --ignore-scripts` PASS（911 packages）、`npm run lint` PASS、`npm test -- --runInBand` **8 suites / 87 tests PASS**。ignore-scripts 安裝不驗證所有安裝腳本；不能替代映像建置。root build 與 Product 原生依賴進一步驗證另行記錄。

暫存解壓曾出現不完整 Node 二進位／segfault，後改在 /tmp 隔離解壓並確認 v24.22.1 後才執行上述通過項目。早期系統 Node24.19.0 的安裝嘗試不列為精確候選通過證據。Product 早期安裝受 node-gyp header extraction 的 fchown EINVAL 阻擋，不能據此斷言套件必然不相容；後續仍須實際建立 Database、schema、SQL、持久化及服務往返。

## 審查與交付 Gate

原始碼審查可進行；容器驗證、Product／前端升級、DL580 驗收互相分離。即使 hosted image CI 通過，也不代表 DL580 已部署。

正式切換必須在 DL580 以實際 image digest、實際 process/container、服務埠、better-sqlite3（如適用）、卷持久化、重啟及 rollback 驗證，並取得 Root Owner 明確核准。本次不執行主線合併、映像發佈、正式容器切換、全域 PATH／獨立 Runtime／現行服務修改。

回復方式：僅 revert 本 PR 的候選 Dockerfile／CI commit；既有 Node20 來源可由 parent 精確還原。Product／前端原檔與全部 lock/package 檔案均保留。

## Requested vs Generated

Expected_File_List 為 audit JSON 列出的六個檔案；四組件皆已查核（4/4），兩個容器升級候選、兩個保留並有風險紀錄。依賴與 package map 同時列於 audit，逐檔記錄大小、SHA-256、before SHA-256、parent/source；audit 自身以 Git blob 身分核對，避免遞迴自雜湊。

來源檔交付核對與執行驗收分開：Missing/Extra/Mismatch 必須為 0 才可標記來源 DELIVERY_PASS；**整體 runtime/deployment DELIVERY_PASS 尚未成立**。未要求 ZIP，因此 ZIP 比對不適用；實際 Dockerfile/workflow 已交付，audit 不替代內容。

## 追加驗證 2026-10-24（保留初次回執）

Node24.22.1 root production build（含 postbuild）PASS。既有 standalone 在 Node24.22.1、隔離 3300 埠啟動成功，/api/mrl/status 回 200（讀取來源樹既有 snapshot）；此回應不是 DL580 即時觀測，不能當作實機驗收。缺快照時回 503 仍為原始碼契約。Product 精確版本 npm ci 無預編譯 binary，node-gyp header 解壓遭 fchown EINVAL；改用隔離 headers 進一步嘗試編譯，未宣告相容。

[首輪映像 CI](https://github.com/dofaromg/flow-tasks/actions/runs/39987510501)，head ce09066bd4cdc1a88829e6c7ea863ca4cddae7ec：RuntimeOS image build 與容器內 acceptance PASS，健康輪詢在啟動瞬間遭 curl 56 connection reset；Bridge 在 Redis service 建立階段因 health-cmd 單引號解析 invalid reference format，尚未執行映像 build。修正測試框架為雙引號 health-cmd 與有界 retry-all-errors，保留原服務契約；下一輪以新 head 驗證，首輪結果不改寫為成功。


[第二輪映像 CI](https://github.com/dofaromg/flow-tasks/actions/runs/39987796225)，head `f31d2f7d31a6b5b9be16e73092c7a81e75c4fe6c`：Bridge Alpine build、精確 Node24.22.1、9 regressions、7800 version、PG/Redis health **全部 PASS**；RuntimeOS Debian build、精確 Node24.22.1、既有 acceptance、8788 health **全部 PASS**。本次兩個 Dockerfile 已在 hosted Linux Docker 驗證，仍非 DL580 驗收。

GitGuardian 將首 commit 工作流內固定的 CI-only 測試字串標記 Generic Password（incident 38907116）。這些值只曾供此隔離測試容器使用，非既有服務憑證；現行工作流改為 openssl 隨機生成、add-mask、job env 傳遞，測試後銷毀資料庫容器。既有 commit 不重寫，也不替 GitGuardian 裁定／關閉歷史 incident；若掃描仍針對舊 commit 報失敗，保留 owner review 阻擋。新 head 必須再驗證，不將第二輪結果當作新 head 結果。

第二輪來源讀回比對 6/6（首輪也為 6/6），實際 Git compare 只包含 Expected_File_List，沒有 package／lock／Product／前端或正式服務設定差異。原生編譯還在隔離副本測試，Product 保留不變。


## 原生模組最終結果與最新來源核對

2026-10-24 隔離 Product 副本以精確 Node `v24.22.1`、現有 package-lock 執行 `npm ci`；預編譯 binary 不存在，先排除 header 解壓限制，再用 `/tmp/node-v24.22.1` headers 編譯。**better-sqlite3 9.6.0 source build FAIL**，make exit 2／npm exit 1；主要錯誤包含 `v8config.h: C++20 or later required`、舊建置標準不接受 `requires`／`std::ranges`，以及 V8 `Local<v8::Primitive>` 型別轉換錯誤。這證明現存原生建置路徑未通過 Node24.22.1，不能只改 FROM；未修改套件、lock、schema 或資料庫。後續應獨立評估原生套件升級並驗證資料庫往返／持久化／服務啟動，而不是強行在此次 PR 全面替換。

原生安裝失敗後未執行 DB／金流整合，不將缺少模組時的空 `npm rebuild` 成功訊息當作相容證據。

[最新映像驗證回執](https://github.com/dofaromg/flow-tasks/actions/runs/39988073299)，head `e72c250c81fdbf3db4d44e9b76197eef1eccba6d`：改用隨機短期測試憑證後，Bridge、RuntimeOS jobs **均 PASS**。此 head 六個檔案逐檔讀回一致、compare 僅有預期六檔、hash／依賴均已核對：Missing 0、Extra 0、Mismatch 0、Coverage 100%，**來源 DELIVERY_PASS**。部署／實機 DELIVERY_PASS 未成立。

本追加僅更新報告及 audit 的原生失敗結果；容器、工作流、package/lock 與上述驗證 head 相同。追加 commit 的來源讀回與 checks 仍須分別核對。
