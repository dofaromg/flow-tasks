param(
  [string]$DestinationRoot = "D:\modules"
)

$ErrorActionPreference = "Stop"
$SourceRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$TargetRoot = Join-Path $DestinationRoot "MRL_FireCore_v1_0"

Write-Host "MRL FireCore local backfill" -ForegroundColor Cyan
Write-Host "Source: $SourceRoot"
Write-Host "Target: $TargetRoot"

New-Item -ItemType Directory -Force -Path $TargetRoot | Out-Null

$exclude = @(".git", "node_modules", ".wrangler")
Get-ChildItem -Path $SourceRoot -Force | Where-Object { $exclude -notcontains $_.Name } | ForEach-Object {
  $dest = Join-Path $TargetRoot $_.Name
  if ($_.PSIsContainer) {
    Copy-Item -Path $_.FullName -Destination $dest -Recurse -Force
  } else {
    Copy-Item -Path $_.FullName -Destination $dest -Force
  }
}

Write-Host "Backfill copy complete." -ForegroundColor Green
& (Join-Path $TargetRoot "verify_backfill.ps1") -Root $TargetRoot
