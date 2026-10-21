#requires -Version 5.1
. "$PSScriptRoot\MRL_bridge_common.ps1"
Assert-Administrator
$c = Get-BridgeConfig; $task=Get-BridgeTask; Assert-TaskOwner $task $c.root
if ($task) { Disable-ScheduledTask -TaskPath $script:TaskPath -TaskName $script:TaskName | Out-Null }
New-Item -ItemType File (Join-Path $c.root '.bridge\stop.request') -Force | Out-Null
for ($i=0; $i -lt 20; $i++) {
    if (-not (Test-BridgeProcess (Get-BridgeRecord $c) $c)) { break }
    Start-Sleep 2
}
Stop-OwnedNode $c
if ($task) { Stop-ScheduledTask -TaskPath $script:TaskPath -TaskName $script:TaskName }
Write-BridgeReceipt 'stop' @{remainingListeners=@(Get-BridgeListeners)}
