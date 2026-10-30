# MRL Files 互通 v1.1

origin_signature: MrLiouWord

來源血緣：flow-tasks → MrliouWord → iOS → PR #691。
承接 head `3075350761f9e6053ff4262022fea40a090d9ef4`，保留原名與 v1 JSON，沒有重新命名或刪除原有模組。
查核日期：2026-10-30（Asia/Taipei）。

## 公開 API 權限與原生標籤

| 情境 | 公開方式／實際邊界 | 本次交付 |
|---|---|---|
| Files 多選文件進入 MRL | 系統 fileImporter；僅取得使用者授權的 URL，security scope 成對釋放 | 既有文件參照登錄，分享匯出時 NSFileCoordinator 讀取 |
| Files 分享選單進入 MRL | com.apple.share-services extension、App Group；不是任意讀取其他 App 容器 | 新增真正 extension target 並嵌入 App；收件匣副本持久化後再由主 App 登錄 |
| MRL 文件回到 Files | UIActivityViewController 的「儲存到檔案」由系統與 provider 決定是否提供 | 分享所選文件副本與 MRL_標籤.json，保留檔名與內容 |
| Files 原生「加入標籤」視窗一鍵全選 | 沒有找到可供第三方替換該原生視窗或控制其勾選狀態的公開入口 | 不實作私有介面；Files 先選文件 → 分享至 MRL → 在 MRL 全選標籤 |
| iPhone 任意 provider 原生標籤寫入 | URLResourceValues.tagNames 不能視作跨平台、跨 provider 的保證；本案沒有使用它回寫 iOS 原生標籤 | 未完成；替代為可攜 MRL 標籤封包，不宣稱 Files 系統標籤已變更 |
| 自有 File Provider 的標籤 | tagData 是抽象資料；setTagData 是自有 provider 接收使用者標籤更新的 override，不是取得其他 provider 的通用寫入權限 | 本次沒有建立 MRL File Provider domain，不偽造 opaque tagData、不反向解析 Apple 私有格式 |
| macOS Finder 標籤 | macOS 有 URLResourceValues.tagNames 公開屬性，但仍受檔案權限與儲存系統支援限制 | 本次為 iOS 工程，未交付 macOS Finder 回寫模組 |

Apple 官方依據（查核時可取得的公開文件；「沒有找到」屬本次 API 調查結論，不宣稱永遠不可能）：
- https://developer.apple.com/documentation/foundation/urlresourcevalues/tagnames
- https://developer.apple.com/documentation/fileprovider/nsfileprovideritemprotocol/tagdata
- https://developer.apple.com/documentation/fileprovider/nsfileproviderextension/settagdata(_:foritemidentifier:completionhandler:)
- https://developer.apple.com/library/archive/documentation/General/Conceptual/ExtensibilityPG/Share.html
- https://developer.apple.com/documentation/foundation/nsitemprovider/loadfilerepresentation(fortypeidentifier:completionhandler:)
- https://developer.apple.com/documentation/uikit/providing-access-to-directories
- https://support.apple.com/en-ie/guide/security/sec1a976c067/web

loadFileRepresentation 提供的暫存檔在 callback 返回後可能被刪除，因此同步複製後才返回。
分享 extension 不強制啟動 containing App；使用者關閉分享畫面後開啟 MRL 即可收件。
分享副本不是原件原生標籤的鏡像，來源標籤不會自動被匯入。

## 操作與可驗收替代

1. 開啟 `MrliouWord.xcodeproj` 的 MrliouWord scheme。App 與 MRLShareExtension 都需設定同一個開發團隊，並註冊 `group.com.mrliouword.app` App Group；沒有此 entitlement 時顯示錯誤，不假裝分享成功。Bundle IDs 需與簽署帳號註冊值一致。
2. Files 選取多份普通檔案 → 分享 →「加入 MRL」→ 按「加入 MRL」。顯示成功／失敗數；不支援資料夾、符號連結或未提供相容 representation 的來源。每次最多 1000 份。
3. 回到 MRL「檔案與標籤」，自動讀取或按「讀取分享收件匣」。檔案副本存於 Documents/MRL_匯入/來源 UUID/MRL_Payload/原檔名，Files 可透過 App 文件目錄看到它們。
4. 全選文件 → 加入標籤 → 全選／取消全選／逐項選取 → 套用。既有標籤保留。
5. 「分享所選文件與 MRL 標籤」產生文件副本和 `MRL_標籤.json`；在系統分享面板選「儲存到檔案」。相同檔名放入不同 UUID 暫存子目錄，避免覆寫；最終 provider 的儲存對話由使用者決定。
6. 在另一個 MRL 安裝先加入文件，再選取目標文件 →「匯入 MRL 標籤到所選文件」→ 選 JSON。只有原檔名與 SHA-256 同時符合才合併，顯示配對數。內容改變或改名不自動套用。JSON 不含 bookmark、本機路徑或權限。

## 儲存與回復

主檔仍是 Application Support/MRL_TagArchive.json，版本 1；新增可選 sourceRecord，舊版沒有此欄位仍可解碼。
sourceRecord 連到來源 UUID 目錄的 `.MRL_source.json`，記錄 origin_signature、來源 UUID、原名、收件時間、複製模式與原生標籤未匯入狀態。
分享 extension 只寫 App Group/MRL_Inbox；主 App 獨占標籤主檔，避免兩程序覆寫。每份文件先 staging，再原子更名為 ready。
主 App 完整複製後才登錄，登錄成功才清除共享收件匣。中途終止可重試，同一路徑不重複登錄。
損壞、未知版本或來源標記不同的主檔停止寫入。寫入失敗不更新 archive，不顯示過時成功訊息。
可攜封包的 originSignature 是格式血緣標記，不是數位簽章或可信來源證明；只接受使用者主動選取的封包。封包最大 16 MiB，限制筆數與欄位長度。
bookmark 失效時明確報錯，請從 Files 重新選取，不暗中變更來源。
匯出與雜湊採分塊讀取；目前準備操作仍在主執行緒，大檔或慢速雲端 provider 可能阻塞畫面，屬實機效能驗收項目。
分享部分失敗時已成功副本保留，畫面顯示數量；整批重試可能產生另一份副本，不宣稱跨批去重。

## 驗證層次與完成閘門

- 程式測試：Swift package 核心選取／封包往返／同名異內容拒絕／冪等合併／未知版本與來源拒絕；另跑 macOS store 回歸（重啟、損壞、未知版本、來源不符、寫入失敗、分享副本與 staging 清理）。
- SDK 型別檢查：iOS 16 模擬器 SDK 的 models/store/分享共用檔/介面。
- 完整建置：xcodebuild 建置 App 與嵌入 extension，不簽署；這不證明有效 provisioning 或實機可見性。
- iPhone 實機：待驗收 Files 分享入口、App Group 簽署、iCloud／On My iPhone／第三方 provider、離線／延遲下載、分享取消、部分失敗、程序終止後收件、重新啟動、撤銷權限、VoiceOver／最大字體、1000 份文件、大檔與同名不同內容。
- 原生標籤視窗與原生標籤回寫：未實作；需 Root Owner 接受上述替代方式，不能以 CI 成功標記原生回寫完成。

完整原始「兩邊都要」含原生標籤修改與實機驗收仍為 DELIVERY_FAIL。
工程可實作範圍以 CI 與逐檔證據判定，不將 Cloudflare 部署檢查與 iOS CI 混為一談。
Root Owner 決定是否合併；本次不合併、不部署、不提交 App Store。

回滾：保留本次 commit 與原始 v1，必要時 revert 工程 commit。先備份 Documents/MRL_匯入、App Group/MRL_Inbox 與原標籤 JSON；不刪使用者資料。


## 同分支補強（2026-10-30）

承接 `43e8a3a1bc190f44fa0518886c8691f1fa96c9b3`，保留其 Xcode 專案、分享延伸、
MRLTagTransfer、sourceRecord 與名稱＋SHA-256 配對方式，不另建第二套標籤封包。

- 登錄前只解析既有 bookmark 一次，批次內與重新開啟後均以標準 URL 去重。
- 成功原子寫入會清除過往錯誤；每次操作先清除舊成功訊息，取消選檔不當成故障。
- 主檔若包含重複文件 UUID／標籤目錄鍵，停止寫入保留原件。
- 可攜封包輸出與輸入共用 16 MiB 上限；拒絕未正規化標籤，避免目錄與文件標籤分歧。
- 沿用父版本的 MRL_Payload 內容／溯源隔離，原名為 `.MRL_source.json` 的文件也保留原內容。
- 新增實際寫入失敗再恢復、記憶體／磁碟原件保留、重複 UUID、批次去重、來源側檔衝突、
  封包輸出超限與空白標籤回歸；沿用既有 macOS CI，不以型別檢查取代完整 App 建置。

本次補強預期 6 檔：本文件、MRLTagStore.swift、MRLTagTransfer.swift、MRLTagManagerView.swift、
IntegrationTests/MRLTagStoreRegression.swift、Tests/MRLTagTransferTests.swift。
無刪除、更名、第二份 App target 或平行標籤格式；以 Git commit 交付，ZIP 不適用。
逐檔雜湊與 Requested/Generated 對照附於 PR 說明。完整原始需求與實機閘門仍維持上節狀態。

## 2026-10-30 接續修補（父系 7a47d14）

保留 PR #691、原名、v1 格式與 origin_signature: MrLiouWord。

- 已核對前版將每次操作 notice 清空、register 一次建立 bookmark 索引，以及損壞／未知版本／來源錯誤／寫入失敗保留原資料的回歸。
- 分享 representation 優先使用 provider.suggestedName；拒絕斜線、反斜線、空白名稱、點目錄與 NUL，非法名稱回退暫存 basename。
- 新增標籤限制 1024 UTF-8 bytes；批次套用與封包聯集限制每文件 1000 標籤，拒絕時不提交候選資料。
- 登錄時每個既有 bookmark 只解析一次並更新過期 bookmark；文件操作時也持久化更新，寫入失敗停止操作。
- 收件匣以 SHA-256 核對 payload 與來源紀錄；缺少副本補回，衝突保留兩側原件且不刪收件匣；單份失敗不阻止其他收件。只登錄本次 incoming payload，不將目的地額外檔案視為來源。
- 新增有效封包 encoded round-trip、標籤上限不可變更、真實收件匣至 store、衝突保留與遺失副本重試、suggestedName 與非法名稱回退測試。

Apple 公開文件再次核對：
- https://developer.apple.com/documentation/foundation/nsitemprovider/suggestedname
- https://developer.apple.com/documentation/foundation/nsitemprovider/loadfilerepresentation(forTypeIdentifier:completionHandler:)
- https://developer.apple.com/documentation/fileprovider/nsfileproviderextension/settagdata(_:foritemidentifier:completionhandler:)

setTagData 是 File Provider extension 接收其項目標籤變更的 override，不提供任意第三方 provider 的原生標籤寫入權限。沿用 Files 分享入口與可逆 MRL 封包；不宣稱修改系統標籤介面。

仍待完成：大檔 copy／digest 的背景執行、可重現的過期 bookmark 測試、Apple 簽署與 App Group 實際 provisioning、iPhone／多 provider／效能驗收。主檔保護與跨文件標籤行為由 macOS CI 執行；本機沒有 Swift／Xcode，不將靜態檢查列為編譯成功。完整需求 DELIVERY_FAIL，待 exact-head CI 及上述驗收補齊。

本次交付依賴：Selection／Transfer → Store → Manager；Share controller → Inbox → Store；Tests／IntegrationTests → 既有 mrl-ios-tags workflow。工程已引用各檔，無新增 target 或遺失依賴，無重新建立相同功能。交付形式為既有 Git 分支，ZIP 不適用。
