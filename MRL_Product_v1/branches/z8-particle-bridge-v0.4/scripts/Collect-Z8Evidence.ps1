[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [ValidateSet('xiaozhi', 'weiliao')]
    [string]$Channel,
    [string]$PackageName,
    [string]$OutputRoot = 'D:\MRL_Product_v1\evidence\z8'
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$adb = (Get-Command adb -ErrorAction Stop).Source
$connected = & $adb devices | Select-Object -Skip 1 | Where-Object { $_ -match "\tdevice$" }
if (@($connected).Count -ne 1) { throw "Expected exactly one authorized Z8; found $(@($connected).Count)." }

$stamp = Get-Date -Format 'yyyyMMdd-HHmmss'
$privateRoot = Join-Path $OutputRoot "$Channel-$stamp-private"
$shareRoot = Join-Path $OutputRoot "$Channel-$stamp-share"
New-Item -ItemType Directory -Path $privateRoot -Force | Out-Null
New-Item -ItemType Directory -Path $shareRoot -Force | Out-Null

function Save-AdbOutput {
    param([string]$Name, [string[]]$Arguments)
    & $adb @Arguments 2>&1 | Out-File -LiteralPath (Join-Path $privateRoot $Name) -Encoding utf8
}

Save-AdbOutput -Name 'getprop.txt' -Arguments @('shell', 'getprop')
Save-AdbOutput -Name 'packages.txt' -Arguments @('shell', 'pm', 'list', 'packages', '-f')
Save-AdbOutput -Name 'activity-before.txt' -Arguments @('shell', 'dumpsys', 'activity', 'activities')
Save-AdbOutput -Name 'window-before.txt' -Arguments @('shell', 'dumpsys', 'window', 'windows')
Save-AdbOutput -Name 'media-codec.txt' -Arguments @('shell', 'dumpsys', 'media.codec')
if ($PackageName) {
    Save-AdbOutput -Name 'package-detail.txt' -Arguments @('shell', 'dumpsys', 'package', $PackageName)
}

Read-Host "On the owned Z8, perform exactly one $Channel action, then press Enter"
Save-AdbOutput -Name 'activity-after.txt' -Arguments @('shell', 'dumpsys', 'activity', 'activities')
Save-AdbOutput -Name 'window-after.txt' -Arguments @('shell', 'dumpsys', 'window', 'windows')
Save-AdbOutput -Name 'logcat-after.txt' -Arguments @('logcat', '-d', '-v', 'threadtime', '-t', '5000')

$redactions = @(
    @{ Pattern = '[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}'; Replacement = '[REDACTED_EMAIL]' },
    @{ Pattern = '\b(?:\d{1,3}\.){3}\d{1,3}\b'; Replacement = '[REDACTED_IP]' },
    @{ Pattern = '\b(?:[0-9A-Fa-f]{2}[:-]){5}[0-9A-Fa-f]{2}\b'; Replacement = '[REDACTED_MAC]' },
    @{ Pattern = '(?i)(authorization|access[_-]?token|channel[_-]?secret)\s*[:=]\s*\S+'; Replacement = '$1=[REDACTED_SECRET]' }
)
foreach ($file in Get-ChildItem -LiteralPath $privateRoot -File) {
    $text = Get-Content -LiteralPath $file.FullName -Raw
    foreach ($rule in $redactions) { $text = $text -replace $rule.Pattern, $rule.Replacement }
    Set-Content -LiteralPath (Join-Path $shareRoot $file.Name) -Value $text -Encoding utf8
}

$metadata = [ordered]@{
    channel = $Channel
    captured_at = [DateTimeOffset]::Now.ToString('o')
    package_hint = $PackageName
    capture_mode = 'read-only adb evidence; no log clear, install, write, root, or endpoint replacement'
}
$metadata | ConvertTo-Json -Depth 5 | Set-Content -LiteralPath (Join-Path $shareRoot 'capture.json') -Encoding utf8
$zipPath = Join-Path $OutputRoot "$Channel-$stamp-share.zip"
Compress-Archive -Path (Join-Path $shareRoot '*') -DestinationPath $zipPath -CompressionLevel Optimal
Write-Host "Private raw evidence: $privateRoot"
Write-Host "Redacted share ZIP: $zipPath"
