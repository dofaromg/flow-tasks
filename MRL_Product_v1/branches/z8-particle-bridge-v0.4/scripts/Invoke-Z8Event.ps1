[CmdletBinding(DefaultParameterSetName = 'Text')]
param(
    [Parameter(Mandatory = $true)]
    [ValidateSet('weiliao', 'xiaozhi')]
    [string]$Source,

    [Parameter(ParameterSetName = 'Text')]
    [string]$Text,

    [Parameter(ParameterSetName = 'Voice')]
    [string]$AudioRef,

    [Parameter(ParameterSetName = 'Voice')]
    [string]$Codec = 'unknown',

    [string]$TargetId,
    [string]$DeviceId = 'owned-z8',
    [string]$BridgeUrl = 'http://127.0.0.1:8788',
    [string]$ProjectRoot = (Split-Path -Parent $PSScriptRoot)
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function Get-MrlEnvValue {
    param([string]$Name)
    $processValue = [Environment]::GetEnvironmentVariable($Name, 'Process')
    if ($processValue) { return $processValue }
    $envPath = Join-Path $ProjectRoot '.env'
    if (Test-Path -LiteralPath $envPath) {
        $match = Get-Content -LiteralPath $envPath | Where-Object { $_ -match "^$([regex]::Escape($Name))=" } | Select-Object -Last 1
        if ($match) { return $match.Substring($match.IndexOf('=') + 1).Trim().Trim('"').Trim("'") }
    }
    return $null
}

$secret = Get-MrlEnvValue -Name 'Z8_DEVICE_SHARED_SECRET'
if (-not $secret) { throw 'Z8_DEVICE_SHARED_SECRET is not set in the process or .env.' }
if ($Source -eq 'weiliao' -and -not $Text) { throw '-Text is required for a weiliao event.' }
if ($Source -eq 'xiaozhi' -and -not $AudioRef) { throw '-AudioRef is required for a xiaozhi event.' }

$event = [ordered]@{
    event_id = "$Source-$([guid]::NewGuid().ToString('N'))"
    source = $Source
    kind = if ($Source -eq 'weiliao') { 'text' } else { 'voice' }
    device_id = $DeviceId
    occurred_at = [DateTimeOffset]::UtcNow.ToString('o')
}
if ($Source -eq 'weiliao') { $event['text'] = $Text }
else { $event['audio'] = [ordered]@{ ref = $AudioRef; codec = $Codec; duration_ms = 0 } }
if ($TargetId) { $event['target'] = [ordered]@{ type = 'user'; id = $TargetId } }

$body = $event | ConvertTo-Json -Depth 8 -Compress
$hmac = [Security.Cryptography.HMACSHA256]::new([Text.Encoding]::UTF8.GetBytes($secret))
try {
    $signature = [Convert]::ToBase64String($hmac.ComputeHash([Text.Encoding]::UTF8.GetBytes($body)))
}
finally {
    $hmac.Dispose()
}

Invoke-RestMethod -Method Post -Uri "$($BridgeUrl.TrimEnd('/'))/v1/z8/events" `
    -ContentType 'application/json; charset=utf-8' `
    -Headers @{ 'X-MRL-Signature' = $signature } `
    -Body ([Text.Encoding]::UTF8.GetBytes($body))
