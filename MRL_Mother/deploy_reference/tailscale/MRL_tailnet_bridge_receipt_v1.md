# MRL Tailscale / Bridge receipt v1

origin_signature: `MrLiouWord`  
canonical_authority: `Mr.liou`  
parent: `MRL_Mother/deploy_reference/tailscale`  
source: `config/MRL_Tailscale_Reference.json` (historical reference, **not** current runtime state)

## Existing architecture, not a parallel deployment

- DL580 Windows Server host `WIN-PBVUI7VK2A6`, Tailscale private mesh.
- MRL_Bridge `:7800`, MRL_RuntimeOS `:8790`, and MRL_3DScanner_ProductBridge `:3050` remain **separate** endpoints.
- MRL_Tunnel (Cloudflare) and Tailscale are external connectivity adapters; neither is the MRL mother runtime.
- Continue historical `MRL_AI_SYSTEM/deploy/dl580/MRL_Network_Receipt.ps1`. This script captures a **narrow, additive** Tailscale/Bridge receipt, not a replacement.
- No reconfiguration, service start/stop/restart, remote command, authentication or secret export.

## Execute on DL580 (read-only)

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\MRL_Mother\deploy_reference\tailscale\MRL_tailnet_bridge_receipt_v1.ps1 -ProbeLoopback -OutDir D:\mrl\artifacts\network_receipts
```

The script writes one JSON and prints its SHA-256. It inspects Tailscale backend and own tailnet addresses, service status and listening binds. `-ProbeLoopback` additionally performs TCP + GET /health at 127.0.0.1 for `:7800`, `:8790`, `:3050`. Non-200 is FAIL for that endpoint, not proof the whole DL580 is offline. A service bound to tailnet IP alone may be reachable remotely despite a loopback failure.

It intentionally does not record peer identities, all tailnet addresses, machine command lines, request/response bodies, credentials or private files. The receipt contains local hostname and self tailnet IP: keep JSON **on the DL580**, not in a public repository or public issue. Post only receipt path, SHA-256, PASS/FAIL/UNKNOWN and redacted findings in Linear.

## Completion gates

1. **Repository construction**: code committed + exact commit/CI reviewed.
2. **Local receipt**: DL580 script actually executed; JSON non-empty; SHA-256 recalculated.
3. **Cross-device**: iPhone/Mac independently reach authorized endpoints over tailnet, with contemporaneous evidence.
4. **Bridge roundtrip**: separate authenticated app-level request/response evidence; NOT equivalent to Tailscale connectivity.
5. **Deployment**: requires root owner approval; no GitHub green CI can substitute for DL580 live proof.

Until all applicable gates are observed, `remote_roundtrip=UNRUN` and `DL580_DEPLOYMENT=UNRUN`. Preserve source names/versions and original receipts; APPEND_ONLY.

## MRL-44 跨裝置驗收

沿用本目錄的 Windows 採集器，另以 `MRL_tailnet_cross_device_receipt_v1.py`
在 DL580 與 Mac 採集互為方向的網路證據。使用 Python 3.10+（測試需 3.11+）
與已連上既有 tailnet 的 Tailscale CLI。收據版本由 Python 程式的 SHA-256 識別，
對照執行 checkout 的 `git rev-parse HEAD`。每輪用新 UUID，兩端時鐘需同步，
全部採集於 30 分鐘內。範例均從本目錄執行。

| 服務 | 埠 | HTTP 檢查 | 證據界線 |
| --- | --- | --- | --- |
| MRL_Bridge | 7800 | GET /health | 比對服務身分與 API／PG／Redis 欄位 |
| MRL_RuntimeOS | 8790 | GET /api/mrl/health | 比對產品身分與 status |
| MRL_Inference（同時列出 Windows 服務 MRL_Inference_v5） | 7500 | GET /health | 歷史登錄路徑候選，HTTP 2xx 的服務身分仍待核對 |
| MRL_FlowAgent_API | 7900 | GET /health | 歷史登錄路徑候選，HTTP 2xx 的服務身分仍待核對 |
| MRL_3DScanner_ProductBridge | 3050 | GET /health | 獨立端點，HTTP 2xx 的服務身分仍待核對 |

埠基準來自 `config/MRL_PORT_MAP.json`、PR #707 與
`MRL_AI_SYSTEM/deploy/dl580/MRL_Network_Receipt.ps1`。RuntimeOS 路徑及產品欄位來自
`MRL_RuntimeServer.js`。Bridge 路徑、`x-api-key` 和回應格式來自 `MRL_Bridge/server.js`。
埠登錄是候選，Windows 採集器會另外記錄目前 listener、bind 和 PID。直接連線可能因既有授權
或 loopback-only 綁定而不可用。若實機使用已授權的 Serve HTTPS 或內部 Bridge 轉接，
將它另外記為該路徑的證據。此版自動探測固定埠上的 tailnet IPv4 HTTP，不猜測轉接入口。

### 1. Windows Server 2019（DL580）

選擇已有受限 ACL、僅管理員和必要服務帳號可存取的 DL580 本地目錄。
用兩端當期 `tailscale ip -4` 的結果互填對方位址。Mac CLI 若不在 PATH，
可用 `/Applications/Tailscale.app/Contents/MacOS/Tailscale ip -4`。

```powershell
$root = 'D:\mrl\artifacts\network_receipts'
$run = [guid]::NewGuid().ToString()
$private = Join-Path $root $run
New-Item -ItemType Directory -Path $private | Out-Null
$macIp = Read-Host 'Mac current Tailscale IPv4'

$win = powershell -NoProfile -File .\MRL_tailnet_bridge_receipt_v1.ps1 -OutDir $private |
  ConvertFrom-Json
$dl = py -3 .\MRL_tailnet_cross_device_receipt_v1.py collect --role dl580 `
  --run-id $run --peer-ip $macIp --out-dir $private | ConvertFrom-Json
$run
```

Windows 採集器檢查 `WIN-PBVUI7VK2A6`、服務和 socket bind，Python 同時收集目前的
`status --json`、`ip -4`、`netcheck`、`serve status`、DL580 → Mac 的 ping
和 DL580 的五個 loopback 端點。netcheck 會向 Tailscale 診斷基礎設施送網路探測。
原始命令 stdout/stderr、MagicDNS、設備標籤及網路位址留在私有 JSON。
若 Windows 只提供 `python` 命令，以下各例的 `py -3` 以 `python` 代替。

如要做認證後 Bridge 讀回，在同一輪目錄建立一個單次測試檔。選擇已允許 Bridge 讀取的
測試目錄。只把測試檔路徑、雜湊及 run ID 交給 Mac。

```powershell
$canary = Join-Path $private 'MRL_Tailnet_Canary.txt'
$bytes = [Text.Encoding]::ASCII.GetBytes([guid]::NewGuid().ToString())
$stream = [IO.File]::Open($canary, [IO.FileMode]::CreateNew)
try { $stream.Write($bytes, 0, $bytes.Length) } finally { $stream.Dispose() }
$canaryHash = (Get-FileHash -Algorithm SHA256 -LiteralPath $canary).Hash.ToLowerInvariant()
$canary
$canaryHash
```

### 2. Mac（同一輪 UUID）

```bash
umask 077
printf 'Run UUID: '; read -r run_id
printf 'DL580 current Tailscale IPv4: '; read -r dl580_ip
private_dir="$HOME/Library/Application Support/MRL/private-network-receipts"
python3 MRL_tailnet_cross_device_receipt_v1.py collect --role mac \
  --run-id "$run_id" --peer-ip "$dl580_ip" --out-dir "$private_dir"
```

選做讀回時，在這輪 Mac 採集命令加上
`--bridge-canary 'D:\實際測試目錄\MRL_Tailnet_Canary.txt' --canary-sha256 '<小寫雜湊>'`。
程式先核對既有 tailnet peer 和 Bridge 回應身分，再以隱藏輸入取得 API key。
既有 7800 走 tailnet 內的 HTTP，僅在確認該直達服務獲准使用現有 Bridge key 時使用此選項。
請用一次性測試檔，Bridge 會按既有行為記錄讀取路徑。驗收程式不呼叫寫檔或命令執行端點。
金鑰、檔案內容及路徑均不寫入收據。需要重新採集時，在兩端開始新 UUID。

### 3. DL580 讀回、配對與對外摘要

將 Mac 原始 JSON 經既有且獲授權的私有傳輸路徑放入同一個 DL580 目錄。Mac 的
`shasum -a 256 <私有收據>` 應符合採集當下印出的雜湊。Windows 端可用
`Get-FileHash -Algorithm SHA256 -LiteralPath $win.receipt,$dl.file,$macFile` 讀回。
在配對指令使用 Mac 原先印出的雜湊。若沒有既有授權傳輸路徑，配對保留未驗證。

```powershell
$macFile = Join-Path $private "MRL_Tailnet_mac_$run.json"
$macHash = Read-Host 'SHA-256 printed on Mac (lowercase)'
$summary = py -3 .\MRL_tailnet_cross_device_receipt_v1.py reconcile `
  --mac $macFile --mac-sha256 $macHash --dl580 $dl.file --dl580-sha256 $dl.sha256 `
  --windows-receipt $win.receipt --windows-sha256 $win.sha256 --out-dir $private |
  ConvertFrom-Json
Get-Content -Raw -LiteralPath $summary.file
(Get-FileHash -Algorithm SHA256 -LiteralPath $summary.file).Hash.ToLowerInvariant() -eq $summary.sha256
```

有做認證讀回時，在配對命令加 `--canary $canary` 以核對本機原始測試檔。若已有當期
Deployment Passport，可加 `--passport $passportPath`。摘要提供外掛 network 證據與
Passport bytes 的 SHA-256，保留 PR #704 硬體工具原介面。`MRL_hardware_smoke_v1.py`
仍自行驗證 `observation=current`、OS、runner、runtime、image 與 artifact bytes。
網路摘要不填寫 Passport 的 GPU、Runtime 或模型欄位，也不變更任何 Passport 檔案。

`DIRECT`、`DERP`、`PEER_RELAY` 是個別方向觀測到的路徑，可能在同一輪出現多種。
`TCP PASS` 表示 socket 可接通，`http=RESPONSE` 表示收到狀態碼。`401/403`
是 HTTP 已回應且請求遭拒，可能是入口或應用授權，設備狀態依其他證據判定。
`bridge_readback=PASS` 需要配對、經驗證的 Bridge 回應與 DL580 本地 canary 雜湊。
原始 peer、bind、輸出與絕對路徑只留私有，對外僅用摘要 JSON 和其 SHA-256。
未核對 tailnet grants 時為 `UNKNOWN`。可由已有權限的管理員在現行管理介面逐項比對設備身分、
標籤與核准的來源／目的埠，對外只記核對結果。

iPhone 使用既有 Tailscale 連線後，由 Safari 或既有 MRL iPhone 客戶端開啟當前授權的私有健康端點，
記下 UTC、實際服務、HTTP 狀態及是否有應用回應，將原證據留在 DL580。手機端手動健康回應
應另立證據，不能用 Mac 結果代填。此自動摘要的 iPhone 欄位保持 `UNRUN`。

### 4. 工程測試與回復

```bash
python3 -m unittest -v test_MRL_tailnet_cross_device_receipt_v1
```

GitHub 的矩陣只跑合成測試，Windows 加上原 PowerShell 採集器語法解析。
兩端的操作只產生收據及選用的測試檔。需退出本輪時停止採集，將本輪測試檔及收據留在私有證據目錄。
程式回復以反向提交回到 PR #707 的前一版本，保留原版本歷史。沒有服務設定回復步驟。
實機、iPhone、授權讀回和部署以當次證據單獨驗收。
