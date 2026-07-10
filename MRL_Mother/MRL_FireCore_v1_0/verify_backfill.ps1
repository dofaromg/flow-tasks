param(
  [string]$Root = (Get-Location).Path
)

$ErrorActionPreference = "Stop"
$ManifestPath = Join-Path $Root "MRL_FireCore_v1_0_BACKFILL_MANIFEST.json"
if (!(Test-Path $ManifestPath)) {
  throw "Manifest not found: $ManifestPath"
}

$manifest = Get-Content $ManifestPath -Raw | ConvertFrom-Json
$missing = @()
$empty = @()
$hashMismatch = @()

foreach ($file in $manifest.files) {
  $path = Join-Path $Root $file.path
  if (!(Test-Path $path)) {
    $missing += $file.path
    continue
  }
  $item = Get-Item $path
  if ($item.Length -le 0) {
    $empty += $file.path
  }
  if ($file.sha256 -and $file.sha256 -ne "MANIFEST_SELF_HASH_OMITTED") {
    $hash = (Get-FileHash -Algorithm SHA256 -Path $path).Hash.ToLowerInvariant()
    if ($hash -ne $file.sha256) {
      $hashMismatch += $file.path
    }
  }
}

$result = [ordered]@{
  root = $Root
  expected_count = $manifest.files.Count
  missing_count = $missing.Count
  empty_count = $empty.Count
  hash_mismatch_count = $hashMismatch.Count
  missing_files = $missing
  empty_files = $empty
  hash_mismatch_files = $hashMismatch
}

$result | ConvertTo-Json -Depth 8

if ($missing.Count -gt 0 -or $empty.Count -gt 0 -or $hashMismatch.Count -gt 0) {
  throw "DELIVERY_FAIL: verification did not pass."
}

Write-Host "DELIVERY_PASS: local backfill verification passed." -ForegroundColor Green
