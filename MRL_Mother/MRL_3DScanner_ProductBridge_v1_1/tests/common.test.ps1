$ErrorActionPreference='Stop'
. "$PSScriptRoot/../scripts/MRL_bridge_common.ps1"
function Assert($value,$message) { if (-not $value) { throw $message } }
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
# Parse every script before deployment. PowerShell 7 parser is only a syntax check, not Windows validation.
foreach ($file in Get-ChildItem "$PSScriptRoot/../scripts" -Filter '*.ps1') {
    $tokens=$null; $errors=$null
    $null=[Management.Automation.Language.Parser]::ParseFile($file.FullName,[ref]$tokens,[ref]$errors)
    Assert ($errors.Count -eq 0) ("Parse errors: " + $file.Name + ': ' + ($errors | Out-String))
}
'PASS: process identity, PID reuse, foreign port, foreign task, all script syntax'
