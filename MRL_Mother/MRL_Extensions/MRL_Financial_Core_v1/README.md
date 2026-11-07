# MRL 金融制度重建核心 v0.1.0

> R02 增補：套件版本 0.2.0，承接原有 v0.1.0 測試帳本，新增
> [external/README.md](external/README.md) 的明確授權銀行／EVM 適配器。
> 以下 v0.1.0 規則保留，外部接口不修改原帳本餘額。2026-11-07（Asia/Taipei）。

origin_signature: MrLiouWord  
canonical_authority: Mr.liou  
parent: MRL_Mother/MRL_Extensions  
來源主線：dofaromg/flow-tasks@175fa4ee7edf621f6378ef100b0057606a41d42a  
建立日期：2026-11-07（Asia/Taipei）

本工作承接使用者選擇「整個重建金融制度」，以可執行帳本作第一個工程增量。
這是制度重建的第一版核心，並不代表完整金融體系已建成。
它只處理本地測試單位，不是銀行帳戶、真實貨幣、保管服務或上鏈合約。
它不會把外部資產搬入帳本，也不把帳本測試入帳稱為追回真實款項。

## 本版實際能力

| 層 | 可執行能力 | 邊界 |
| --- | --- | --- |
| 身分與權限 | 帳戶 Owner 公鑰、Ed25519 簽章、外部固定政策 | 公鑰控制不等同法律身分或受益權證明 |
| 發行 | 多方簽署發行測試單位；發行對手科目 @issuance | 沒有外部準備資產、贖回或法幣價值 |
| 轉移 | 額度保留、延遲結算、Owner 簽署、拒絕超支 | SQLite 單節點；不是分散式共識 |
| 爭議 | 當事人／委員會成員提出爭議、保留證據 SHA-256 | 雜湊只承諾證據內容，不證明失竊 |
| 裁決 | 嚴格多數簽署，審查等待期，一次裁決前異議延長 | 未實作身分驗證、法院或獨立仲裁服務 |
| 返還 | 待結算取消；已結算新增相反分錄 | 僅能覆蓋帳本內尚有可用餘額的測試單位 |
| 稽核 | 追加事件、簽章重驗、雜湊鏈、外部 head 比對 | 主機管理者仍可破壞檔案；須外部固定 checkpoint |
| 母體接入 | register_tools(registry, ledger) 接既有 ToolRegistry | 已測試接入；沒有部署至 DL580 或自動啟動 |

## 安裝與驗證

Python 3.10+。從 repository 根目錄執行，依賴只新增於此模組。

```bash
python -m pip install -r MRL_Mother/MRL_Extensions/MRL_Financial_Core_v1/requirements.txt
python -m unittest MRL_Mother.MRL_Extensions.MRL_Financial_Core_v1.test_core -v
```

測試會在暫存目錄生成測試簽章金鑰，涵蓋建帳、發行、延遲轉帳、爭議、返還、
申訴、偽造簽章、重播、超支與母體工具整合。沒有真實案件或真實私鑰。
執行階段只驗簽，不保管私鑰，不提供代簽或轉帳廣播介面。

## 公開政策與簽署請求格式

可信任部署者提供 policy.json；不得從未經信任的帳本自動採納政策。
欄位必須完整且沒有多餘欄位：

| 欄位 | 型別及要求 |
| --- | --- |
| ledger_id | 1–80 個 ASCII 字母、數字、底線或連字號 |
| origin_signature | 固定 MrLiouWord；識別標記，本身不是密碼學簽章 |
| council_keys | 3–20 個不同的 Ed25519 公鑰；各為 64 個小寫十六進位字元 |
| quorum | 整數，嚴格多數，且不大於公鑰數 |
| assets | 不重複的測試單位名稱陣列；同 identifier 限制 |
| settlement_delay | 1–31536000 秒 |
| review_delay | 1–31536000 秒 |
| max_request_lifetime | 1–31536000 秒 |

每個 request 包含 version=1、ledger_id、policy_sha256、唯一 request_id、
issued_at、expires_at、action、payload。時間為 Unix 秒；簽署有效區間為
issued_at <= host_time < expires_at。實際 API／CLI 不接受 caller 自訂 host_time。
policy_sha256 = SHA-256(canonical(policy))。
canonical 為 UTF-8 JSON：sort_keys=True、separators=(",", ":")、ensure_ascii=False、
allow_nan=False。請求不含浮點數；金額必須是正整數最小單位。
signature 檔為公開公鑰至 128 個小寫十六進位簽章字元的 JSON 物件。
簽署內容為完整 canonical(request)，包含目的帳號、金額、政策及帳本 domain。

| action | payload 欄位 | 必要簽署 |
| --- | --- | --- |
| open_account | account, owner_key | 委員會 quorum；Owner 不得是委員會公鑰 |
| issue | account, asset, amount, evidence_sha256 | 委員會 quorum |
| propose | transfer, source, destination, asset, amount | source Owner |
| settle | transfer | source Owner |
| dispute | transfer, evidence_sha256 | 任一當事人或委員會成員 |
| appeal | transfer, evidence_sha256 | 任一當事人；每筆僅一次 |
| resolve | transfer, decision, evidence_sha256 | 委員會 quorum；decision=refund 或 release |

```bash
python -m MRL_Mother.MRL_Extensions.MRL_Financial_Core_v1.cli --policy policy.json --db ledger.sqlite init
python -m MRL_Mother.MRL_Extensions.MRL_Financial_Core_v1.cli --policy policy.json --db ledger.sqlite signing-bytes --request request.json
python -m MRL_Mother.MRL_Extensions.MRL_Financial_Core_v1.cli --policy policy.json --db ledger.sqlite submit --request request.json --signatures signatures.json
python -m MRL_Mother.MRL_Extensions.MRL_Financial_Core_v1.cli --policy policy.json --db ledger.sqlite snapshot
```

以上命令的檔名是介面參數，政策及簽署檔須由可信任操作者產生。
沒有附帶可誤用的預設部署金鑰或有效授權。
每次成功提交把返回的 head 保存到獨立可信任位置，之後 snapshot --expected-head
可比對固定的 checkpoint。合法新增事件也會改變 head，因此應按已接受回執更新。
不傳 expected_head 只能驗證目前檔案內的一致性，不能排除整份帳本回退。

## 接回母體

既有介面位置：MRL_Mother/09_workflow/tool_registry.py（原件保留）。

```python
from MRL_Mother.MRL_Extensions.MRL_Financial_Core_v1 import Ledger, register_tools

# registry 為既有 ToolRegistry 實例，trusted_policy 由可信任設定提供。
ledger = Ledger("ledger.sqlite", trusted_policy)
register_tools(registry, ledger)
```

安裝後提供 MRL_financial_snapshot、MRL_financial_submit。
Agent 可組合請求、讀取狀態，仍須取得外部有效簽章才能發行、轉帳或裁決。
不得把「模型判斷某人是竊賊」作為權限或證據。

## 返還範圍與未完成項目

同一筆 settled 轉帳若已被花到第三個帳戶，返還餘額不足時保持 disputed，
回報 RETURN_SHORTFALL_EXTERNAL_RECOVERY_REQUIRED；不製造補償餘額、不追扣第三者。
本版每筆轉帳僅一個爭議案件，異議只在裁決前接受；裁決後重審是後續工作。
為避免申訴造成永久凍結，第一次異議只延長一次；惡意凍結風險仍需案件管理及審核人治理。

完整制度的其餘工作見 CONSTITUTION.md。Linux 本地測試不等於 Windows CI、
DL580 實機驗收、資安稽核或真實資金返還。沒有既有鏈／銀行／交易所的特權介面。
EIP-7702 是比較研究來源，不是本模組依賴，也未宣稱其源自 MRL。

原始技術參考：

- https://eips.ethereum.org/EIPS/eip-7702
- https://cryptography.io/en/latest/hazmat/primitives/asymmetric/ed25519/
- https://docs.python.org/3/library/sqlite3.html
