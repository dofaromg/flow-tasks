[CmdletBinding()]
param(
    [ValidateSet('qwen-main', 'muse-agent')]
    [string]$Engine,
    [ValidateSet('chatgpt', 'line')]
    [string]$VoiceMode,
    [string]$BridgeUrl = 'http://127.0.0.1:8788',
    [string]$ProjectRoot = (Split-Path -Parent $PSScriptRoot)
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
if (-not $Engine -and -not $VoiceMode) { throw 'Specify -Engine, -VoiceMode, or both.' }

$token = [Environment]::GetEnvironmentVariable('Z8_CONTROL_TOKEN', 'Process')
if (-not $token) {
    $envPath = Join-Path $ProjectRoot '.env'
    if (Test-Path -LiteralPath $envPath) {
        $line = Get-Content -LiteralPath $envPath | Where-Object { $_ -match '^Z8_CONTROL_TOKEN=' } | Select-Object -Last 1
        if ($line) { $token = $line.Substring($line.IndexOf('=') + 1).Trim().Trim('"').Trim("'") }
    }
}
if (-not $token) { throw 'Z8_CONTROL_TOKEN is not set in the process or .env.' }
$headers = @{ Authorization = "Bearer $token" }
$base = $BridgeUrl.TrimEnd('/')

if ($Engine) {
    Invoke-RestMethod -Method Post -Uri "$base/v1/control/engine" `
        -ContentType 'application/json' -Headers $headers `
        -Body (@{ engine = $Engine } | ConvertTo-Json -Compress) | Out-Host
}
if ($VoiceMode) {
    Invoke-RestMethod -Method Post -Uri "$base/v1/control/voice" `
        -ContentType 'application/json' -Headers $headers `
        -Body (@{ voice_mode = $VoiceMode } | ConvertTo-Json -Compress) | Out-Host
}
