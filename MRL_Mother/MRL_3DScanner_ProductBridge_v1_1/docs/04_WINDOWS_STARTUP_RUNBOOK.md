# DL580 / Windows Server 2019 開機恢復修補

此增量修補既有 ProductBridge；不建立平行產品。原始版本：
`dofaromg/flow-tasks@1b10f5605ec5542f2271315e38d8302c3f1d387a`。
原有 `included/`、`MANIFEST.json`、`CHECKSUMS.sha256` 保留；原始 checksum
描述原始交付，不代表修補後檔案。修補內容另用 `PATCH_MANIFEST.json` 核對。

## 本次驗證界線

來源及測試在 macOS 暫存環境執行。PowerShell 7.4.6 解析與 mock 測試不等於
Windows PowerShell 5.1／Task Scheduler 實測。尚未取得可用 DL580 管道，沒有
D: 安裝、重開機或恢復 PASS。Tailscale CLI 未能載入設定；沒有嘗試猜測 SSH
帳號或密碼。Drive 修復版資料夾可讀，但抽查 `MRL_start_bridge.ps1` 返回
0 bytes，無法證明內容與 GitHub 相同。保留 Drive 原始結構及檔案。

## 方案

使用內建 Task Scheduler，單一 `\MRL\MRL_3DScanner_ProductBridge` 排程：
SYSTEM、無需登入、開機延遲 30 秒、每分鐘恢復觸發、失敗每分鐘重試三次、
IgnoreNew、無三天執行上限。監督程式用全域 mutex 防重複，Node 指定絕對
server.js 與工作目錄，固定 3050、stdout/stderr 分檔。Node 退出後十秒重啟；
啟動寬限 60 秒後連續三次健康失敗才停止自己的程序樹並恢復。

入口與出口只走 DL580 的 Tailscale 位址 `100.78.70.78`（ROOT 定義）。Node 只監聽
`100.78.70.78:3050` 與 `127.0.0.1:3050`（本機健康檢查用），拒絕 0.0.0.0／::；
任一位址綁定失敗就退出，不改綁其他網卡。開機時若 Tailscale 位址尚未出現，
監督程式記錄 `WAIT_BIND_ADDRESS` 並等待，不啟動 Node；位址出現後記錄
`BIND_ADDRESS_READY`。回執的 `listenAddresses` 保存實際監聽位址。非 DL580 的
測試環境須明確設定 `MRL_BRIDGE_BIND=127.0.0.1`，否則會因沒有該位址而拒絕啟動。

若 3050 被其他程序占用，拒絕啟動，絕不以埠號殺程序。健康檢查同時比对
service/version/port、安裝 instance、PID、CreationDate、執行檔與監聽 PID。
安全停止先禁用排程、寫 stop.request，等待監督程式停止；必要時只停止
符合完整身分的 Node 程序樹。移除僅移除本安裝排程，保留所有資料與回執。
SYSTEM 執行前拒絕 Everyone／Authenticated Users／Users 的廣泛寫入 ACL；除根目錄
外，也檢查 node.exe、python.exe、backend（只排除掃描資料目錄
`backend\MRL_3D_Reconstruction_Server\storage` 的絕對路徑，不排除任何其他
名為 storage 的套件資料夾）、scripts 及相依目錄中的所有子目錄與載入檔案，
避免子目錄或檔案上單獨設定的可寫 ACE 繞過父目錄檢查。
檢查範圍包含部署根目錄、scripts、backend、既有 `.bridge` 狀態目錄、
node.exe 與 python.exe 所在目錄，python.exe 的 venv 根目錄（若存在
`pyvenv.cfg`）、該檔 `home` 指向的基底解譯器目錄，以及 `-DependencyPath`
的每一個目錄（它們會被放到 SYSTEM 的 PATH 前面，並以解析後的絕對路徑儲存）。
這些 Python 目錄的檢查只讀設定檔，不在 ACL 通過前執行 python.exe。
ACL 與路徑正規化在 `scripts/MRL_bridge_acl.ps1`；排程恢復觸發必須已開始且
重複期間為無限，不能把 StartBoundary 推到未來或縮短 RepetitionDuration。
寫入、附加、刪除、變更權限、取得擁有權與 GenericWrite／GenericAll 都視為廣泛寫入。
部署程式碼、Node、Python 及所有依賴目錄須只允許受信管理者修改；本次不
自動修改既有 ACL、開防火牆或其他排程。

設定變更不能直接覆蓋運作中的任務；先停止並安全移除，備份
`.bridge\config.json` 後改名保存，再用新路徑註冊。重複使用相同參數註冊
只回報現有排程；不重設觸發或啟動第二個程序。註冊／停止／啟動亦會核對排程
主體、動作與工作目錄、開機及每分鐘觸發、重啟設定和電源設定；任何漂移都拒絕操作。
監督程式將 Node 與其後代放入 kill-on-close Job Object，Node 意外結束時結束
仍在執行的 Python/COLMAP 後代，再進行恢復。

## 0. 先盤點，保留 D: 原始版本

以系統管理員開啟 **Windows PowerShell 5.1**。`$root` 必須替換成實機目前
修復版所在目錄。舊文件的 `D:\MRL_3DScanner_ProductBridge_v1` 只是歷史
預設，不能當作已確認路徑。`$patch` 是解壓此修補包的暫存位置。

```powershell
$root = Read-Host 'DL580 現有 ProductBridge 完整 D: 路徑'
$root = (Resolve-Path $root).Path
$patch = 'D:\MRL_patch_staging\MRL_3DScanner_ProductBridge_v1_1'
$inventory = Join-Path $root ('MRL_before_patch_' + (Get-Date -Format 'yyyyMMdd_HHmmss'))
New-Item -ItemType Directory $inventory | Out-Null
Get-NetTCPConnection -LocalPort 3050 -State Listen -ErrorAction SilentlyContinue |
  Format-List * | Out-File "$inventory\port3050.txt"
Get-CimInstance Win32_Process | Select-Object ProcessId,ParentProcessId,Name,ExecutablePath,CommandLine,CreationDate |
  ConvertTo-Json -Depth 6 | Set-Content "$inventory\processes.json"
Get-ScheduledTask | Select-Object TaskName,TaskPath,State,Actions |
  ConvertTo-Json -Depth 8 | Set-Content "$inventory\tasks.json"
Get-CimInstance Win32_Service | Select-Object Name,State,StartMode,PathName |
  ConvertTo-Json -Depth 6 | Set-Content "$inventory\services.json"
Get-ChildItem "$root\scripts","$root\backend" -Recurse -File |
  Where-Object { $_.FullName -notmatch '\\(node_modules|storage)\\' } |
  Get-FileHash -Algorithm SHA256 | Export-Csv "$inventory\source-hashes.csv" -NoTypeInformation
```

核對 listener 的 ExecutablePath、CommandLine 與現有根目錄後，手動停止
確認屬於這套 bridge 的舊互動視窗。發現舊服務或其他啟動排程時，先匯出其
設定並釐清責任；不要自動刪除。若 listener 是 `node server.js` 相對路徑，
僅凭該命令不足以確認根目錄。不能確認時停在盤點階段。

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "$patch\scripts\MRL_apply_patch.ps1" -TargetRoot $root
if ($LASTEXITCODE -ne 0) { throw 'Patch application failed' }
```

套用前驗證所有來源 hash，只接受 pinned GitHub 原文或同一修補版本。
Drive 實機修復內容若不同會拒絕，需先保存差異再人工合併；不能強制覆蓋。
備份／套用回執在 `.bridge\backups\<time>\`；不觸及 storage 或 included。
套用腳本複製失敗時保留已完成回執與備份，重新執行能繼續；保留失敗訊息。

## 1. 相依安裝與註冊

指定已安裝、受保護的 Node 路徑及 Python 真正執行檔。Node backend 已無 npm
套件；安裝腳本在 package.json 無 dependencies 時記錄 NODE_PACKAGES_NONE。
建議在既有根目錄建立專用 Python venv，避免 SYSTEM 看不到互動使用者的套件。
COLMAP 路徑須包含實際可執行檔及必要 DLL，從 SYSTEM 執行環境實測才算可用。

```powershell
$node = 'C:\Program Files\nodejs\node.exe'
$npm = 'C:\Program Files\nodejs\npm.cmd'
$basePython = Read-Host '已安裝的 python.exe 完整路徑'
& $basePython -m venv "$root\.venv"
if ($LASTEXITCODE -ne 0) { throw 'venv failed' }
$python = "$root\.venv\Scripts\python.exe"
& "$root\scripts\MRL_install_bridge.ps1" -PythonPath $python -NpmPath $npm
if (-not $?) { throw 'Dependency install failed' }
$dependencyPath = Read-Host 'COLMAP 等依賴目錄（以分號分隔；缺少可留空）'
& "$root\scripts\MRL_register_bridge.ps1" -NodePath $node -PythonPath $python -DependencyPath $dependencyPath
& "$root\scripts\MRL_status_bridge.ps1"
& "$root\scripts\MRL_start_bridge.ps1"
if ($LASTEXITCODE -ne 0) { throw 'Start failed' }
& "$root\scripts\MRL_health_bridge.ps1"
if ($LASTEXITCODE -ne 0) { throw 'Health failed' }
```

ACL 失敗時先保存 `Get-Acl`／`icacls` 輸出，再由管理員依既有帳號權限規劃
修正。不要用 Everyone FullControl 解決安裝問題。註冊不依赖使用者 PATH。

確認入口只在 Tailscale 位址：監聽清單只能有 `100.78.70.78` 與 `127.0.0.1`。

```powershell
Invoke-RestMethod 'http://100.78.70.78:3050/api/health'
Get-NetTCPConnection -LocalPort 3050 -State Listen | Select-Object LocalAddress,OwningProcess
```

## 2. 分別驗收健康、上傳、3D 功能

```powershell
& "$root\scripts\MRL_acceptance_check_bridge.ps1" -Mode Mesh
$meshExit = $LASTEXITCODE
$images = Read-Host '至少三張實際重疊照片的目錄'
& "$root\scripts\MRL_acceptance_check_bridge.ps1" -Mode Images -ImagesDirectory $images -TimeoutSeconds 1800
$imagesExit = $LASTEXITCODE
```

Mesh 驗收只證明 mesh adapter 分析，不證明照片重建。每次採唯一 scan ID，
不覆蓋舊 scans；上傳檔案逐一與原檔 hash 比對。Images 驗收才走 COLMAP
sparse reconstruction + MRL 分析；此產品目前未整合 OpenMVS dense mesh，
不能稱為 dense mesh 完成。影片 adapter 是影片診斷，不能當作幾何重建。
COLMAP 缺失獨立回 `FAIL_COLMAP_MISSING`／job `failed`／exit 3；其他缺少
MRL、Python 或 runner 報告亦為失敗。無報告的 exit 0、adapter 不符、缺少
必要输出檔案均不能 completed。Node 重啟將舊 queued/running 標記
`INTERRUPTED_BY_BACKEND_RESTART`，不偷偷重跑或刪除。

iOS 端還須另取實際裝置上傳回執：在既有 App 設定目前 DL580 位址與 3050，
上傳新掃描，核對 scan ID／檔案數／DL580 manifest，再發起工作並保存最終
job/report。localhost 驗收不證明 iPhone 網路、權限或 App 操作已成功。
App 位址須設為 `100.78.70.78:3050`（或 MagicDNS
`win-pbvui7vk2a6.tail7de813.ts.net:3050`），iPhone 必須連上同一個 Tailscale；
區網 IP 等其他位址不再能連到 bridge。

## 3. 主機重開機恢復回執

先取得健康的 status 回執路徑，再於已安排的維護時段由管理員重啟主機。
可於維護前執行 `wevtutil sl Microsoft-Windows-TaskScheduler/Operational /e:true` 啟用排程操作日誌；status 回執會保存本次開機的相關事件，讀取失敗會明確記錄。此文件不自動重啟 DL580。重新開機後 **不要先執行 start**，等待至少
90 秒，直接執行：

```powershell
$before = Read-Host '重開機前 .bridge\receipts 的健康 status JSON 完整路徑'
& "$root\scripts\MRL_status_bridge.ps1"
& "$root\scripts\MRL_health_bridge.ps1"
& "$root\scripts\MRL_acceptance_check_bridge.ps1" -Mode Mesh -BeforeRebootReceipt $before
& "$root\scripts\MRL_acceptance_check_bridge.ps1" -Mode Images -ImagesDirectory $images -TimeoutSeconds 1800 -BeforeRebootReceipt $before
```

恢復核對 host/root、開機時間確實不同、排程 Running、所有健康身分符合；
回執包含 PID、BootTime、TaskState、LastTaskResult、腳本 hash 及 task XML。
TaskState Running 才是長駐狀態，LastTaskResult 可能為 `0x41301`（正在執行），
不能要求它等於 0。要證明自動恢復，保留 task XML、啟動健康回執及 Task
Scheduler Operational 日誌；手動 start 後的 PASS 不算開機自動恢復。

程序退出恢復可另於維護期間比對 node.json 身分後停止該 Node，等待
監督程式建立新 PID；保存前後 health/status 回執。不要按埠號殺程序。

## 4. 日誌、安全停止與移除

```powershell
Get-ChildItem "$root\.bridge\logs" | Sort-Object LastWriteTime -Descending
Get-Content "$root\.bridge\logs\supervisor_$(Get-Date -Format yyyyMMdd).log" -Tail 100
& "$root\scripts\MRL_stop_bridge.ps1"
& "$root\scripts\MRL_remove_bridge.ps1"
```

停止保持 Disabled；使用 start 才重新 Enabled。移除可重複執行，保留 config、
來源備份、receipt、stdout/stderr、scan、job、outputs 及報告。日誌不自動刪除，
依既有備份政策另行歸檔。回退先安全移除，再使用 backup 與 patch manifest
恢復本次變更檔案；不要還原或刪除掃描 storage。

## 可核對的最終交付

依序交付：來源 commit／修補 hash、套用回執、註冊 XML、啟動健康回執、
upload hash 與 scan ID、重建 job/report 與功能範圍、重開機前後 bootTime／PID
與 Task Scheduler 日誌。任何尚未執行的階段保留 NOT_RUN，不能補成 PASS。

Microsoft 參考：
- https://learn.microsoft.com/en-us/windows-server/administration/windows-commands/schtasks
- https://learn.microsoft.com/en-us/powershell/module/scheduledtasks/new-scheduledtasksettingsset
