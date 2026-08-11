[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [ValidateSet('dry-run', 'apply')]
    [string]$Mode,
    [string]$BridgeUrl = 'http://127.0.0.1:8788',
    [string]$ProjectRoot = (Split-Path -Parent $PSScriptRoot)
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$token = [Environment]::GetEnvironmentVariable('Z8_CONTROL_TOKEN', 'Process')
if (-not $token) {
    $envPath = Join-Path $ProjectRoot '.env'
    if (Test-Path -LiteralPath $envPath) {
        $line = Get-Content -LiteralPath $envPath | Where-Object { $_ -match '^Z8_CONTROL_TOKEN=' } | Select-Object -Last 1
        if ($line) { $token = $line.Substring($line.IndexOf('=') + 1).Trim().Trim('"').Trim("'") }
    }
}
if (-not $token) { throw 'Z8_CONTROL_TOKEN is not set in the process or .env.' }

$body = @{ mode = $Mode } | ConvertTo-Json -Compress
Invoke-RestMethod -Method Post -Uri "$($BridgeUrl.TrimEnd('/'))/v1/control/mode" `
    -ContentType 'application/json' `
    -Headers @{ Authorization = "Bearer $token" } `
    -Body $body
