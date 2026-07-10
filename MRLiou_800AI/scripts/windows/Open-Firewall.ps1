[CmdletBinding()]
param(
    [ValidateRange(1, 65535)][int]$Port = 8787,
    [string]$RemoteAddress = 'LocalSubnet'
)

$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot 'Common.ps1')
Assert-MRLAdministrator

$ruleName = "MRLiou 800AI TCP $Port"
Get-NetFirewallRule -DisplayName $ruleName -ErrorAction SilentlyContinue | Remove-NetFirewallRule
New-NetFirewallRule -DisplayName $ruleName -Direction Inbound -Action Allow -Protocol TCP -LocalPort $Port -Profile Domain,Private -RemoteAddress $RemoteAddress | Out-Null
Write-Host "Firewall rule created: $ruleName; remote address: $RemoteAddress"
