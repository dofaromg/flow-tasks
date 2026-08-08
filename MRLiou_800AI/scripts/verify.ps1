param([switch]$SkipLiveApi)
$ErrorActionPreference = 'Stop'
& (Join-Path $PSScriptRoot 'windows\Verify-WindowsServer.ps1') @PSBoundParameters
