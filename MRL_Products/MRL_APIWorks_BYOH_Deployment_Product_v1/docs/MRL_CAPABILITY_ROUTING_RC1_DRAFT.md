# MRL-36 Capability-aware routing 契約增量

| 欄位 | 值 |
|---|---|
| 商品 | MRL-APIWORKS-BYOH-DEPLOY-V1 |
| 契約 | `0.1-RC1-DRAFT` |
| 工程快照 | `dofaromg/flow-tasks` · `mrl-37/license-redistribution-gate-v1-20261105` · `ccb13c3cedea9388d06cf9cbacdbb136d6a074ab` |
| origin_signature | MrLiouWord |
| canonical_authority | Mr.liou |
| Owner 審閱 | PENDING |

## 契約與既有呼叫

| 文件 | MRL-45 CLI 契約名稱 | 欄位與判定 |
|---|---|---|
| `routing-decision-input.schema.json` | `routing-decision-input-rc1-draft` | task、workload、能力需求、資料分類與雙層授權、硬體／ABI、model／runtime revision、健康度／延遲／費用預算、控制面的 policy 及候選快照。 |
| `routing-adapter-result.schema.json` | `routing-adapter-result-rc1-draft` | 一次已選目標的結果。欄位固定為 `status`、`output_digest`。 |
| `route-receipt.schema.json` | `route-receipt-rc1-draft` | requested／resolved 識別、decision_model、route_probabilities、route_reason、execution_location、health_fallback、ttft_class、pricing、逐輪淘汰原因與重放證據。 |

三份 Schema 位於 `schemas/rc1-draft/`。MRL-45 原本的 `route-receipt`、`decision-request`、`decision-response` 名稱繼續解析 RC0 原件。新增版本使用獨立的 `$id`，共用欄位透過離線 `$ref` 讀取 RC0 的子結構。RC0 收據要求有執行目標與至少一次嘗試，收據為 `abstained`、`no_route`、`shadow_selected` 時按 RC1 草案保存。RC0 呼叫者繼續使用既有發行格式。

現有 Gateway、既有 Ollama／llama.cpp adapter、MRL-45 Billing Receipt 與其價格格式沿用基線。路由器的單位為同幣別的百萬分之一貨幣單位，欄位 `estimated_cost_micros` 代表估價。下游 MRL-39 使用自己的計量與結算證據。

## 選路與回退

1. 控制面固定 `policy_id`、`policy_version` 和 `decision_model`，提供可信的候選資格快照及請求分類，並以目標 ID 綁定 adapter 和執行位置。請求檔的 `input_digest` 須與即將交付給 stub 的不可變 bytes 一致。
2. 每一輪以當輪時間檢查工作類、能力、model／runtime revision、加速器與 ABI、健康觀測時間、score、TTFT、剩餘延遲與費用。缺少硬體、健康、價格或延遲依據的目標退出當輪。價格窗為 `effective_at <= evaluated_at < expires_at`，費用限制使用同一幣別，預先保留已試目標的估價。
3. 雲端需同時符合請求允許外送、請求核准的目標、控制面目標允許清單及分類允許清單。每輪重新檢查，並在呼叫雲端 stub 前再檢查。測試以帶有 `egress_allowed=false` 的相同本地故障案例證明雲端呼叫數為 0。
4. 先使用所有合格 local 目標，local 清空時才評估合格 cloud 目標。由控制面權重算出整數基點機率，使用最大餘數法分配至合計 10,000。被排除或位於另一個優先層的目標權重為 0。依原始權重排序，同權重以目標 ID 字典順序決定。這些數值表示當輪的相對選路權重，實測成功率另有獨立證據。
5. 最高順位目標低於 `abstain_below_bps` 時回傳 `abstained`，並保存當輪分布。合格集為空時回傳 `no_route`。兩種結果都停止分派，也可發生在上一次本地健康拒絕之後。
6. adapter 收到一份凍結的 `Invocation`，其中包含指定目標、版本、時間預算與 bytes。回傳只能表達此次結果。只有 `health_rejected_before_acceptance` 可以開啟下一輪。回傳未知、已失敗、格式錯誤、例外或無 adapter 時停止。到達嘗試上限以 `execution_failed`／`ATTEMPT_LIMIT_REACHED` 保存。每個已嘗試目標當次最多分派一次。
7. `ttft_class` 由估計 TTFT 套用政策門檻。interactive 和 standard 的上界包含端點，batch 為其餘仍符合預算的值。shadow 評估只讀取描述資料，保留預測目標與價格，各例的 `execution_location`、輸出 digest 為 `null`、`attempts` 為空。shadow 結果可以與正式結果不同，兩者各自保存。

此版本的 adapter 是程序內合成 stub。欄位限制、註冊位置與呼叫記錄可以證明合約等級的控制界線。任意供應商程式的隔離、傳輸層外送限制、回覆提交狀態證明、串流取消、timeout 強制與跨請求冪等由正式接線與獨立驗收提供。Runtime 資產簽章、實機准入及授權證據沿用現有 Gate。

## 重放與證據

收據保存決策需要的請求 metadata、policy、候選清單、逐輪時間及 adapter 結果。重放使用記載時間及結果重算選路，對照每次 dispatch 的目標與位置，拒絕遺漏或多餘決策輪次、外送違規和重算後不匹配的收據。重放不發動推論。收據可能含內部目標和決策政策，保留於原有的受控證據區。

`integrity.input_digest` 是原始 bytes 的 SHA-256。快照與收據 digest 沿用商品既有的正規化 JSON 雜湊（UTF-8、按鍵排序、無額外空白、無非有限數值），收據 digest 僅排除 `integrity.receipt_digest` 本身。hash 可作內容核對，`--expected-digest` 可比對從可信證據取得的 digest。Adapter 成功輸出 digest 在回執中作為記載觀測值。

收據在發行時可帶 `trace_id`、`sequence` 及前筆 digest。相鄰回執核對要求相同 trace、相同 mode、sequence 遞增一及正確的前筆 digest。提供 `--previous` 可核對相鄰連結。完整 journal、簽章、寫入順序及不可變性由外部證據保存機制負責。

## 本地驗證

從商品目錄執行，安裝版本沿用 `requirements.mrl45.lock`。

```sh
python -m pip install --require-hashes -r requirements.mrl45.lock
python scripts/MRL_gate_schema_validator_v1.py check
python scripts/MRL_gate_schema_validator_v1.py validate route-receipt tests/fixtures/mrl45/route-receipt.json
python scripts/MRL_gate_schema_validator_v1.py validate route-receipt-rc1-draft tests/fixtures/mrl36/receipts/health-fallback-egress-denied.json
python scripts/MRL_capability_routing_v1.py tests/fixtures/mrl36/receipts/health-fallback-egress-denied.json
python scripts/MRL_capability_routing_v1.py tests/fixtures/mrl36/receipts/live-ledger-child.json --previous tests/fixtures/mrl36/receipts/live-local.json
python -m unittest discover -s tests -p test_capability_routing.py -v
python -m unittest discover -s tests -p test_gate_schema_validator.py -v
```

測試資料與回執位於 `tests/fixtures/mrl36/`，目標、時間、硬體識別、價格及輸入正文皆為合成。基線、RC0 父版 hash、Schema Git blob 與候選分支見同目錄層級的 [版本譜系](../schemas/MRL_36_routing_contract_provenance_R01.json)。
