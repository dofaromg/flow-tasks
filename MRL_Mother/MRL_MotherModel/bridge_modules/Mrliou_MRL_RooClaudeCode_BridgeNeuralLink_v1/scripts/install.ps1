#!/usr/bin/env powershell
# MRL_RooClaudeCode_BridgeNeuralLink_v1 Installation Script
# Target: DL580 Windows Runtime
# Purpose: Install Node.js dependencies and validate bridge module

param(
    [string]$ModuleRoot = "D:\MRL_Mother\bridge_modules\Mrliou_MRL_RooClaudeCode_BridgeNeuralLink_v1",
    [switch]$Force
)

$ErrorActionPreference = "Stop"
$VerbosePreference = "Continue"

Write-Host "========================================"
Write-Host "MRL_RooClaudeCode_BridgeNeuralLink_v1"
Write-Host "Installation Script"
Write-Host "========================================"

# Verify module root exists
if (-not (Test-Path $ModuleRoot)) {
    Write-Error "Module root not found: $ModuleRoot"
    exit 1
}

Write-Host "[1/5] Checking module structure..."
$requiredDirs = @("src", "config", "docs", "evidence")
foreach ($dir in $requiredDirs) {
    $path = Join-Path $ModuleRoot $dir
    if (-not (Test-Path $path)) {
        Write-Error "Missing directory: $path"
        exit 1
    }
    Write-Host "  ✓ $dir"
}

# Check for source files
Write-Host "[2/5] Verifying source files..."
$sourceFiles = @(
    "src/BridgeOrchestrator.ts",
    "src/SocketTransport.ts",
    "src/TaskChannel.ts",
    "src/BaseChannel.ts",
    "src/index.ts"
)
foreach ($file in $sourceFiles) {
    $path = Join-Path $ModuleRoot $file
    if (-not (Test-Path $path)) {
        Write-Error "Missing source file: $path"
        exit 1
    }
    $size = (Get-Item $path).Length
    Write-Host "  ✓ $file ($size bytes)"
}

# Check for package.json
Write-Host "[3/5] Checking Node.js dependencies..."
$packageJsonPath = Join-Path $ModuleRoot "package.json"
if (-not (Test-Path $packageJsonPath)) {
    Write-Host "  ⚠ package.json not found - skipping npm install"
    Write-Host "  Note: Ensure socket.io-client and @roo-code/types are installed"
} else {
    Write-Host "  ✓ package.json found"
    Write-Host "  Note: Run 'npm install' from module directory to install dependencies"
}

# Verify manifest
Write-Host "[4/5] Validating module manifest..."
$manifestPath = Join-Path $ModuleRoot "module.manifest.json"
if (-not (Test-Path $manifestPath)) {
    Write-Error "Missing module.manifest.json"
    exit 1
}

try {
    $manifest = Get-Content $manifestPath -Raw | ConvertFrom-Json
    Write-Host "  ✓ manifest.json valid"
    Write-Host "  ✓ module_id: $($manifest.module_id)"
    Write-Host "  ✓ version: $($manifest.version)"
} catch {
    Write-Error "Invalid JSON in module.manifest.json: $_"
    exit 1
}

# Check configuration files
Write-Host "[5/5] Verifying configuration files..."
$configFile = Join-Path $ModuleRoot "config/dl580_bridge.config.json"
if (-not (Test-Path $configFile)) {
    Write-Error "Missing configuration: $configFile"
    exit 1
}

try {
    $config = Get-Content $configFile -Raw | ConvertFrom-Json
    Write-Host "  ✓ dl580_bridge.config.json valid"
    Write-Host "  ✓ target_runtime: $($config.target_runtime)"
    Write-Host "  ✓ protocol: $($config.transport.protocol)"
} catch {
    Write-Error "Invalid JSON in dl580_bridge.config.json: $_"
    exit 1
}

Write-Host ""
Write-Host "========================================"
Write-Host "✓ Installation validation PASS"
Write-Host "========================================"
Write-Host ""
Write-Host "Next steps:"
Write-Host "  1. Run verify.ps1 to validate all components"
Write-Host "  2. Run package.ps1 to create deployment package"
Write-Host "  3. Deploy to D:\MRL_Mother on DL580"
Write-Host ""

exit 0
