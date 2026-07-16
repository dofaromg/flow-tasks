param(
    [string]$ListenAddress = '127.0.0.1',
    [int]$Port = 8787,
    [switch]$InstallStartupTask,
    [switch]$OpenFirewall,
    [string]$RemoteAddress = 'LocalSubnet',
    [string]$Wheelhouse = ''
)
$ErrorActionPreference = 'Stop'
& (Join-Path $PSScriptRoot 'windows\Install-WindowsServer.ps1') @PSBoundParameters
