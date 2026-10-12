#requires -Version 5.1
. "$PSScriptRoot\MRL_bridge_common.ps1"
Assert-Administrator
$task=Get-BridgeTask; Assert-TaskOwner $task (Get-BridgeRoot)
if ($task) {
    & "$PSScriptRoot\MRL_stop_bridge.ps1"
    if (-not $?) { throw 'Stop failed; refusing removal' }
    Unregister-ScheduledTask -TaskPath $script:TaskPath -TaskName $script:TaskName -Confirm:$false
}
# Keep config, logs, receipts, original packages, and every scan/job/output.
Write-BridgeReceipt 'remove' @{dataPreserved=$true}
