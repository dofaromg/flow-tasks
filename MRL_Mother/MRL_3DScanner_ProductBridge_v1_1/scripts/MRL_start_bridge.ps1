#requires -Version 5.1
. "$PSScriptRoot\MRL_bridge_common.ps1"
Assert-Administrator
$c = Get-BridgeConfig; $task = Get-BridgeTask
if (-not $task) { throw 'Register the startup task first' }
Assert-TaskOwner $task $c.root
Remove-Item (Join-Path $c.root '.bridge\stop.request') -ErrorAction SilentlyContinue
Enable-ScheduledTask -TaskPath $script:TaskPath -TaskName $script:TaskName | Out-Null
Start-ScheduledTask -TaskPath $script:TaskPath -TaskName $script:TaskName
for ($i=0; $i -lt 24; $i++) {
    try { $null=Get-BridgeHealth $c; Write-BridgeReceipt 'start-pass' $null; exit 0 } catch { Start-Sleep 5 }
}
Write-BridgeReceipt 'start-fail' $null
throw '3050 did not become healthy within 120 seconds; inspect .bridge\logs'
