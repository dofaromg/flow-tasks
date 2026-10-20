$ErrorActionPreference='Stop'
. "$PSScriptRoot/../scripts/MRL_bridge_common.ps1"
. "$PSScriptRoot/../scripts/MRL_bridge_acl.ps1"
function Assert($value,$message) { if (-not $value) { throw $message } }
$env:SystemRoot=(Get-Location).Path
$c=[pscustomobject]@{node='D:\node.exe';entry='D:\bridge\server.js';root='D:\bridge';instance='test-instance'}
$record=[pscustomobject]@{pid=123;created='2026-10-12T00:00:00.0000000Z'}
function Get-CimInstance { [pscustomobject]@{ExecutablePath='D:\node.exe';CreationDate=[datetime]'2026-10-12T00:00:00Z';CommandLine='"D:\node.exe" "D:\bridge\server.js"'} }
Assert (Test-BridgeProcess $record $c) 'matching process must be accepted'
$record.created='2026-10-11T00:00:00.0000000Z'
Assert (-not (Test-BridgeProcess $record $c)) 'reused PID must be rejected'
$record.created='2026-10-12T00:00:00.0000000Z'
function Get-BridgeRecord { $record }
function Get-BridgeListeners { ,123 }
function Invoke-RestMethod { [pscustomobject]@{ok=$true;service='MRL_3D_Reconstruction_Server';version='1.0.0';port=3050;pid=123;instance='test-instance'} }
Assert ((Get-BridgeHealth $c).pid -eq 123) 'matching health must pass'
function Get-BridgeListeners { ,999 }
$rejected=$false
try { Get-BridgeHealth $c | Out-Null } catch { $rejected=$true }
Assert $rejected 'foreign listener must fail health'
$rejected=$false
try { Assert-TaskOwner ([pscustomobject]@{Description='foreign-task'}) 'D:\bridge' } catch { $rejected=$true }
Assert $rejected 'foreign task must be protected'
$taskRoot=Join-Path $PSScriptRoot 'bridge'
$runScript=Join-Path $taskRoot 'scripts\MRL_run_bridge.ps1'
$boot=[pscustomobject]@{CimClass=[pscustomobject]@{CimClassName='MSFT_TaskBootTrigger'};Enabled=$true;Delay='PT30S'}
$repeat=[pscustomobject]@{CimClass=[pscustomobject]@{CimClassName='MSFT_TaskTimeTrigger'};Enabled=$true;StartBoundary=(Get-Date).AddMinutes(-1).ToString('o');Repetition=[pscustomobject]@{Interval='PT1M';Duration=''}}
$task=[pscustomobject]@{
    Description="$script:OwnerTag|$taskRoot"
    Actions=@([pscustomobject]@{
        Arguments="-NoProfile -NonInteractive -ExecutionPolicy Bypass -File `"$runScript`""
        Execute=(Join-Path $env:SystemRoot 'System32\WindowsPowerShell\v1.0\powershell.exe')
        WorkingDirectory=(Join-Path $taskRoot 'backend\MRL_3D_Reconstruction_Server')
    })
    Triggers=@($boot,$repeat)
    Principal=[pscustomobject]@{UserId='SYSTEM';LogonType='ServiceAccount';RunLevel='Highest'}
    Settings=[pscustomobject]@{
        MultipleInstances='IgnoreNew';ExecutionTimeLimit='PT0S';StartWhenAvailable=$true
        RestartCount=3;RestartInterval='PT1M';DisallowStartIfOnBatteries=$false;StopIfGoingOnBatteries=$false
    }
}
Assert-TaskOwner $task $taskRoot
$task.Principal.UserId='InteractiveUser'
$rejected=$false
try { Assert-TaskOwner $task $taskRoot } catch { $rejected=$true }
Assert $rejected 'task principal drift must be rejected'
$task.Principal.UserId='SYSTEM'
foreach ($case in @(
    @('Actions', 'Arguments', 'foreign'),
    @('Actions', 'Execute', 'foreign.exe'),
    @('Actions', 'WorkingDirectory', 'foreign'),
    @('Settings', 'MultipleInstances', 'Parallel'),
    @('Settings', 'ExecutionTimeLimit', 'PT72H'),
    @('Settings', 'RestartCount', 0),
    @('Settings', 'RestartInterval', 'PT5M'),
    @('Settings', 'StartWhenAvailable', $false),
    @('Settings', 'StopIfGoingOnBatteries', $true),
    @('Principal', 'LogonType', 'Interactive'),
    @('Principal', 'RunLevel', 'Limited')
)) {
    $copy=$task | ConvertTo-Json -Depth 12 | ConvertFrom-Json
    $target=$copy.($case[0]); if($case[0] -eq 'Actions') {$target=$target[0]}
    $target.($case[1])=$case[2]
    $rejected=$false
    try { Assert-TaskOwner $copy $taskRoot } catch {$rejected=$true}
    Assert $rejected ('task drift accepted: ' + $case[0] + '.' + $case[1])
}
$repeat.Repetition.Interval='PT2M'
$rejected=$false
try { Assert-TaskOwner $task $taskRoot } catch {$rejected=$true}
Assert $rejected 'trigger interval drift must be rejected'
$repeat.Repetition.Interval='PT1M'
$repeat.StartBoundary=(Get-Date).AddDays(7).ToString('o')
$rejected=$false
try { Assert-TaskOwner $task $taskRoot } catch {$rejected=$true}
Assert $rejected 'future recovery start must be rejected'
$repeat.StartBoundary=(Get-Date).AddMinutes(-1).ToString('o')
$repeat.Repetition.Duration='PT1H'
$rejected=$false
try { Assert-TaskOwner $task $taskRoot } catch {$rejected=$true}
Assert $rejected 'finite recovery duration must be rejected'
$repeat.Repetition.Duration=''
Assert ((Get-BridgeNormalizedDependencyPath ' D:\colmap\ ; D:\tools ') -eq 'D:\colmap;D:\tools') 'dependency path trim must not require a live filesystem'
$fixture=Get-Content "$PSScriptRoot/fixtures/upload-response.json" -Raw | ConvertFrom-Json
Assert-BridgeUploadResponse $fixture 'unique' 1
$fixture | Add-Member NoteProperty manifestPath 'D:\private\manifest.json'
$rejected=$false
try { Assert-BridgeUploadResponse $fixture 'unique' 1 } catch {$rejected=$true}
Assert $rejected 'server path leak must fail local acceptance'
# Parse every script before deployment. PowerShell 7 parser is only a syntax check, not Windows validation.
foreach ($file in Get-ChildItem "$PSScriptRoot/../scripts" -Filter '*.ps1') {
    $tokens=$null; $errors=$null
    $null=[Management.Automation.Language.Parser]::ParseFile($file.FullName,[ref]$tokens,[ref]$errors)
    Assert ($errors.Count -eq 0) ("Parse errors: " + $file.Name + ': ' + ($errors | Out-String))
}
'PASS: process identity, PID reuse, foreign port, task definition drift, recovery window, upload contract, all script syntax'
