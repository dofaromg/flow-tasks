# MRL GitHub 任務接線 v1

origin_signature: MrLiouWord  
canonical_authority: Mr.liou  
parent: 既有 ConnectorManager → GitHubConnector → MRL橋接轉譯中心  
source_repository: dofaromg/flow-tasks  
parent_commit: 175fa4ee7edf621f6378ef100b0057606a41d42a

## 接續範圍

2026-11-08 Mr.liou 指示先銜接 GitHub。既有 GitHubConnector 的
sync_data 原先只檢查連線便回報 success / items_synced: 0。
本次在原模組補上「主控提交任務 → 指定 GitHub 來源 → 取得原資料 →
任務結果與回執回到主控」，沿用共用 HTTP 邊界與轉譯中心。

既有八項服務的全域 config/connectors.yaml 保持原設定。
MRL_GitHub_Task_v1.json 是明確指定的 GitHub 單一執行配置，其他服務保持停用。
沒有另開常駐服務、網路埠或平行母體。

## 主控呼叫

在現有 checkout 的 Python 環境使用既有 requests、PyYAML：

    from connectors.connector_manager import ConnectorManager
    manager = ConnectorManager("connectors/MRL_GitHub_Task_v1.json")
    result = manager.execute_task("github", {
        "task_id": "MRL_GitHub_PR700",
        "operation": "get_pull_request",
        "repository": "dofaromg/flow-tasks",
        "number": 700,
    })

result 含 task_id、success、status、data、source_url、observed_at 與
mrl_bridge。執行者用 task_id 對應原任務，將結果交回原主控。
HTTP 原始回應與任務結果各自保留轉譯中心雜湊，沿同一 trace 串接。
原始 GitHub 名稱、branch、完整 SHA、state、merged 與原日期留在 data。

| operation | 必要參數 | 結果 |
| --- | --- | --- |
| get_repository | repository | 原始 repository metadata |
| get_pull_request | repository、number | 原始 PR metadata，含 head/base 與合併狀態 |
| get_file | repository、path、40 位 ref | 原始 bytes 的 base64、size、Git blob SHA、SHA-256 |

repositories 是主機設定的來源清單，任務不能自行擴大。
get_file 固定 exact commit，不使用會移動的 branch 作讀檔基準。
檔案保留原 bytes，範圍為 1 MiB 以下的一般檔案。
任務讀取不接受 redirect，不把憑證交給跳轉目的地。

## 本地入口與回傳

執行範例配置中的 8 PR：

    python -m connectors.github_task_runner --config connectors/MRL_GitHub_Task_v1.json --output-dir MRL_receipts/GitHub

指定單項任務：

    python -m connectors.github_task_runner --config connectors/MRL_GitHub_Task_v1.json --task-json task.json --output-dir MRL_receipts/GitHub

公開來源可使用配置中明列的 allow_public_read:true。
私人來源沿用既有主機 GITHUB_TOKEN 環境綁定；不從 ChatGPT 連接器抽取憑證。
輸出檔名包含 UTC 時間與 UUID，排他建立，保留前次結果。
stdout 回傳結果位置與 success；全部指定任務完成才 exit 0。
部分失敗時保留成功與失敗的個別回傳，整批 exit 1。

既有主控／本機調度器可呼叫 execute_task 或上述入口。
本次不變更排程或安裝 DL580 服務。任務結果封包與總控台 raw schema 分開，
不將任務完成自動當成 Gate、商品或實機驗收。

## 已有對話資料路徑

同輪已使用原生 GitHub 連接器取得 PR #329、#700、#701、#705、#706、#707、
#708、#712 的 metadata，追加回原有 MRL 工程驗收總控台。
4 Linear 與各工作流程、審查端點保留原日期。
這次追加觀察 digest：
50f17c2affb4108715b236a2f3d1f1916cecb3e0985971b7856bf148c6cba5b5

## 交付與依賴

本次接線完成後，Python 3.12.14 的相關測試為 74 passed。
另以本入口實際執行公開來源的 8 PR 讀取，items_synced: 8、success: true；
本地回傳檔為 MRL_GitHub_Task_20261108T154929101397Z_bf746eb8412449c8a7fa3406492650aa.json。
這是本地 GitHub 任務讀取與回傳紀錄，DL580 安裝／執行仍由原部署流程接續。

Expected_File_List（8 個實際工程檔）：

1. connectors/base_connector.py
2. connectors/github_connector.py
3. connectors/connector_manager.py
4. connectors/github_task_runner.py
5. connectors/MRL_GitHub_Task_v1.json
6. connectors/test_connectors.py
7. connectors/test_github_tasks.py
8. connectors/MRL_GitHub_Task_Wiring_v1.md

依賴：既有 MRL_Bridge/translation_center.py → BaseConnector →
GitHubConnector → ConnectorManager → github_task_runner → 本地任務回執。
配置提供 repository 與 task 清單；測試涵蓋真實共用傳輸呼叫路徑、來源身分、
錯誤回傳、原 bytes 與回執串接。SHA-256／size 清冊隨 PR 交付描述保存。

變更可由還原本次提交撤回；已產生的本地回執保持原件。
