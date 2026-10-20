#requires -Version 5.1
[CmdletBinding()]
param([Parameter(Mandatory=$true)][string]$NodePath, [Parameter(Mandatory=$true)][string]$PythonPath, [string]$DependencyPath = '')
. "$PSScriptRoot\MRL_bridge_common.ps1"
Assert-Administrator
$root = Get-BridgeRoot
if ($root -notmatch '^D:\\') { throw 'Register only in the existing D: deployment directory' }
$node = (Resolve-Path $NodePath).Path; $python = (Resolve-Path $PythonPath).Path
if ([IO.Path]::GetFileName($node) -ne 'node.exe' -or [IO.Path]::GetFileName($python) -ne 'python.exe') { throw 'Use absolute node.exe and real python.exe (no Store aliases)' }
$backend = Join-Path $root 'backend\MRL_3D_Reconstruction_Server'
$entry = Join-Path $backend 'server.js'
if (-not (Test-Path $entry) -or -not (Test-Path (Join-Path $backend 'node_modules'))) { throw 'Install existing backend dependencies first' }
# SYSTEM must not execute code writable by broad unprivileged groups.
# DependencyPath is prepended to SYSTEM's PATH and the runner resolves colmap/mrl3d through it.
$dependencyPathValue = Get-BridgeNormalizedDependencyPath $DependencyPath
$dependencyDirs = @($dependencyPathValue -split ';' | Where-Object { $_ })
foreach ($dir in $dependencyDirs) {
    if (-not (Test-Path -LiteralPath $dir -PathType Container)) { throw "Dependency path must be a directory: $dir" }
}
Assert-BridgeRegistrationAcl -Root $root -Backend $backend -Node $node -Python $python -DependencyDirs $dependencyDirs
$task = Get-BridgeTask; Assert-TaskOwner $task $root
$conflicts = @(Get-ScheduledTask | Where-Object {
    $candidate = $_
    -not ($candidate.TaskPath -eq $script:TaskPath -and $candidate.TaskName -eq $script:TaskName) -and (
        $candidate.TaskName -match 'MRL.*(3D|Bridge|Scanner)' -or
        @($candidate.Actions | Where-Object { $_.WorkingDirectory -eq $backend -or $_.Arguments -like ('*' + $root + '*') }).Count -gt 0
    )
})
$services = @(Get-CimInstance Win32_Service | Where-Object { $_.PathName -like ('*' + $root + '*') })
if ($conflicts.Count -or $services.Count) { throw 'Another bridge startup task/service exists; export and reconcile it before registration' }

$state = Join-Path $root '.bridge'; New-Item -ItemType Directory $state -Force | Out-Null
$configFile = Join-Path $state 'config.json'
if (Test-Path $configFile) {
    $c = Get-BridgeConfig
    if ($c.node -ne $node -or $c.python -ne $python -or (Get-BridgeNormalizedDependencyPath ([string]$c.dependencyPath)) -ne $dependencyPathValue) { throw 'Configuration change requires safe removal first' }
} else {
    if ($task) { throw 'Task exists without config; inspect before recovery' }
    $c = [ordered]@{root=$root; node=$node; python=$python; entry=$entry; port=3050; dependencyPath=$dependencyPathValue; instance=[guid]::NewGuid().ToString(); source='1b10f5605ec5542f2271315e38d8302c3f1d387a'}
    Write-BridgeJson $configFile $c
}
if ($task) { Write-BridgeReceipt 'register-existing' $null; exit 0 }
if (@(Get-BridgeListeners).Count) { throw 'Port 3050 already occupied; inspect existing process, never kill by port' }
$ps = Join-Path $env:SystemRoot 'System32\WindowsPowerShell\v1.0\powershell.exe'
$arg = '-NoProfile -NonInteractive -ExecutionPolicy Bypass -File "' + (Join-Path $root 'scripts\MRL_run_bridge.ps1') + '"'
$action = New-ScheduledTaskAction -Execute $ps -Argument $arg -WorkingDirectory $backend
$startup = New-ScheduledTaskTrigger -AtStartup
$startup.Delay = 'PT30S'
# Periodic trigger recovers a dead supervisor after restart retries are exhausted.
$watch = New-ScheduledTaskTrigger -Once -At (Get-Date).AddMinutes(1) -RepetitionInterval (New-TimeSpan -Minutes 1)
$settings = New-ScheduledTaskSettingsSet -MultipleInstances IgnoreNew -ExecutionTimeLimit ([TimeSpan]::Zero) -StartWhenAvailable -RestartCount 3 -RestartInterval (New-TimeSpan -Minutes 1) -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries
$principal = New-ScheduledTaskPrincipal -UserId 'SYSTEM' -LogonType ServiceAccount -RunLevel Highest
$scheduler=New-Object -ComObject 'Schedule.Service'
$scheduler.Connect()
try { $null=$scheduler.GetFolder('\MRL') } catch { $null=$scheduler.GetFolder('\').CreateFolder('MRL') }
Register-ScheduledTask -TaskPath $script:TaskPath -TaskName $script:TaskName -Action $action -Trigger @($startup,$watch) -Settings $settings -Principal $principal -Description "$script:OwnerTag|$root" | Out-Null
Write-BridgeReceipt 'register' @{ account='SYSTEM'; trigger='Boot + one-minute recovery'; port=3050 }
