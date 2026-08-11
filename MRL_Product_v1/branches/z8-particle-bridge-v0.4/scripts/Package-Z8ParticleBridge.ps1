[CmdletBinding()]
param(
    [string]$ProjectRoot = (Split-Path -Parent $PSScriptRoot),
    [string]$OutputDirectory = (Join-Path (Split-Path -Parent $PSScriptRoot) 'artifacts')
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
& (Join-Path $PSScriptRoot 'Test-Z8ParticleBridge.ps1') -ProjectRoot $ProjectRoot

$name = 'Mrliou_Z8_ParticleBridge_Setup_v0.4'
$stagingBase = Join-Path ([IO.Path]::GetTempPath()) "$name-$([guid]::NewGuid().ToString('N'))"
$stagingRoot = Join-Path $stagingBase $name
New-Item -ItemType Directory -Path $stagingRoot -Force | Out-Null
New-Item -ItemType Directory -Path $OutputDirectory -Force | Out-Null

try {
    $files = Get-ChildItem -LiteralPath $ProjectRoot -File -Recurse | Where-Object {
        $relative = [IO.Path]::GetRelativePath($ProjectRoot, $_.FullName)
        $relative -notmatch '^(?:\.env$|artifacts[\\/]|data[\\/]|dist[\\/]|logs[\\/]|node_modules[\\/])'
    }
    foreach ($file in $files) {
        $relative = [IO.Path]::GetRelativePath($ProjectRoot, $file.FullName)
        $destination = Join-Path $stagingRoot $relative
        New-Item -ItemType Directory -Path (Split-Path -Parent $destination) -Force | Out-Null
        Copy-Item -LiteralPath $file.FullName -Destination $destination
    }

    $manifest = Get-ChildItem -LiteralPath $stagingRoot -File -Recurse | Sort-Object FullName | ForEach-Object {
        $relative = [IO.Path]::GetRelativePath($stagingRoot, $_.FullName).Replace('\', '/')
        $digest = (Get-FileHash -LiteralPath $_.FullName -Algorithm SHA256).Hash.ToLowerInvariant()
        "$digest  $relative"
    }
    $manifest | Set-Content -LiteralPath (Join-Path $stagingRoot 'MANIFEST.sha256') -Encoding ascii

    $zipPath = Join-Path $OutputDirectory "$name.zip"
    if (Test-Path -LiteralPath $zipPath) {
        $previous = "$zipPath.previous-$(Get-Date -Format 'yyyyMMdd-HHmmss')"
        Move-Item -LiteralPath $zipPath -Destination $previous
    }
    Compress-Archive -LiteralPath $stagingRoot -DestinationPath $zipPath -CompressionLevel Optimal
    $zipHash = (Get-FileHash -LiteralPath $zipPath -Algorithm SHA256).Hash.ToLowerInvariant()
    "$zipHash  $([IO.Path]::GetFileName($zipPath))" | Set-Content -LiteralPath "$zipPath.sha256" -Encoding ascii
    Write-Host "Package: $zipPath"
    Write-Host "SHA-256: $zipHash"
    Write-Host "Files: $($files.Count + 1)"
}
finally {
    if (Test-Path -LiteralPath $stagingBase) { Remove-Item -LiteralPath $stagingBase -Recurse -Force }
}
