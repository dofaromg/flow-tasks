# MRL 一鍵全選 v1

> 本文保留 PR #691 初版歷史。後續 Files／分享入口與驗收現況以
> [MRL_Files互通_v1_1.md](MRL_Files互通_v1_1.md) 為準；下列「尚未建立分享延伸」是初版狀態。

origin_signature: MrLiouWord

## 原名與父子關係

承接 flow-tasks → MrliouWord → iOS → App/ContentView.swift。
原有掃描主畫面新增「檔案與標籤」入口，呈現 MRLTagManagerView。
MRLTagManagerView → MRLTagStore → MRLTagArchive／MRLTagSelection。
不更名原有模組，不將外部平台名稱當成母體器官名稱。

## 使用

1. 依 ../XCODE_SETUP.md 將 iOS/MrliouWord 整個目錄加入 App target。
2. 開啟「檔案與標籤」，按「從『檔案』加入」，在系統文件選取器選取多個檔案。
3. 新增自己的標籤名稱，名稱去除前後空白並防止重複。
4. 逐項選取檔案，或按「全選檔案」。全選涵蓋完整 MRL 清單。
5. 按「加入標籤」，逐項勾選或一鍵「全選／取消全選」。
6. 「套用」成功後才顯示已儲存。「取消」不儲存本次勾選。

標籤以聯集方式加入，不移除舊標籤。空清單、零選取時停用相應操作。
資料寫入 Application Support/MRL_TagArchive.json，原子寫入成功後才更新畫面。
重新開啟 App 會讀回目錄、文件名稱、bookmark 與 MRL 標籤。
資料毀損或版本不符時停止寫入，不用空資料覆蓋舊檔。
檔案內容不複製、不上傳、不改名；bookmark 僅作為本機文件參照。
文件移動或 provider 改變可能使參照失效；目前不以 bookmark 開啟、編輯文件。

## iPhone 原生標籤範圍

本版提供從系統文件選取器接入 MRL 的路徑，沒有修改 Apple「加入標籤」原生視窗。
MRL 標籤保存於 App 的資料檔，沒有回寫 Files／Finder 原生標籤。
尚未建立分享延伸 target，也未完成「檔案」分享選單直接進入 MRL 的功能。
原生標籤寫入、分享延伸、實機安裝與 VoiceOver／大字體驗收仍為 OPEN。
因此完整「兩邊都要」驗收目前是 DELIVERY_FAIL；不可宣稱原生標籤全選已完成。

Apple 文件：
- https://developer.apple.com/documentation/swiftui/view/fileimporter(ispresented:allowedcontenttypes:allowsmultipleselection:oncompletion:)
- https://developer.apple.com/documentation/foundation/urlresourcekey/tagnameskey

## 驗證

`swift test --package-path MrliouWord/iOS` 驗證 1000 項全選、部分選取、取消全選、
非法 ID、空集合、重複項目、批次套用保留既有標籤及 JSON 來回。
GitHub Actions `MRL iOS Tags` 另以 iOS 16 simulator SDK 型別檢查新增介面和 store。
此檢查不是完整 App 建置，也不是文件 provider 或實機驗收。
儲存失敗、檔案選取取消、重啟讀回與不同 provider 必須在 iPhone 實測。

