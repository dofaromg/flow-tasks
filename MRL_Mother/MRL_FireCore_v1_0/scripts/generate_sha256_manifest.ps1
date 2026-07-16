param(
  [string]$Root = (Get-Location).Path,
  [string]$OutFile = "MRL_FireCore_v1_0_SHA256SUMS.txt"
)

$ErrorActionPreference = "Stop"
$outPath = Join-Path $Root $OutFile
Get-ChildItem -Path $Root -File -Recurse | Sort-Object FullName | ForEach-Object {
  $rel = $_.FullName.Substring($Root.Length).TrimStart('\','/') -replace '\','/'
  $hash = (Get-FileHash -Algorithm SHA256 -Path $_.FullName).Hash.ToLowerInvariant()
  "$hash  $rel"
} | Set-Content -Encoding UTF8 $outPath
Write-Host "SHA256 evidence written: $outPath"
