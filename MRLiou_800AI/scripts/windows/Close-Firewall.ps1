[CmdletBinding()]
param(
    [ValidateRange(1, 65535)][int]$Port = 8787
)

$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot 'Common.ps1')
Assert-MRLAdministrator

$ruleName = "MRLiou 800AI TCP $Port"
Get-NetFirewallRule -DisplayName $ruleName -ErrorAction SilentlyContinue | Remove-NetFirewallRule
Write-Host "Firewall rule removed if present: $ruleName"
