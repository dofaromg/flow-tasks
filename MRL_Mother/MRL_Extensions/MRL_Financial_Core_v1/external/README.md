# MRL 授權銀行／鏈上錢包連接模組 R02

module_id: MRL_Financial_External_Access_v1  
origin_signature: MrLiouWord  
canonical_authority: Mr.liou  
parent: MRL_Mother/MRL_Extensions/MRL_Financial_Core_v1  
承接版本：dofaromg/flow-tasks@d7e0e8137c833fef123f6681ca19f827bc99a0e8（PR #713）  
日期：2026-11-07（Asia/Taipei）

這是可以安裝及呼叫的外部適配器，不是銀行特權、任意錢包控制或追回完成證明。
只透過正式 API／實際來源錢包簽章操作已授權帳戶。原本 core.py 的測試單位帳本
保持獨立，外部入帳、付款申請或廣播回執不自動變成測試帳本的發行或返還。

## 已實作範圍

| 適配器 | 可執行介面 | 此版邊界 |
| --- | --- | --- |
| Mercury | GET 帳戶、GET 單筆交易、POST 需銀行端核准的 ACH 付款申請 | 有效 Token 與指定帳戶／既有收款人；未實作核准／直接送款 API |
| EVM | ETH 餘額、交易與 receipt 查詢；外部簽署的 EIP-1559 原生幣轉帳廣播 | Ethereum chain 1／Sepolia 11155111；來源與收款端均須無合約程式碼 |
| 操作授權 | 原根登錄中的明確操作記錄，加上既有 ledger policy 的多數 Ed25519 簽核 | 不把 repo 存取、Agent 能力或竊案指控當作授權 |
| 提交日誌 | 唯一請求／nonce 預留、UNKNOWN 防重送、追加雜湊歷史及回執讀回 | 本地 SQLite；主機擁有人仍可破壞檔案，應在獨立位置保留 checkpoint |
| 母體回填 | 4 個外部工具註冊；module_registry 的 additive_children 承接父子關係 | 程式與登錄已回填 GitHub；不是 DL580 上線回執 |

Mercury 是首個銀行服務接頭，不代表使用者的帳戶已開通，也不是所有銀行共用的 API。
Bitcoin、Solana、其他銀行、ERC-20、合約呼叫、approve、EIP-7702 委派與強制扣款均未實作。
未附帶真實帳戶 ID、銀行 Token、私鑰、助記詞或有效金融操作授權。

## 安裝與測試

從 repository 根目錄：

```bash
python -m pip install -r MRL_Mother/MRL_Extensions/MRL_Financial_Core_v1/external/requirements.txt
python -m unittest MRL_Mother.MRL_Extensions.MRL_Financial_Core_v1.test_core MRL_Mother.MRL_Extensions.MRL_Financial_Core_v1.external.test_external -v
```

測試使用暫存目錄、臨時金鑰及明確標記的 provider fixtures，完全不碰真實帳戶。
來源錢包核驗測試使用真實 secp256k1 簽名／恢復，但不送出任何交易。
原 repo 未安裝選配 eth-account 時，通用測試探索會跳過需要該依賴的測試；
本模組專項 CI 會安裝 external/requirements.txt，再執行全部 40 項測試。
cryptography 與 eth-account 的授權及來源保留原樣；正式部署前仍須依既有 Runtime Artifact Trust Gate 驗收。

## 預設狀態與啟用條件

settings 由 default_settings(ledger_policy) 產生：writes_enabled=false、allow_live=false，
銀行帳戶、錢包、收款人清單均空，RPC URL 空。init-settings 只建立這份停用設定。
ledger-policy 是前版可信任政策檔，內含公開 council_keys；不是私鑰。

每次操作都必須依次滿足：

1. 設定中的來源、收款人、環境、資產與單筆額度匹配。
2. 同一個 config/MRL_AUTHORIZATION_REGISTRY_v1.json 內的 financial_external_grants
   有唯一、有效、未撤銷的明確範圍記錄。此欄位在本次既有根登錄中不存在，等同空清單。
3. 寫入時須開啟 writes_enabled，並取得既有 ledger policy 嚴格多數公鑰對完整請求的簽章。
4. 寫入請求綁定 ledger ID、ledger policy SHA-256、connector policy SHA-256、
   根登錄 SHA-256、唯一 request_id、有效期、來源、收款人及金額；最長有效期 300 秒。
5. 真實環境額外要求設定 allow_live=true 及操作者執行時 --enable-live，兩者缺一拒絕。
6. 銀行須有相符環境、權限及銀行端允許的 Token；錢包須由真正的來源私鑰在外部簽署交易。

尚未提供任何實際帳戶與逐筆操作授權，因此本次保留正式帳戶未啟用狀態。
建立連接器不會替任何帳戶產生授權，亦沒有變更既有 structure-index 的 active_grants。
根登錄及 policy 檔屬於可信任部署設定，必須由 Owner 控制存取；公鑰清單不同不證明現實中是不同人。

## 根登錄的增補介面

在同一個根登錄內，未來按 Owner 的具體帳戶授權追加 financial_external_grants 陣列。
沒有建立平行的權威登錄。舊 active_grants 保留給原來的結構索引 consumer。
正式記錄須由已核對的授權資料產生，不能直接把測試 fixture 搬入正式環境。

| 欄位 | 規則 |
| --- | --- |
| record_id | 唯一識別；1–80 個 ASCII 字母、數字、底線或連字號 |
| issued_by | MrLiouWord；根登錄檔由可信任操作者控制 |
| actor | 實際本地主機帳號 local:USERNAME，精確比對 getpass.getuser() |
| issued_at / expires_at | 具時區 ISO 8601，現在必須落於有效區間 |
| status | 只有 active 生效，revoked 不生效 |
| action | 下表列出的精確動作 |
| resource / destination | 下表格式，沒有 wildcard 或全域預設權限 |
| environment | mercury-sandbox、mercury-live、evm-sepolia 或 evm-mainnet |
| evidence_reference | 非空的原始帳戶控制及 Owner 授權證據位置；字串本身不驗證權利真假 |

| action | resource | destination |
| --- | --- | --- |
| financial.mercury.read | mercury:ACCOUNT_UUID | local-operator |
| financial.mercury.request_ach | mercury:ACCOUNT_UUID | mercury-recipient:RECIPIENT_UUID |
| financial.evm.read | evm:CHAIN_ID:LOWERCASE_ADDRESS | local-operator |
| financial.evm.send_native | evm:CHAIN_ID:LOWERCASE_SOURCE | evm:CHAIN_ID:LOWERCASE_RECIPIENT |

以上大寫名稱是欄位說明，不是已交付帳號或現成授權。根登錄每次操作都重讀，
簽核後更動根登錄會使舊簽核失效。變更根登錄的正式權限時，還必須接續既有治理校驗與 Owner 審核。
本次未替未指定帳戶簽發該記錄，也未把現有結構索引授權擴充為金融權限。

## CLI 與母體工具

```bash
python -m MRL_Mother.MRL_Extensions.MRL_Financial_Core_v1.external.cli --help
```

共同參數：--ledger-policy、--settings、--root-registry、--journal。
init-settings 建立停用設定；init-journal 排他建立外部 outbox；observe 讀取 query JSON；
plan 讀取 operation JSON 並產生待簽請求；submit 讀取 request／signatures JSON，
EVM 另外讀取 --signed-raw-file（內容為已簽交易 hex 的 JSON 字串）；status 讀回 request_id。
私鑰不進此 CLI。MRL_MERCURY_API_TOKEN 只由環境或安全祕密管理載入，不得寫進 repo 或聊天。

```python
from MRL_Mother.MRL_Extensions.MRL_Financial_Core_v1.external.gateway import Gateway, register_external_tools

# 以下物件來自既有、受保護的本地主機設定；沒有自動產生金融授權。
gateway = Gateway(trusted_ledger_policy, disabled_or_approved_settings,
                  root_registry_path, local_external_journal_path)
register_external_tools(existing_tool_registry, gateway)
```

註冊 MRL_financial_external_plan、MRL_financial_external_observe、
MRL_financial_external_submit、MRL_financial_external_status，保留原工具且拒絕覆蓋同名工具。
ToolRegistry 會記錄呼叫輸入，因此簽署請求與 raw transaction 的操作日誌須留在受保護主機。
已簽的鏈上交易可由其他人轉送；MRL 的簽核限制適用於本模組的提交路徑，
不會把普通錢包變成鏈上多簽，也不能撤回已洩漏的有效 raw transaction。
Token 不接受為工具參數，provider 錯誤內容也不寫入回執或 traceback。

## 操作 JSON 契約

| 類型 | 必要欄位 |
| --- | --- |
| mercury.account query | kind=mercury.account、account |
| mercury.transaction query | kind=mercury.transaction、account、transaction |
| evm.wallet query | kind=evm.wallet、wallet；可另帶 tx_hash |
| Mercury operation | kind=mercury.request_ach、environment、account、recipient、amount_cents |
| EVM operation | kind=evm.native_transfer、environment、source、transaction |

EVM transaction 必須且只能包含 type=2、chainId、nonce、to、value、gas=21000、
maxFeePerGas、maxPriorityFeePerGas、data="0x"、accessList=[]。數值全部是整數最小單位，
to 由 plan 使用小寫地址。source／to 必須在 allowlist 且目前沒有程式碼。
會核對節點 chain ID、pending nonce、來源可用額度，以及 raw transaction 恢復出的簽署來源。
Token allowance／任意 calldata／7702 授權不能混入此原生幣介面。

銀行 amount_cents 以固定小數 JSON number 送出，沒有浮點金額計算；僅 ACH。
Token／銀行組織政策仍可能拒絕請求。Mercury 的核准由銀行平台執行，本模組沒有批准權。

## 回執、逾時與追回的區別

| 狀態 | 能證明什麼 | 不能宣稱什麼 |
| --- | --- | --- |
| BANK_REQUEST_RECORDED | API 回傳相符的付款申請及 provider status | 款項已結算／失竊資產已追回 |
| TX_BROADCAST | 節點回傳與已簽交易相同的交易 hash | 上鏈成功、終局確認或原帳戶返還完成 |
| TX_RECEIPT_OBSERVED | RPC 提供相符來源及交易 hash 的 receipt | 節點可信或已達鏈上終局性 |
| SUBMISSION_UNKNOWN | 外部回應、寫回或傳輸未能明確完成 | 可以安全換 ID 重送 |

outbox 在外部寫入前先提交 UNKNOWN 與唯一請求／nonce，遇到逾時或崩潰不自動重送。
UNKNOWN 必須沿原銀行申請或交易 hash 核對；不得換新 request_id 規避 outbox。
銀行冪等鍵由 ledger ID 及 request_id 雜湊產生。EVM 同一 chain/source/nonce 只保留一次。
日誌儲存 request SHA-256、intent、回執與追加雜湊歷史，不保存銀行 Token 或已簽 raw transaction。
保留原請求及外部簽核檔於受保護主機供稽核；journal_head 應另存獨立 checkpoint。
日誌防重送不替代外部對帳，不提供跨主機或已刪除日誌後的 exactly-once 保證。

這些介面能在取得適當授權後發起新的返還付款。已離開控制範圍的資產仍須正式追回管道，
不能用此模組控制被指控者的帳戶。鏈上終局性驗證、正式帳戶連線、DL580 實機、
法幣清算對帳與真實返還驗收均保留為未驗證，沒有用模擬測試冒充實測。

原始技術來源與查核日期見 sources.json。
