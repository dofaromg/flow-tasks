#!/usr/bin/env powershell
# MRL_RooClaudeCode_BridgeNeuralLink_v1 Packaging Script
# Target: DL580 Windows Runtime
# Purpose: Create deployment package for D:\MRL_Mother installation

param(
    [string]$ModuleRoot = "D:\MRL_Mother\bridge_modules\Mrliou_MRL_RooClaudeCode_BridgeNeuralLink_v1",
    [string]$OutputDir = "D:\MRL_Mother\packages",
    [switch]$Force
)

$ErrorActionPreference = "Stop"
$VerbosePreference = "Continue"

Write-Host "========================================"
Write-Host "MRL_RooClaudeCode_BridgeNeuralLink_v1"
Write-Host "Packaging Script"
Write-Host "========================================"
Write-Host ""

# Verify module root
if (-not (Test-Path $ModuleRoot)) {
    Write-Error "Module root not found: $ModuleRoot"
    exit 1
}

Write-Host "[1/4] Validating module structure..."
$requiredItems = @(
    "src",
    "config",
    "docs",
    "evidence",
    "scripts",
    "module.manifest.json"
)

foreach ($item in $requiredItems) {
    $path = Join-Path $ModuleRoot $item
    if (-not (Test-Path $path)) {
        Write-Error "Missing required item: $path"
        exit 1
    }
    Write-Host "  ✓ $item"
}

Write-Host ""
Write-Host "[2/4] Creating output directory..."
if (-not (Test-Path $OutputDir)) {
    New-Item -ItemType Directory -Path $OutputDir -Force | Out-Null
    Write-Host "  ✓ Created: $OutputDir"
} else {
    Write-Host "  ✓ Output directory exists"
}

Write-Host ""
Write-Host "[3/4] Creating deployment package..."

$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$packageName = "Mrliou_MRL_RooClaudeCode_BridgeNeuralLink_v1_${timestamp}.zip"
$packagePath = Join-Path $OutputDir $packageName

try {
    # Get module directory name
    $moduleName = Split-Path $ModuleRoot -Leaf

    # Create compression object
    Add-Type -AssemblyName System.IO.Compression.FileSystem

    # Prepare items for compression
    $filesToCompress = @()

    # Get all files from module root
    $allItems = Get-ChildItem -Path $ModuleRoot -Recurse -File

    if ($allItems.Count -eq 0) {
        Write-Error "No files found in module root"
        exit 1
    }

    # Create zip file
    $zipStream = New-Object System.IO.FileStream($packagePath, [System.IO.FileMode]::Create)
    $zipArchive = New-Object System.IO.Compression.ZipArchive($zipStream, [System.IO.Compression.ZipArchiveMode]::Create)

    foreach ($item in $allItems) {
        $itemPath = $item.FullName
        $relativePath = $itemPath.Substring($ModuleRoot.Length + 1)
        $entryPath = "${moduleName}/${relativePath}" -replace '\\', '/'

        $entry = $zipArchive.CreateEntry($entryPath)
        $writer = New-Object System.IO.StreamWriter($entry.Open())
        $writer.Write([System.IO.File]::ReadAllText($itemPath))
        $writer.Close()
    }

    $zipArchive.Dispose()
    $zipStream.Close()

    $packageSize = (Get-Item $packagePath).Length
    Write-Host "  ✓ Package created: $packageName"
    Write-Host "  ✓ Size: $([Math]::Round($packageSize / 1MB, 2)) MB"

} catch {
    Write-Error "Failed to create package: $_"
    exit 1
}

Write-Host ""
Write-Host "[4/4] Generating package manifest..."

$manifestData = @{
    package_name = $packageName
    package_path = $packagePath
    package_size_bytes = $packageSize
    module_id = "Mrliou_MRL_RooClaudeCode_BridgeNeuralLink_v1"
    created_utc = Get-Date -Format "o"
    deployment_target = "D:\MRL_Mother\bridge_modules\Mrliou_MRL_RooClaudeCode_BridgeNeuralLink_v1"
    installation_steps = @(
        "1. Extract package to D:\MRL_Mother\bridge_modules\",
        "2. Run scripts\install.ps1 to validate",
        "3. Run scripts\verify.ps1 to verify",
        "4. Deploy to target runtime"
    )
}

$manifestPath = Join-Path $OutputDir "${packageName}.manifest.json"
$manifestData | ConvertTo-Json -Depth 10 | Out-File -FilePath $manifestPath -Encoding UTF8
Write-Host "  ✓ Manifest created: ${packageName}.manifest.json"

Write-Host ""
Write-Host "========================================"
Write-Host "✓ Packaging PASS"
Write-Host "========================================"
Write-Host ""
Write-Host "Package ready for deployment:"
Write-Host "  Location: $packagePath"
Write-Host "  Manifest: $manifestPath"
Write-Host ""
Write-Host "Next steps:"
Write-Host "  1. Transfer package to DL580 target system"
Write-Host "  2. Extract to D:\MRL_Mother\bridge_modules\"
Write-Host "  3. Run install.ps1 to validate"
Write-Host "  4. Run verify.ps1 to confirm readiness"
Write-Host ""

exit 0
