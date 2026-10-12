#requires -Version 5.1
. "$PSScriptRoot\MRL_bridge_common.ps1"
try { $h=Get-BridgeHealth (Get-BridgeConfig); Write-BridgeReceipt 'health-pass' $h; exit 0 }
catch { Write-BridgeReceipt 'health-fail' @{error=$_.Exception.Message}; exit 1 }
