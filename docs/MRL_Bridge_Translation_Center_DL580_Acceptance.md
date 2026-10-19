# MRL橋接轉譯中心：DL580 部署與分層驗收

origin_signature: MrLiouWord
canonical_authority: Mr.liou

本修補接續 PR #671–#674 與既有 `MRL_Bridge`，不建立平行 Runtime、服務、埠或遠端控制通道。
來源基線：`cc5b00595cab803867ec9ed374902cae04aefcad`；#674 合併來源：`01cb5bad5fdb3142547a164aac93ce83628b27ee`。

## 已補的接線

1. `scripts/MRL_deploy_accept_bridge_translation_center.ps1` 是原安裝器的薄接線。
   在停止任何服務前，先核對實際監聽 PID、Node 執行檔、Bridge server.js 路徑與 Windows 服務祖先程序。
   它呼叫原 `MRL_install_bridge_translation_center.ps1`，仍使用原五檔備份與還原機制。
2. `scripts/MRL_accept_bridge_translation_center.py` 只在真正的 Windows DL580 執行驗收，所有輸入、輸出與帳本路徑限定 D:。
   它核對五個已裝檔案、即時 HTTP、帳本 hash chain、request/response bytes、錯誤回應及程式碼封包來源。
3. Python 原 `TranslationCenter` 的新事件額外記錄 `runtime_evidence`：PID、執行檔、模組路徑、載入時刻與載入時的 LF SHA-256。
   舊帳本不改寫，舊事件仍可重放。這是本地主機證據，不是密碼學身分認證。
4. Python 驗收只採用指定既有服務的活程序，要求程序建立與模組載入均在本次部署開始後，且模組指紋與已裝來源一致。
   另需真的有 connector 往返回執與一條完整 Mobius route/collapse/lift 回鏈。
   新開 unittest、CLI 或測試程序不能取代該服務的活動。

## 原主機先決條件

- 主機 `WIN-PBVUI7VK2A6`，管理員 Windows PowerShell 5.1，原有 `MRL_Bridge` 正在運行。
- 使用已查得的既有 Runtime 根目錄、Bridge 目錄、Node >=24 與 Python 路徑。接線不修改全域 PATH。
- SourceRoot 是 D: 上已取得本修補 commit 的乾淨 Git checkout；不自動 git pull、reset 或 checkout 既有 Runtime。
- 現有服務啟動設定已將 Python 的 `PYTHONPATH` 指向 RuntimeRoot，並將 `MRL_TRANSLATION_LEDGER_DIR` 指向 D: 持久化證據目錄。
  驗收接線不猜測、不覆寫服務的啟動設定、環境或憑證。
- 呼叫驗收器的授權程序須繼承既有 `MRL_BRIDGE_API_KEY`。不把金鑰放入命令列、query、文件、stdout 或 Git。
- NodeLedgerDirectory 必須是實際服務的 `MRL_TRANSLATION_LEDGER_DIR`，或原本 `MRL_BRIDGE_LOG_DIR`，預設 `D:\mrl\bridge\logs`。
- 原安裝器的來源／已裝版本雜湊不符就停止，不能移除 gate 強行覆蓋。

先以既有管理通道讀取本機設定，不輸出服務 CommandLine 或環境中的憑證：

```powershell
Get-CimInstance Win32_Service |
    Where-Object Name -like 'MRL*' |
    Select-Object Name,State,ProcessId
Get-CimInstance Win32_Process |
    Where-Object Name -match '^(node|python|pythonw)\.exe$' |
    Select-Object ProcessId,ParentProcessId,ExecutablePath,CreationDate
Get-NetTCPConnection -State Listen |
    Where-Object LocalPort -in 7800,7500 |
    Select-Object LocalAddress,LocalPort,OwningProcess
```

## 執行介面

### Windows 來源取件：保留歷史的 sparse checkout

首次 Windows CI 已確認既有歷史路徑 `:mnt:data.txt` 無法在 Windows checkout。
不得改名或刪除該歷史檔案。驗收 CI 以 non-cone sparse checkout 精確取出本來源清單與 `MRL_utils.py`，並固定測試 PR head SHA。
原主機同樣只需來源材料，不需要 checkout 全倉庫；以下只在專用的 SourceRoot 來源目錄執行，不能套用到運行中的 RuntimeRoot：

```powershell
# SourceRoot 必須是 D: 上尚不存在的來源材料目錄，非服務根目錄。
if (Test-Path -LiteralPath $SourceRoot) { throw '不得覆寫既有來源或 Runtime' }
git clone --no-checkout https://github.com/dofaromg/flow-tasks.git $SourceRoot
if ($LASTEXITCODE -ne 0) { throw '來源鏡像取得失敗' }
git -C $SourceRoot sparse-checkout init --no-cone
git -C $SourceRoot sparse-checkout set --no-cone MRL_Bridge/ connectors/ MRL_Mother/09_workflow/ scripts/ docs/ .github/workflows/ Dockerfile.mrl
if ($LASTEXITCODE -ne 0) { throw '來源範圍設定失敗' }
git -C $SourceRoot checkout --detach $SourceCommit
if ($LASTEXITCODE -ne 0) { throw '固定版本來源取件失敗' }
```

`SourceCommit` 是本 PR 經核對的完整 head SHA。這是部署材料 checkout，沒有啟動第二套服務。
若該廣度的目錄內另有 Windows 不支援的歷史路徑，應沿 audit 的逐檔清單縮小**來源取件**範圍，不能修改原始命名。

### 呼叫既有部署器與分層驗收

以下參數來自原主機的既有設定，不預設任一 Python 服務或部署路徑已經驗證。
在已取得修補的 SourceRoot 根目錄，使用既有設定變數執行：

```powershell
& .\scripts\MRL_deploy_accept_bridge_translation_center.ps1 `
    -RuntimeRoot $RuntimeRoot -SourceRoot (Get-Location).Path `
    -BridgeDirectory $BridgeDirectory -NodePath $NodePath `
    -BridgePort $BridgePort -NodeLedgerDirectory $NodeLedgerDirectory `
    -PythonPath $PythonPath -PythonLedgerDirectory $PythonLedgerDirectory `
    -PythonServiceName $PythonServiceName -Install -ReloadPython
```

`-ReloadPython` 只會重新啟動明確指定、已在運行且程序使用指定 Python 執行檔的原 Windows 服務。
未提供 PythonServiceName 時仍可安裝與驗收 Node，但 Python gate 必定不通過。
Task Scheduler／自訂 supervisor 管理的 Python Runtime 目前沒有自動重載 adapter；不得冒認為 Windows 服務或另啟平行程序。

首次部署尚無實際服務事件時會如實回傳 DELIVERY_FAIL，保留 `deployment_session_<uuid>.json`。
沿原服務業務入口產生正常 connector 操作與 Mobius 往返後，用同一 session 再次觀測，避免用新開始時間排除已取得的真實事件：

```powershell
& .\scripts\MRL_deploy_accept_bridge_translation_center.ps1 `
    -RuntimeRoot $RuntimeRoot -SourceRoot (Get-Location).Path `
    -BridgeDirectory $BridgeDirectory -NodePath $NodePath `
    -BridgePort $BridgePort -NodeLedgerDirectory $NodeLedgerDirectory `
    -PythonPath $PythonPath -PythonLedgerDirectory $PythonLedgerDirectory `
    -PythonServiceName $PythonServiceName -DeploymentSession $DeploymentSession
```

第二次不加 `-Install` 或 `-ReloadPython`，不重複部署、不另開測試 Runtime。
所有 session、inventory、acceptance JSON 以唯一檔名留在
`D:\MRL_Mother\EvidenceChain\MRL_Bridge_Translation_Center`；原五檔備份仍在原 BridgeDirectory。
暫存目錄也限定 D:。原始 payload 與憑證不進入驗收回執。

## 分開判定

| Gate | 必須有的證據 |
|---|---|
| Node Bridge | 五檔來源一致；重啟後既有服務的 listener；即時 `/version`；未認證 401；認證 status 200 且 durable；tag 200 且原文與外部來源不變；錯誤 tag 400；各 trace request/response hash 與 parent chain |
| Python Runtime | 指定原服務活 PID；部署後程序建立與模組載入；新模組 hash；D: connector 與 Mobius 帳本；完整 connector 結果及 Mobius 四事件往返 |
| DELIVERY_PASS | 兩個 gate 同時通過 |

安裝器自身的 `MRL_BRIDGE_TRANSLATION_DEPLOYMENT_PASS` 仍只表示既有 Node localhost gate；不能取代上表。
localhost 通過也不證明 iOS、Tailscale、Cloudflare 或每個未接入 adapter 的流量皆已驗收。
本驗收不主動向外部服務製造故障；實際 connector transport_error 可被核對，但沒有觀測的失敗路徑不能宣稱已演練。

## 可逆邊界與限制

原安裝器在安裝或 localhost gate 失敗時按原流程還原五檔。
若原安裝器已成功、後續 Python 重載或完整驗收失敗，接線保留原備份與失敗證據，不自動回滾到可能仍被載入的 Python 舊版。
必須沿既有服務管理方式處理重載或還原；不殺未知程序，不改排程，不刪帳本。
hash chain 是內容一致性證據，不能取代主機權限、來源權威驗證或 owner 的部署裁定。

## 修改交付稽核

本修補預期 7 檔：原 Python center、原 source audit，以及新增接線 PowerShell、驗收 Python、驗收回歸測試、此文件、驗收 CI。
原 audit 維持原清單並追加新檔，保留 #674 的可升級 hash，不改名、不刪除歷史。
GitHub hosted Windows CI 只執行 fixture regressions 與 PowerShell 5.1 parser，不取得 DL580 憑證、不下載本機回執，也不能輸出實機部署成功。
