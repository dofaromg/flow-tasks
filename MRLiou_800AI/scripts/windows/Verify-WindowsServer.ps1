[CmdletBinding()]
param(
    [switch]$SkipLiveApi
)

$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot 'Common.ps1')

$root = Get-MRLProjectRoot
Set-Location $root
$python = Get-MRLVirtualPython

& $python -m unittest discover -s tests -v
if ($LASTEXITCODE -ne 0) { throw 'Unit tests failed.' }

& $python -m mrliou_800ai.cli health | Out-Null
if ($LASTEXITCODE -ne 0) { throw 'CLI health check failed.' }

& $python examples\make_cfd_mass_sample.py | Out-Null
if ($LASTEXITCODE -ne 0) { throw 'CFD sample generation failed.' }

$verifyOut = Join-Path $root 'runs\verify_windows_mass'
Remove-Item $verifyOut -Recurse -Force -ErrorAction SilentlyContinue
& $python -m mrliou_800ai.cli mass-audit --data examples\cfd_mass_sample.npz --out $verifyOut | Out-Null
if ($LASTEXITCODE -ne 0) { throw 'Mass audit command failed.' }
if (-not (Test-Path (Join-Path $verifyOut 'mass_audit.json'))) { throw 'Mass audit output is missing.' }

$configPath = Join-Path $root 'config\windows_server.runtime.json'
$tokenPath = Join-Path $root 'secrets\api_token.txt'
if (-not (Test-Path $configPath)) { throw 'Windows runtime config is missing.' }
if (-not (Test-Path $tokenPath)) { throw 'API token file is missing.' }
if ((Get-Item $tokenPath).Length -lt 32) { throw 'API token is unexpectedly short.' }

if (-not $SkipLiveApi) {
    $config = Get-MRLRuntimeConfig
    $token = Get-MRLApiToken
    $health = Invoke-RestMethod -Method Get -Uri (Get-MRLLocalHealthUri) -TimeoutSec 5
    if (-not $health.ok) { throw 'Live health endpoint failed.' }
    $headers = @{ 'X-MRL-Token' = $token }
    $agents = Invoke-RestMethod -Method Get -Uri "http://127.0.0.1:$($config.port)/agents" -Headers $headers -TimeoutSec 5
    if (@($agents.agents).Count -ne 8) { throw 'Live agent registry did not return eight role families.' }
}

Write-Host 'DELIVERY_PASS_WINDOWS_SERVER'
