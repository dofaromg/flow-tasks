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

## 2026-10-30 圖譜核對追加（承接使用者確認）

origin_signature: MrLiouWord；canonical_authority: Mr.liou。以上記錄保留為歷史；本節取代「兩圖待裁定、保留 base」的目前狀態。保留 119 個商品節點的原名與既有順序，只更新 231 的合併狀態並追加 30 個已核對來源分支；輸出為 149 nodes / 148 links。既有版本、來源鏈與 14 個原 payload 不變。

五個既有 owned canonical IDs 完整保留：

- `Mrliou_MRL_Naming_Repair_20260908_v1`
- `Mrliou_MRL_OuterAutomation_ProtectedBridge_v1`
- `Mrliou_MRL_SourceToProduct_ParallelLink_v1`
- `Mrliou_MRL_external_sync/ba73806676b4-148dba5ce171`
- `Mrliou_MRL_sync_operations_20260907_v1`

新增 owned 分支同樣依 `source_branch` 保留 `Mrliou_MRL_`，不沿用歷史主線錯序名稱。每項遠端 ref SHA、PR head/base/merge SHA、時間、舊候選值與採用值已追加至 JSON 的 `topology_reconciliation_history[0].entries`。

| Source branch | Adopted status | Evidence |
|---|---|---|
| `231` | merged | [#93](https://github.com/dofaromg/flow-tasks/pull/93) merged into MRL_System_Integration_v1; ref `7579264263156f4d4a227fefe7889a9c038e8a88` |
| `MRL_APIWorks_First_Transaction_Closure_v1` | merged | [#642](https://github.com/dofaromg/flow-tasks/pull/642) merged into main; ref `5a3d0ff2f258cefd49e9485c7b4c8c7e89a3bed7` |
| `MRL_Causal_Optimization_Review_v1` | active | [#643](https://github.com/dofaromg/flow-tasks/pull/643) open; not merged; ref `539e32a166c2fc5f0694a0642b7c7c2f4e6ddcc9` |
| `Mrliou/structure-authorization-reaudit-20260918-r03` | merged | [#653](https://github.com/dofaromg/flow-tasks/pull/653) merged into main; ref `1bc2c30a597b213eb4d9263f8d5818393a74fe10` |
| `Mrliou/structure-index-authorization-20260918-v1` | merged | [#652](https://github.com/dofaromg/flow-tasks/pull/652) merged into main; ref `7fa3d7421ea67f7fd804e50e6c3d2d805e2c3239` |
| `Mrliou_APIWorks_Public_Control_Plane_v1` | merged | [#644](https://github.com/dofaromg/flow-tasks/pull/644) merged into main; ref `db3b691b450905e1651a0660fb8373114feb14ed` |
| `Mrliou_MRL_BYOH_633_Mainline_20260908` | active | [#639](https://github.com/dofaromg/flow-tasks/pull/639) closed; not merged; ref `4e17678e245d3effbb226dcf7c83f7cc6c4cfceb` |
| `Mrliou_MRL_BYOH_Mainline_Integration_20260908_v1` | merged | [#638](https://github.com/dofaromg/flow-tasks/pull/638) merged into main; ref `69733408929099298d09311a09acb85d8105d465` |
| `Mrliou_MRL_Cloudflare_Entry_20260909` | merged | [#641](https://github.com/dofaromg/flow-tasks/pull/641) merged into main; ref `68487f54cb77ade8af6887794caee889c53ba30c` |
| `Mrliou_MRL_neural_sync/0b92d6c0e3eb-34976921701` | active | remote ref verified; PR association unverified; ref `afe4e494f7c797e8cdad16d68f75aca62f9c22bf` |
| `Mrliou_MRL_neural_sync/10248fd51138-34975285661` | active | remote ref verified; PR association unverified; ref `1aa3ec7eefbf25a98b15c995c22b923831a7f120` |
| `Mrliou_MRL_neural_sync/17d3e2e35711-34256954722` | merged | [#640](https://github.com/dofaromg/flow-tasks/pull/640) merged into main; ref `74a4d3e95446ecb9829b90c459fee11172acd4aa` |
| `Mrliou_MRL_neural_sync/51ced55850de-35070531704` | active | remote ref verified; PR association unverified; ref `da134bdd6bb17c77f59c320e04cf0a31fc06bc70` |
| `Mrliou_MRL_neural_sync/5b8ec5fb610e-34932121251` | active | remote ref verified; PR association unverified; ref `572244180717dcfa76391a4470f711640a49be5a` |
| `Mrliou_MRL_neural_sync/5da46c168a6e-35069164303` | active | remote ref verified; PR association unverified; ref `3bf67421317c9e7e326048f5eb5df0f0752ae549` |
| `Mrliou_MRL_neural_sync/848f5d62aa80-35292425260` | active | remote ref verified; PR association unverified; ref `4d347f59b4e5aea3fac7ecb9b002d5290025be11` |
| `Mrliou_MRL_neural_sync/bc648a2dedec-34324512598` | active | remote ref verified; PR association unverified; ref `d49b4bdf9430c5fc6c1019100a121b0959093bb7` |
| `Mrliou_MRL_neural_sync/c4797c441ba6-35942353110` | active | remote ref verified; PR association unverified; ref `0bd5b9fe8b7ec4d0729c8fbe042bd262505edd1e` |
| `Mrliou_MRL_neural_sync/d3bbf2ebcc81-34978699795` | active | remote ref verified; PR association unverified; ref `4c21719962f6a50d5b3aabe779e8536f57586632` |
| `Mrliou_MRL_neural_sync/d43e53dee101-35306164636` | active | remote ref verified; PR association unverified; ref `eb91b9bf2ba31017de0dc2c9684301131b11f6d7` |
| `Mrliou_MRL_neural_sync/dfadd64d5f6d-35304693932` | active | remote ref verified; PR association unverified; ref `57ae7f41bcbaca410961dcffc351b2f9c5a03d4b` |
| `Mrliou_fix/cloud-connector-config-20260926` | active | remote ref verified; PR association unverified; ref `e7ad7676f87c146a57334e0a2c9aa0c95674e9c7` |
| `codex-qgelca` | merged | [#655](https://github.com/dofaromg/flow-tasks/pull/655) merged into main; ref `71ab347b2ffad4be0680c3a07d47edf4faef9d5f` |
| `feat/mrl-apiworks-evidence-entry-v1-20260916` | merged | [#647](https://github.com/dofaromg/flow-tasks/pull/647) merged into main; ref `c95df501717753b3d59d6ee79baa71a31e21d005` |
| `feat/mrl-apiworks-live-and-route-receipts-v1-20260916` | active | [#649](https://github.com/dofaromg/flow-tasks/pull/649) open; not merged; ref `42e6e73a369ecf4bf5576041d0d16e8f8b3f2283` |
| `feat/mrliou-mrl-dual-target-pages-v1` | merged | [#650](https://github.com/dofaromg/flow-tasks/pull/650) merged into feat/mrl-apiworks-live-and-route-receipts-v1-20260916; ref `cfe691dfffdac5312febcccb45cf02b782b5d027` |
| `fix/mrl-apiworks-browser-acceptance-v1-20260916` | merged | [#648](https://github.com/dofaromg/flow-tasks/pull/648) merged into main; ref `b2d1db76f4022894a8012591a2190e93f997a039` |
| `fix/mrl-apiworks-customer-zip-acceptance-v1` | merged | [#645](https://github.com/dofaromg/flow-tasks/pull/645) merged into main; ref `95e23fbd03a5ee27262d13fa88c660426ad7bf33` |
| `fix/mrl-sync-publication-attribution-20260918` | merged | [#651](https://github.com/dofaromg/flow-tasks/pull/651) merged into main; ref `c918fc2005049f2fba74421e2f85b5fc494cdbb2` |
| `fix/mrl-webgpu-ci-allowed-actions-v1-20260921` | merged | [#654](https://github.com/dofaromg/flow-tasks/pull/654) merged into main; ref `4a8481bd5a29a827b09ebe0722833b58ecfe6e7f` |
| `fix/neural-sync-no-feature-writeback-v1` | merged | [#646](https://github.com/dofaromg/flow-tasks/pull/646) merged into main; ref `ba34318704c86bf712c0ad1bef7b497007b735b6` |

`active` 沿用生成器「未證實 merged」的分支顯示語意，不等於 PR 開啟；#639 已關閉未合併。12 個未附 PR 的分支只證實 ref 存在，不編造 PR 或歸屬。其既有 link timestamp 僅保留為歷史觀測時間，不宣稱是分支建立時間。#650、#654 依最新 PR 證據改為 merged。

`MRL_main` 星狀邊沿用既有視覺慣例，不表示 Git ancestry 或都合入 main：#93 實際合入 `MRL_System_Integration_v1`，#650 合入 #649 的來源分支。是否另改邊語意、加入 closed 狀態，以及原 #329 其餘歷史差異，仍待 owner 決定。沒有合併、部署、關閉 #329 或修改 main。

本次本機重跑：authority 8、sync pytest 37、runtime unittest 20、商品 unittest 12，合計 77 項通過。Runtime 32/32 與商品來源 checksum 驗證通過；JSON duplicate keys、canonical/source、Mermaid ID collision、重複邊、端點及確定性生成一致性通過。118 個既有節點與 117 條既有邊（除 231 狀態相關）完整保留，14 payload SHA256 不變。新 commit 的 CI 需推送後另行核對；舊 run 不當作本次驗證。
