# MRL-47 Reference Adapter R01

| 欄位 | 值 |
|---|---|
| 介面 | `MRL_Reference_Adapter_v1` · `0.1-RC1-DRAFT` |
| 商品 | `MRL-APIWORKS-BYOH-DEPLOY-V1` |
| Provenance | `MrLiouWord` · `Mr.liou` · `APPEND_ONLY` |
| Git 父提交 | `ccb13c3cedea9388d06cf9cbacdbb136d6a074ab` |
| 本地依賴 | `MRL_36_R01.patch`，SHA-256 `d765e8251d32dcd514b2728e58f5ea5738b8cc82301584c5c0f5b2efd2b9e5b0` |
| Runtime 父模組 | `MRL_AI_Mother_Autonomous_Runtime_Baseline_v1`，源自 PR #632 |
| Owner 採認 | PENDING |
| DL580／V100 | UNKNOWN |

## 介面與接線

從商品的 `scripts/MRL_reference_adapter_v1.py` 以本地 CLI 呼叫，Python 程式可直接使用
`MRLReferenceAdapter`。兩個入口共用同一份控制面與 Schema。運行時由 MRL-36 先決策，
再透過現有 Runtime 的 `MRLLocalModelAdapter.complete` 呼叫 Ollama 或 llama.cpp。
既有 APIWorks Gateway 的 HTTP 路由沿用原入口。R01 直接呼叫底層 Adapter，
因此運行時僅回傳結果和收據，Memory、Passport 和既有對話的持久化仍由母 Runtime 的入口負責。

| 操作 | R01 行為 |
|---|---|
| `health` | 查詢已配置模型是否已出現在本機清單。Ollama 同時檢查 `/api/show` 的本機 GGUF 資訊。 |
| `capabilities` | 回報同步純文字 chat、介面版本、來源以及本地限定政策。 |
| `models` | 回報已配置且通過當次探測的模型。模型／Runtime revision 取自操作方提供的證據快照。 |
| `decision` | 驗證請求的訊息摘要並做一次本機 metadata 探測。使用 MRL-36 shadow 演算法回傳可離線重放的決策。 |
| `generate` | 在能力、模型版本、硬體、健康度、價格與預算通過 MRL-36 時送出一次本地非串流請求。成功附決策收據、使用量收據與文字。 |

### 來源與權限

操作方在本機提供可信的 `reference-adapter-config`。端點、目標、政策、硬體、價格和
健康分數均由該檔提供。請求包含 `routing_request` 及純文字 `messages`。目標、URL
及供應商參數不屬於請求 Schema。訊息摘要採用 UTF-8、按鍵排序、無額外空白的 canonical JSON，
以 `sha256:` 加上 64 位小寫十六進位數字表示。每次運行建立一份結果，由呼叫者以 request／trace ID
關聯。R01 沒有跨請求去重或正式 journal。

本地探測觀察模型能否被當前服務識別。它不延長控制面健康分數的有效期，也不證明版本、機器或權利已採認。
缺失硬體／價格或過期證據照 MRL-36 規則退出選路。範例 config 內的型號、版本、價格窗和
測試時鐘是合成資料。Ollama 須以主機已停用雲端功能的本地服務運行，主機／容器的外送限制由其
部署邊界執行和採證。僅有 loopback socket 無法判斷該 downstream 服務是否自行轉送。

在 Adapter 的連線層，`localhost` 只嘗試 loopback IP，跳過環境與系統代理，拒絕 HTTP 重新導向。
請求指定外送時直接回應 `EGRESS_DENIED`。Ollama 雲端標記、遠端別名及無法驗證本地來源的模型
都會在消息送出前拒絕。成功後端資料只有字串結果和有值的整數 token 欄位會被採用。
HTTP、I/O 或回應格式錯誤回傳穩定錯誤碼與保守的接受狀態。推論提交不明時，收據使用
`commit_unknown`，當次停止。回執中的缺失 token 保存為 `null` 並標示 `partial` 或
`unknown`。已有整數零照原值保存。MRL-39 Billing Schema 延續原版本。

來源連結

- [PR #632](https://github.com/dofaromg/flow-tasks/pull/632) · [PR #718](https://github.com/dofaromg/flow-tasks/pull/718) · [MRL-47](https://linear.app/dofaromgg/issue/MRL-47)
- [Ollama 本機模式](https://docs.ollama.com/faq#how-do-i-disable-ollamas-cloud-features) · [llama.cpp server](https://github.com/ggml-org/llama.cpp/blob/master/tools/server/README.md)

## 往返重放

本地生成輸出含 `decision_receipt` 及 `usage_receipt`。呼叫者以新增檔案的方式保存收據，
延續既有來源。決策可在沒有後端時用 MRL-36 重放。使用量重放驗證 route／request ID、輸入／輸出
digest、決策 digest、時間與實際存下的 counts。它重算收據結構，後端觀測的 token 計數由後端提供。
決策及使用量收據只保存摘要與 metadata。原文核對時，在本機把原請求另外帶入 replay。

```text
python -B scripts/MRL_reference_adapter_v1.py capabilities --config LOCAL_CONFIG.json
python -B scripts/MRL_reference_adapter_v1.py generate --config LOCAL_CONFIG.json --request LOCAL_REQUEST.json
python -B scripts/MRL_reference_adapter_v1.py replay --decision DECISION.json --request LOCAL_REQUEST.json --usage USAGE.json
```

有獨立取得的雜湊時可帶 `--expected-decision-digest` 與 `--expected-usage-digest`。
`enabled=false` 會關閉本地呼叫。`health`、`models`、`decision`、`generate`
的拒絕以及輸入驗證由 CLI 回傳 exit code 2。

## 尚待後續版本

| 項目 | 目前 |
|---|---|
| stream | OPEN。待逐段輸出與提交狀態回歸。 |
| cancel | OPEN。待後端及傳輸層取消與終止回歸。 |
| timeout | PARTIAL。已驗證同步生成 socket 逾時與不重試。整體 deadline、慢速／串流與取消仍 OPEN。 |
| fallback | OPEN。R01 只配置一個本機目標。MRL-36 的合成 fallback 留做既有回歸。 |
| idempotency／retry budget／circuit breaker | OPEN。R01 保存請求關聯 ID，每次有效呼叫最多分派一次。 |
| remote opt-in／供應商替換與回退驗收 | OPEN。R01 的控制面僅註冊本機目標。 |
| DL580／V100／真實模型 | UNKNOWN。待 MRL-35／44、精確資產、權限、部署拓撲、當前模型回執與實機證據。 |

## R02 穩定性修正

同步 `decision` 與 `generate` 共用請求的 monotonic 時間預算。模型清單、
Ollama metadata 探測與生成使用同一截止點。Loopback socket 在截止時關閉，
因此持續收到少量回應的伺服器也會逾時。直接連線保留 localhost 與 TLS
主機驗證，HTTP 重新導向由 Adapter 拒絕。

接收端核對 Content-Length 和實際讀回大小。只送出有效 JSON 前綴的截斷回應
會產生 `BACKEND_INVALID_RESPONSE`。生成嘗試後逾時或輸出無法核對時，使用量收據
維持空值並保留 `commit_unknown`。Adapter 結束本次連線。後端是否已停止推論仍待
取消或端到端回執判定。

R02 的非串流 transport deadline 已在本機回歸驗證。stream、cancel、跨目標 fallback、
跨請求 idempotency 與 DL580 實機驗收仍列在 R01 缺口表。R01 原始交付與證據保留。

公開工程分支以原始 RC0 檔名、版本、SHA-256 及 Git blob 保留來源鏈。私人檔案定位資訊由 R01 原始審計保存。
