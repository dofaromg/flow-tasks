# MRL橋接轉譯中心 deployment — origin_signature: MrLiouWord
# Installs verified files into an existing DL580 runtime and restarts its existing service.
[CmdletBinding()]
param(
    [Parameter(Mandatory=$true)][string]$RuntimeRoot,
    [Parameter(Mandatory=$true)][string]$ServiceName,
    [string]$BridgeDirectory = 'D:\mrl\bridge',
    [string]$SourceRoot = (Split-Path $PSScriptRoot -Parent),
    [string]$ExpectedComputerName = 'WIN-PBVUI7VK2A6'
)
$ErrorActionPreference = 'Stop'
if ($env:COMPUTERNAME -ne $ExpectedComputerName) { throw 'MRL deployment target identity mismatch' }
foreach ($location in @($RuntimeRoot, $BridgeDirectory)) {
    if ([IO.Path]::GetPathRoot([IO.Path]::GetFullPath($location)) -ne 'D:\') {
        throw 'MRL runtime and bridge installation must remain on D:'
    }
    if (-not (Test-Path -LiteralPath $location -PathType Container)) { throw "Missing existing runtime: $location" }
}
$service = Get-Service -Name $ServiceName
if ($service.Status -ne 'Running') { throw 'Existing MRL service must be running before upgrade' }
$audit = Get-Content -LiteralPath (Join-Path $SourceRoot 'docs/MRL_Bridge_Translation_Center_v1.audit.json') -Raw | ConvertFrom-Json
$runtimeFiles = @(
    'MRL_Bridge/translation_center.py',
    'connectors/base_connector.py',
    'MRL_Mother/09_workflow/MRL_Mobius_Closure_Engine_v1.py'
)
$bridgeFiles = @('MRL_Bridge/server.js', 'MRL_Bridge/mrl_bridge_translation_center.cjs')
$plan = @()
foreach ($entry in $audit.files) {
    if (($runtimeFiles -notcontains $entry.path) -and ($bridgeFiles -notcontains $entry.path)) { continue }
    $source = Join-Path $SourceRoot $entry.path
    if ((Get-FileHash -LiteralPath $source -Algorithm SHA256).Hash.ToLowerInvariant() -ne $entry.sha256) {
        throw "MRL source checksum mismatch: $($entry.path)"
    }
    if ($bridgeFiles -contains $entry.path) {
        $target = Join-Path $BridgeDirectory (Split-Path $entry.path -Leaf)
    } else { $target = Join-Path $RuntimeRoot $entry.path }
    $existed = Test-Path -LiteralPath $target
    if ($existed) {
        $actual = (Get-FileHash -LiteralPath $target -Algorithm SHA256).Hash.ToLowerInvariant()
        if (($actual -ne $entry.sha256) -and ($actual -ne $entry.before_sha256)) {
            throw "MRL local version differs; preserve it and reconcile before installation: $target"
        }
    } elseif ($entry.before_sha256) { throw "Expected existing module missing: $target" }
    $plan += [PSCustomObject]@{ Source=$source; Target=$target; Existed=$existed; Sha256=$entry.sha256 }
}
if ($plan.Count -ne 5) { throw 'MRL deployment inventory incomplete' }
& node --check (Join-Path $SourceRoot 'MRL_Bridge/server.js')
if ($LASTEXITCODE -ne 0) { throw 'MRL Bridge syntax check failed' }
& node --test (Join-Path $SourceRoot 'MRL_Bridge/test_mrl_bridge_translation_center.cjs')
if ($LASTEXITCODE -ne 0) { throw 'MRL HTTP acceptance tests failed' }
$backup = Join-Path $BridgeDirectory ('MRL_translation_backup_' + (Get-Date -Format 'yyyyMMdd_HHmmss_fff'))
New-Item -ItemType Directory -Path $backup | Out-Null
for ($i=0; $i -lt $plan.Count; $i++) {
    if ($plan[$i].Existed) { Copy-Item -LiteralPath $plan[$i].Target -Destination (Join-Path $backup "$i.bak") }
}
$changed = $false
try {
    Stop-Service -Name $ServiceName
    $changed = $true
    foreach ($item in $plan) {
        New-Item -ItemType Directory -Force -Path (Split-Path $item.Target -Parent) | Out-Null
        Copy-Item -LiteralPath $item.Source -Destination $item.Target -Force
        if ((Get-FileHash -LiteralPath $item.Target -Algorithm SHA256).Hash.ToLowerInvariant() -ne $item.Sha256) {
            throw 'MRL installed file checksum mismatch'
        }
    }
    Start-Service -Name $ServiceName
    $verified = $false
    for ($attempt=0; $attempt -lt 15; $attempt++) {
        try {
            $response = Invoke-WebRequest -UseBasicParsing -Uri 'http://127.0.0.1:7800/version' -TimeoutSec 3
            $version = $response.Content | ConvertFrom-Json
            if (($response.Headers['X-MRL-Affiliation'] -eq 'MRL') -and
                ($version.bridge_translation.schema -eq 'MRL.BridgeTranslationCenter.v1')) { $verified = $true; break }
        } catch { }
        Start-Sleep -Seconds 1
    }
    if (-not $verified) { throw 'MRL live bridge verification failed' }
    $receipt = [PSCustomObject]@{
        status='MRL_BRIDGE_TRANSLATION_DEPLOYMENT_PASS'; origin_signature='MrLiouWord';
        computer=$env:COMPUTERNAME; timestamp=(Get-Date).ToUniversalTime().ToString('o');
        service=$ServiceName; scope='MRL_Bridge live HTTP; Python modules installed, process reload still required';
        backup=$backup; files=$plan
    }
    $receipt | ConvertTo-Json -Depth 6 | Set-Content -Encoding UTF8 -LiteralPath (Join-Path $backup 'deployment_receipt.json')
    $receipt | ConvertTo-Json -Depth 6
} catch {
    if ($changed) {
        Stop-Service -Name $ServiceName -ErrorAction SilentlyContinue
        for ($i=0; $i -lt $plan.Count; $i++) {
            if ($plan[$i].Existed) { Copy-Item -LiteralPath (Join-Path $backup "$i.bak") -Destination $plan[$i].Target -Force }
            elseif (Test-Path -LiteralPath $plan[$i].Target) { Remove-Item -LiteralPath $plan[$i].Target }
        }
        Start-Service -Name $ServiceName
    }
    throw
}
