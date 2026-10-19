#requires -Version 5.1
[CmdletBinding()]
param([Parameter(Mandatory=$true)][string]$TargetRoot)
$ErrorActionPreference='Stop'
$TargetRoot=(Resolve-Path $TargetRoot).Path
if ($TargetRoot -notmatch '^D:\\' -or -not (Test-Path (Join-Path $TargetRoot 'backend\MRL_3D_Reconstruction_Server\server.js'))) { throw 'Select the existing D: ProductBridge root; do not create a second deployment' }
if (@(Get-NetTCPConnection -LocalPort 3050 -State Listen -ErrorAction SilentlyContinue).Count) { throw 'Stop the identified existing bridge before applying patch; port 3050 is occupied' }
$task=Get-ScheduledTask -TaskPath '\MRL\' -TaskName 'MRL_3DScanner_ProductBridge' -ErrorAction SilentlyContinue
if ($task -and ($task.State -ne 'Disabled')) { throw 'Disable and stop existing managed task before source patching' }
# This installer and the shells that launched it carry -TargetRoot on their command
# line but are not the bridge; exclude them or the check always matches itself.
$self=@($PID); $cur=$PID
for ($i=0; $i -lt 8; $i++) {
    $parent=(Get-CimInstance Win32_Process -Filter "ProcessId=$cur" -ErrorAction SilentlyContinue).ParentProcessId
    if (-not $parent -or $self -contains $parent) { break }
    $self+=$parent; $cur=$parent
}
$live=@(Get-CimInstance Win32_Process | Where-Object { $self -notcontains $_.ProcessId -and $_.Name -match '^(node|powershell).*' -and $_.CommandLine -like ('*' + $TargetRoot + '*') })
if ($live.Count) { throw 'Existing bridge-related process still present; finish safe shutdown before patching' }
$patchRoot=Split-Path $PSScriptRoot -Parent
$manifest=Get-Content (Join-Path $patchRoot 'PATCH_MANIFEST.json') -Raw | ConvertFrom-Json
foreach ($f in $manifest.files) {
    if ($f.path -match '(^[/\\]|\.\.|:)') { throw 'Unsafe patch path' }
    $src=Join-Path $patchRoot $f.path; $dst=Join-Path $TargetRoot $f.path
    if ((Get-FileHash $src -Algorithm SHA256).Hash -ne $f.after) { throw "Patch checksum mismatch: $($f.path)" }
    if (Test-Path $dst) {
        $hash=(Get-FileHash $dst -Algorithm SHA256).Hash
        if ($hash -ne $f.after -and $hash -ne $f.before) { throw "Existing repaired source differs: $($f.path). Preserve it and review diff before overlay." }
    } elseif ($f.before) { throw "Missing existing source: $($f.path)" }
}
$backup=Join-Path $TargetRoot ('.bridge\backups\' + (Get-Date -Format 'yyyyMMdd_HHmmss_fff'))
New-Item -ItemType Directory $backup -Force | Out-Null
$applied=@()
$receiptFile=Join-Path $backup 'apply-receipt.json'
$receipt=@{time=(Get-Date -Format o); target=$TargetRoot; backup=$backup; applied=@(); source=$manifest.source; status='applying'; realDeploymentVerified=$false}
$receipt | ConvertTo-Json -Depth 8 | Set-Content $receiptFile -Encoding UTF8
try {
foreach ($f in $manifest.files) {
    $src=Join-Path $patchRoot $f.path; $dst=Join-Path $TargetRoot $f.path
    if ((Test-Path $dst) -and (Get-FileHash $dst).Hash -eq $f.after) { continue }
    if (Test-Path $dst) { $save=Join-Path $backup $f.path; New-Item -ItemType Directory (Split-Path $save) -Force | Out-Null; Copy-Item $dst $save }
    New-Item -ItemType Directory (Split-Path $dst) -Force | Out-Null
    Copy-Item $src $dst -Force
    if ((Get-FileHash $dst).Hash -ne $f.after) { throw "Copy verification failed: $($f.path)" }
    $applied += $f.path
    $receipt.applied=$applied
    $receipt | ConvertTo-Json -Depth 8 | Set-Content $receiptFile -Encoding UTF8
}
$receipt.status='applied'
} catch { $receipt.status='failed'; $receipt.error=$_.Exception.Message; throw }
finally { $receipt | ConvertTo-Json -Depth 8 | Set-Content $receiptFile -Encoding UTF8 }

Write-Output (Join-Path $backup 'apply-receipt.json')
