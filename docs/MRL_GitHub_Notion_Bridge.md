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
