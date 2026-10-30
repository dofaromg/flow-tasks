# MRL PR #329 衝突修補 v1

origin_signature: MrLiouWord
canonical_authority: Mr.liou

本次從商品分支 c3081301d84e7ad73135d32fc29712b426a1c33e 建立獨立工作分支，將主線 9116b578eca6ec6bd66bc3030f801a0226264b26 的 14 個相關檔案逐位元移植；另新增本說明與 MRL_conflict_evidence.json，共 16 個交付檔案。未將 170 個歷史差異全部合併，未更動 main 或原商品分支，亦未改寫歷史。

## 用途及血緣

原 PR 2026-01-27 建立，標題 Or、內文為未填模板；當時審查摘要描述歷史文件、組態與工具腳本。2026-10-19 曾變更 base。無足夠證據認定原 PR 全部歷史內容仍需併入商品。共同祖先、兩側 SHA、170 個路徑與 11 個衝突的 Git blob 均記錄在證據 JSON。

## 實際修補

- 商品封裝維持倉庫目錄結構，ZIP 可重現、完整回讀核對，交付 checksum sidecar。
- 補入持久化節點回執與重播驗證，承接主線 #688、#690；版本依來源維持 rc3。
- 母體 hash-chain 與 Passport 只按 LF 分割 JSONL，保留模型文字內 Unicode 分隔符。
- CI 使用實際 checkout SHA 命名 artifact，缺檔即失敗。
- 神經同步只發佈獨立 candidate，不直接回寫 feature/source 分支。

## 語意衝突保留

`neural-links/branch-map.json` 與 `neural-links/synaptic-graph.mermaid` 保留商品分支現值；主線版本與共同祖先仍可由證據中的 immutable SHA/blob 讀取。Root Owner 需裁定商品視圖或主線視圖及重新生成策略。本次不以文字衝突消失代表 canonical 拓樸已核准。

原 #329 保持開啟；本修補 PR 只承接已確認的相關內容。是否關閉原 PR、如何處理其他歷史差異與拓樸，仍交 Root Owner。沒有聲稱原 #329 已可合併。

## 驗證與回復

商品 unittest 12 項、母體 runtime unittest 20 項及同步 pytest 37 項通過（共 69 項）。商品來源清單、父 runtime 32 檔、SHA256 與 ZIP 內容核對通過；持續整合結果以本 PR 實際 head 為準。

證據 JSON 列出 14 個 payload 的路徑、大小、SHA256、來源、依賴樹與未移植項目。兩個證據文件為新增審查資料，不屬商品封包，避免破壞既有商品檔數與 checksum 契約。

正式合併須依分支保護與 Root Owner 核准。合併後可 revert 本次修補 commit；原始兩側版本仍由 Git 提供。未部署任何服務。
