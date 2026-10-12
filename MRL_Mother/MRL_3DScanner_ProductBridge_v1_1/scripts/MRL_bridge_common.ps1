Set-StrictMode -Version 2.0
$ErrorActionPreference = 'Stop'
$script:TaskName = 'MRL_3DScanner_ProductBridge'
$script:TaskPath = '\MRL\'
$script:OwnerTag = 'MRL-Bridge-Startup-v1'
function Get-BridgeRoot { (Resolve-Path (Join-Path $PSScriptRoot '..')).Path }
function Get-BridgeConfig {
    $c = Get-Content (Join-Path (Get-BridgeRoot) '.bridge\config.json') -Raw | ConvertFrom-Json
    if ($c.root -ne (Get-BridgeRoot) -or $c.port -ne 3050) { throw 'Config root/port mismatch' }
    return $c
}
function Assert-Administrator {
    $i = [Security.Principal.WindowsIdentity]::GetCurrent()
    if (-not ([Security.Principal.WindowsPrincipal]::new($i)).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) { throw 'Run elevated Windows PowerShell 5.1' }
}
function Get-BridgeTask { Get-ScheduledTask -TaskPath $script:TaskPath -TaskName $script:TaskName -ErrorAction SilentlyContinue }
function Assert-TaskOwner($task, $root) {
    if ($task -and $task.Description -ne "$script:OwnerTag|$root") { throw 'Task belongs to another install; refusing mutation' }
    if ($task) {
        $expected = '-NoProfile -NonInteractive -ExecutionPolicy Bypass -File "' + (Join-Path $root 'scripts\MRL_run_bridge.ps1') + '"'
        if (@($task.Actions).Count -ne 1 -or $task.Actions[0].Arguments -ne $expected -or $task.Actions[0].Execute -ne (Join-Path $env:SystemRoot 'System32\WindowsPowerShell\v1.0\powershell.exe')) { throw 'Task action changed; refusing mutation' }
    }
}
function Get-BridgeListeners { @(Get-NetTCPConnection -LocalPort 3050 -State Listen -ErrorAction SilentlyContinue | Select-Object -ExpandProperty OwningProcess -Unique) }
function Test-BridgeProcess($record, $c) {
    if (-not $record) { return $false }
    $p = Get-CimInstance Win32_Process -Filter "ProcessId=$($record.pid)" -ErrorAction SilentlyContinue
    return ($p -and $p.ExecutablePath -eq $c.node -and $p.CreationDate.ToUniversalTime().ToString('o') -eq $record.created -and $p.CommandLine.Contains('"' + $c.entry + '"'))
}
function Get-BridgeRecord($c) {
    $file = Join-Path $c.root '.bridge\node.json'
    if (Test-Path $file) { return (Get-Content $file -Raw | ConvertFrom-Json) }
    return $null
}
function Get-BridgeHealth($c) {
    $h = Invoke-RestMethod 'http://127.0.0.1:3050/api/health' -TimeoutSec 5
    $record = Get-BridgeRecord $c
    $listeners = @(Get-BridgeListeners)
    if ($h.ok -ne $true -or $h.service -ne 'MRL_3D_Reconstruction_Server' -or $h.version -ne '1.0.0' -or $h.port -ne 3050 -or $h.instance -ne $c.instance -or $h.pid -ne $record.pid -or -not (Test-BridgeProcess $record $c) -or $listeners.Count -ne 1 -or $listeners[0] -ne $h.pid) { throw 'Health/process/port identity mismatch' }
    return $h
}
function Write-BridgeJson($file, $data) {
    $temp = "$file.$PID.tmp"
    $data | ConvertTo-Json -Depth 12 | Set-Content $temp -Encoding UTF8
    Move-Item $temp $file -Force
}
function Write-BridgeReceipt($operation, $extra) {
    $root = Get-BridgeRoot
    $dir = Join-Path $root '.bridge\receipts'
    New-Item -ItemType Directory $dir -Force | Out-Null
    $task = Get-BridgeTask
    $info = if ($task) { Get-ScheduledTaskInfo -TaskPath $script:TaskPath -TaskName $script:TaskName } else { $null }
    $health = $null; $healthError = $null
    try { $health = Get-BridgeHealth (Get-BridgeConfig) } catch { $healthError = $_.Exception.Message }
    $receipt = [ordered]@{ operation=$operation; time=(Get-Date).ToUniversalTime().ToString('o'); host=$env:COMPUTERNAME; root=$root; bootTime=(Get-CimInstance Win32_OperatingSystem).LastBootUpTime.ToUniversalTime().ToString('o'); taskState=$(if($task){[string]$task.State}else{'Absent'}); lastTaskResult=$(if($info){$info.LastTaskResult}else{$null}); lastTaskRunTime=$(if($info){$info.LastRunTime.ToUniversalTime().ToString('o')}else{$null}); listeners=@(Get-BridgeListeners); health=$health; healthError=$healthError; extra=$extra; hashes=@(Get-ChildItem (Join-Path $root 'scripts') -Filter '*.ps1' | Get-FileHash -Algorithm SHA256 | Select-Object Path,Hash) }
    $name = (Get-Date -Format 'yyyyMMdd_HHmmss_fff') + '_' + $operation + '_' + [guid]::NewGuid().ToString('N') + '.json'
    $file = Join-Path $dir $name
    Write-BridgeJson $file $receipt
    if ($task) { Export-ScheduledTask -TaskPath $script:TaskPath -TaskName $script:TaskName | Set-Content "$file.task.xml" -Encoding UTF8 }
    Write-Output $file
}
function Stop-OwnedNode($c) {
    $r = Get-BridgeRecord $c
    if (Test-BridgeProcess $r $c) {
        & "$env:SystemRoot\System32\taskkill.exe" /PID $r.pid /T /F | Out-Null
        if ($LASTEXITCODE -ne 0 -and (Test-BridgeProcess $r $c)) { throw 'Could not stop owned Node process tree' }
    }
}
