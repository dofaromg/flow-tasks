[CmdletBinding()]
param(
    [string]$Destination = '',
    [switch]$IncludeSecrets
)

$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot 'Common.ps1')

$root = Get-MRLProjectRoot
if (-not $Destination) { $Destination = Join-Path (Split-Path $root -Parent) 'MRLiou_Backups' }
New-Item -ItemType Directory -Path $Destination -Force | Out-Null

$stamp = [DateTime]::UtcNow.ToString('yyyyMMddTHHmmssZ')
$temp = Join-Path $env:TEMP "mrliou_backup_$stamp"
$archive = Join-Path $Destination "MRLiou_Runtime_State_$stamp.zip"
New-Item -ItemType Directory -Path $temp -Force | Out-Null
try {
    foreach ($relative in @('config', 'data', 'logs', 'runs')) {
        $source = Join-Path $root $relative
        if (Test-Path $source) { Copy-Item $source -Destination $temp -Recurse -Force }
    }
    if ($IncludeSecrets) {
        $source = Join-Path $root 'secrets'
        if (Test-Path $source) { Copy-Item $source -Destination $temp -Recurse -Force }
    }
    Compress-Archive -Path (Join-Path $temp '*') -DestinationPath $archive -CompressionLevel Optimal -Force
} finally {
    Remove-Item $temp -Recurse -Force -ErrorAction SilentlyContinue
}
Write-Host $archive
