[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot 'Common.ps1')

$root = Get-MRLProjectRoot
$config = Get-MRLRuntimeConfig
$python = Get-MRLVirtualPython
$token = Get-MRLApiToken
if (-not $token) { throw 'API token is missing. Run Install-WindowsServer.ps1.' }

Set-Location $root
$env:MRL_HOME = $root
$env:MRL_HOST = [string]$config.listen_address
$env:MRL_PORT = [string]$config.port
$env:MRL_API_TOKEN = $token
$env:PYTHONUNBUFFERED = '1'

$logPath = Join-Path $root 'logs\windows-runtime.log'
$stamp = [DateTime]::UtcNow.ToString('o')
Add-Content -Path $logPath -Value "[$stamp] Starting MRLiou runtime on $($config.listen_address):$($config.port)"

& $python -m mrliou_800ai.cli serve --host ([string]$config.listen_address) --port ([int]$config.port) *>> $logPath
exit $LASTEXITCODE
