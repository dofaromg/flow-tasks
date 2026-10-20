# MRL GitHub ↔ Notion 接線

origin_signature: MrLiouWord
canonical_authority: Mr.liou
parent_module: MRL_FlowEditBridge_v0.2
record_mode: APPEND_ONLY / SUPPLEMENT_EXISTING

## 既有節點與接線範圍

Notion 總覽是定義根源；GitHub 是工程來源；母體本地頁保存工程回執。
本增補提供 GitHub PR metadata → Notion 追加 → Notion API 讀回 → 本地回執。
反向讀取保留 Notion 頁面身份與編輯版本作為 upstream reference；不聲稱完整頁面匯出或任意檔案雙向同步。
初始監測來源為本輪工作脈絡中的 dofaromg/flow-tasks PR #677；可在配置明列其他 PR。
PR 是否 merged 使用 GitHub 原值，不把分支測試／讀寫成功當成正式部署驗收。

既有來源：
- `MRL_Bridge/README.md`：DL580 :7800 入境通道，出境使用 FlowEditBridge。
- Dropbox `/MRL_FlowEditBridge_v0/MRL_FlowEditBridge_v0.2/MRL_Notion/MRL_Edit.py`：2026-05-17 原模組有 append_paragraph/get_page 等真實 API 實作。
- `adapters/notion_adapter.py` 與 `adapters/github_adapter.py` 保留原樣；前者只有本地匯出和連線探測，後者自述 placeholder，不能冒充已完成同步。
- `scripts/ping-sync.ts` 有真實 Notion 建頁，但不是既有母體頁的工程證據回填。

新程式在既有 adapters 目錄增補，沿用 FlowEditBridge 的 `/blocks/{page_id}/children` 追加契約；沒有匯入或改名 Dropbox 原件。
Dropbox fetch 是文字擷取來源，部分註解有編碼差異；不聲稱取得原始 bytes／SHA-256。

## 私人 DL580 執行

從本 PR 的 exact commit 取得 adapter 和 JSON 配置，放在既有 flow-tasks checkout。
僅使用 Python 3.10+ 標準函式庫，無新增套件。憑證僅從既有本機環境讀取：
`GITHUB_TOKEN`（目標 repo read）與 `NOTION_TOKEN`（兩個指定頁面 read、母體頁 insert）。
不從 ChatGPT 連接器抽取 token，不把 token 放入 git、命令參數或回執。
沒有憑證時 exit 1，不以跳過當成功；本次沒有變更憑證或 Notion 分享設定。

在 DL580 的現有 checkout 先執行 plan，再 apply：

```powershell
& 'D:\MrlToolchain\python\python.exe' adapters/mrl_github_notion_bridge.py --config config/MRL_GitHub_Notion_Bridge.json --output-dir 'D:\mrl\bridge\logs\MRL_GitHub_Notion'
if ($LASTEXITCODE -ne 0) { throw 'MRL bridge plan failed' }
& 'D:\MrlToolchain\python\python.exe' adapters/mrl_github_notion_bridge.py --config config/MRL_GitHub_Notion_Bridge.json --output-dir 'D:\mrl\bridge\logs\MRL_GitHub_Notion' --apply
if ($LASTEXITCODE -ne 0) { throw 'MRL bridge apply or readback failed' }
```

執行檔路徑承接 Notion 既有記錄，安裝前仍需核對實機；沒有重新安裝 Python、變更 PATH 或重啟 Bridge。
此程式是出境一次性工作，不開 inbound listener，不更改現有 Bridge、Tunnel、Tailscale、DNS、排程或其他雲連接器。
本輪不新增雲端 runner 保存私人 Notion 資料；定時觸發須沿既有本機調度器接線並驗收。

## 防重與失敗處理

同一輸出目錄的 lock 避免本機併發；必須共用一個輸出目錄，不能多節點同時寫同一頁。
所有頁面頂層 blocks 完整分頁查找 deterministic SHA-256 marker；相同內容不重寫。
同 marker 不同內容、重複 marker、讀回缺失均失敗；不刪除歷史、不覆寫正文。
POST/PATCH 不自動重試；逾時後重新單次執行會先查 marker，避免盲重送。
若程序被中斷留下 lock，先確定沒有活躍實例，再人工移除空 lock 目錄。
遠端追加成功但本地 receipt 寫入失敗仍 exit 1；下次執行會讀回現有 marker。
SHA-256 用於內容核對；origin_signature 是來源標記，非密碼學簽章。

## 驗證與狀態

```bash
python -m unittest discover -s tests -p test_mrl_github_notion_bridge.py -v
python -m py_compile adapters/mrl_github_notion_bridge.py
```

本地測試只驗證 fixture API、分頁、防重、拒絕權限、失敗讀回及憑證不隨 redirect 外送。
DL580_API_EXECUTION、DL580_DEPLOYMENT、RUNTIME_ROUNDTRIP = UNRUN，不能將 GitHub/Notion connector 成功算作此 runner 的實機成功。
本輪 sandbox 對既有 Bridge /health 回 HTTP 403；Tailscale CLI 不在本環境，100.78.70.78:7800 無可用 route。這不表示 DL580 或既有部署離線。
main 的 Tailscale-only 修改實際位於 3DScanner ProductBridge :3050，不能把該綁定直接套用到母體 :7800。


## 2026-10-21 接續核對與防護增補

固定沿用現行 canonical／母體兩個 page ID；schema、parent_module、parent_source、operation、定義方向不符即停止。
執行時核對 Notion 回傳 page ID、live 狀態，以及權威頁頂層正文的 Mr.liou／MrLiouWord 宣告與母體頁連結。
此為治理內容核對，不是簽章驗證；REST 2022-06-28 不提供本次 Wiki badge 證據，runner 明示 native_wiki_verification=NOT_ASSESSED_BY_RUNNER。
本次另以 Notion connector 讀到兩頁 verified；不將此 badge 當成每次 runner 自動重新驗證。
GitHub number、base.repo.full_name 與兩端 40 位 SHA 必須對上；初始來源仍為 PR #677，不改成接線 PR #679。
原 v1 source payload／marker 保持，舊回執可以直接辨識。PATCH 後核對所有同 marker 項，包含額外的衝突副本。

同一 output-dir 每次新增 MRL_GitHub_Notion_<timestamp>.jsonl：先落盤 START，追加前落盤 APPEND_INTENT（含來源、目標、digest），flush／fsync 失敗則不追加。
每項讀回結果另記錄 phase；失敗記錄 FAIL_RECONCILE_BEFORE_RETRY 與安全的例外類別，不保存 token 或 HTTP body。
JSONL 是調查日誌，只有完整 JSON report 才是成功結果。若磁碟完全不可寫，可能無法保存 FAIL，仍須視為失敗。
逾時、程序終止或回執寫入失敗，先確認鎖及單一寫入者，查看 APPEND_INTENT，再 plan 查遠端 marker；不得只刪鎖後盲目 apply。
鎖只保護共用輸出目錄，不提供跨主機交易／遠端 exactly-once；FlowEditBridge 等其他寫入者須保持單一操作窗口。

本次 Dropbox 原件 metadata：MRL_Edit.py、2826 bytes、rev 6520389e18e3d230ba502、server_modified 2026-05-17T13:36:51Z。
重新讀取的 append_paragraph 仍使用 PATCH /blocks/{page_id}/children 與 paragraph.rich_text.text.content，契約相容；未修改、匯入或替換原模組。
此為文字擷取契約比對，不宣稱原始 bytes 雜湊或 DL580 已安裝版本相符。

本機使用 Python 3.12.14 跑離線測試與語法檢查。真實 CLI plan 已嘗試，缺少 runtime NOTION_TOKEN／環境 GITHUB_TOKEN 而失敗，留下 FAIL 日誌；不是 live plan PASS。
既有 GitHub keyring 登入可用，但未從 connector 抽取憑證。本機 Tailscale 無法載入 preferences，未取得 DL580 授權執行通道。
D:\MrlToolchain\python\python.exe 與 D:\mrl\bridge\logs\MRL_GitHub_Notion 仍為待實機核對路徑。
執行前後沿母體既有 FullCheck 規則，OK→FAIL 立即停止與依原備份復原；此 runner 不自行啟停服務。
LIVE_RUNNER_PLAN、LIVE_APPEND_READBACK、LIVE_REPEAT、LIVE_FAILURE_RECOVERY、DL580_DEPLOYMENT = UNRUN。
離線 plan 與 timeout-after-acceptance 恢復案例通過，不冒充上述真實驗收。
