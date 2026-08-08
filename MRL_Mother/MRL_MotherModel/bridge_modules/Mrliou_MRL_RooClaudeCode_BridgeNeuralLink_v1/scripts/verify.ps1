#!/usr/bin/env powershell
# MRL_RooClaudeCode_BridgeNeuralLink_v1 Verification Script
# Target: DL580 Windows Runtime
# Purpose: Validate all bridge module components for deployment readiness

param(
    [string]$ModuleRoot = "D:\MRL_Mother\bridge_modules\Mrliou_MRL_RooClaudeCode_BridgeNeuralLink_v1",
    [switch]$Verbose
)

$ErrorActionPreference = "Stop"
$VerbosePreference = if ($Verbose) { "Continue" } else { "SilentlyContinue" }

$passCount = 0
$failCount = 0
$findings = @()

Write-Host "========================================"
Write-Host "MRL_RooClaudeCode_BridgeNeuralLink_v1"
Write-Host "Verification Script"
Write-Host "========================================"
Write-Host ""

# Helper functions
function Test-FileNotPlaceholder {
    param(
        [string]$Path,
        [int]$MinLines = 10
    )

    if (-not (Test-Path $Path)) {
        return $false, "File not found"
    }

    $content = Get-Content $Path -Raw
    if ([string]::IsNullOrWhiteSpace($content)) {
        return $false, "File is empty"
    }

    $lines = $content -split "`n"
    $nonEmptyLines = $lines | Where-Object { $_ -match '\S' }

    if ($nonEmptyLines.Count -lt $MinLines) {
        return $false, "File is placeholder (only $($nonEmptyLines.Count) lines)"
    }

    # Check for placeholder patterns
    if ($content -match "TODO|FIXME|PLACEHOLDER|<PLACEHOLDER|placeholder") {
        return $false, "File contains placeholder markers"
    }

    return $true, "Valid"
}

function Record-Finding {
    param(
        [string]$Category,
        [string]$Item,
        [string]$Status,
        [string]$Details = ""
    )

    $finding = @{
        Category = $Category
        Item = $Item
        Status = $Status
        Details = $Details
        Timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    }

    $findings += $finding

    if ($Status -eq "PASS") {
        $passCount++
        Write-Host "  ✓ $Item" -ForegroundColor Green
    } elseif ($Status -eq "PARTIAL") {
        Write-Host "  ⚠ $Item - $Details" -ForegroundColor Yellow
    } else {
        $failCount++
        Write-Host "  ✗ $Item - $Details" -ForegroundColor Red
    }
}

# Verify module root
Write-Host "[1/8] Validating module root..."
if (-not (Test-Path $ModuleRoot)) {
    Write-Error "Module root not found: $ModuleRoot"
    exit 1
}
Write-Host "  ✓ Module root exists"
Write-Host ""

# Verify TypeScript source files
Write-Host "[2/8] Verifying TypeScript source files..."
$sourceFiles = @(
    "src/BridgeOrchestrator.ts",
    "src/SocketTransport.ts",
    "src/TaskChannel.ts",
    "src/BaseChannel.ts",
    "src/index.ts"
)

$srcValid = $true
foreach ($file in $sourceFiles) {
    $path = Join-Path $ModuleRoot $file
    $isValid, $reason = Test-FileNotPlaceholder -Path $path -MinLines 5

    if ($isValid) {
        $size = (Get-Item $path).Length
        Record-Finding "SourceCode" $file "PASS" "$size bytes"
    } else {
        Record-Finding "SourceCode" $file "FAIL" $reason
        $srcValid = $false
    }
}

if (-not $srcValid) {
    Write-Host ""
    Write-Error "Source file validation failed"
    exit 1
}
Write-Host ""

# Verify configuration files
Write-Host "[3/8] Verifying configuration files..."
$configFile = Join-Path $ModuleRoot "config/dl580_bridge.config.json"

try {
    $config = Get-Content $configFile -Raw | ConvertFrom-Json
    Record-Finding "Configuration" "dl580_bridge.config.json" "PASS" "Valid JSON"
    Record-Finding "Configuration" "  protocol: $($config.transport.protocol)" "PASS" ""
    Record-Finding "Configuration" "  auth method: $($config.authentication.method)" "PASS" ""
} catch {
    Record-Finding "Configuration" "dl580_bridge.config.json" "FAIL" "Invalid JSON: $_"
}
Write-Host ""

# Verify module manifest
Write-Host "[4/8] Verifying module manifest..."
$manifestPath = Join-Path $ModuleRoot "module.manifest.json"

try {
    $manifest = Get-Content $manifestPath -Raw | ConvertFrom-Json
    Record-Finding "Manifest" "module.manifest.json" "PASS" "Valid JSON"
    Record-Finding "Manifest" "  module_id: $($manifest.module_id)" "PASS" ""
    Record-Finding "Manifest" "  version: $($manifest.version)" "PASS" ""
    Record-Finding "Manifest" "  status: $($manifest.status)" "PASS" ""

    # Validate immutability rules
    if ($manifest.immutability_rules -and $manifest.immutability_rules.Count -gt 0) {
        Record-Finding "Manifest" "  immutability rules: $($manifest.immutability_rules.Count) rules" "PASS" ""
    }

    # Validate components
    if ($manifest.components -and $manifest.components.Count -eq 4) {
        Record-Finding "Manifest" "  components: 4 registered" "PASS" ""
    } else {
        Record-Finding "Manifest" "  components" "PARTIAL" "Expected 4, found $($manifest.components.Count)"
    }
} catch {
    Record-Finding "Manifest" "module.manifest.json" "FAIL" "Invalid JSON: $_"
}
Write-Host ""

# Verify deployment scripts
Write-Host "[5/8] Verifying deployment scripts..."
$deploymentScripts = @(
    "scripts/install.ps1",
    "scripts/verify.ps1",
    "scripts/package.ps1"
)

foreach ($script in $deploymentScripts) {
    $path = Join-Path $ModuleRoot $script
    if (Test-Path $path) {
        $size = (Get-Item $path).Length
        Record-Finding "Deployment" $(Split-Path $path -Leaf) "PASS" "$size bytes"
    } else {
        Record-Finding "Deployment" $(Split-Path $path -Leaf) "PARTIAL" "Not found (optional for verify run)"
    }
}
Write-Host ""

# Verify documentation
Write-Host "[6/8] Verifying documentation..."
$docsPath = Join-Path $ModuleRoot "docs"
if (Test-Path $docsPath) {
    $docFiles = Get-ChildItem $docsPath -File -ErrorAction SilentlyContinue
    if ($docFiles.Count -gt 0) {
        Record-Finding "Documentation" "docs/" "PASS" "$($docFiles.Count) files"
        foreach ($doc in $docFiles) {
            Record-Finding "Documentation" "  $($doc.Name)" "PASS" "$($doc.Length) bytes"
        }
    } else {
        Record-Finding "Documentation" "docs/" "PARTIAL" "Directory exists but is empty"
    }
} else {
    Record-Finding "Documentation" "docs/" "PARTIAL" "Directory not found"
}
Write-Host ""

# Verify evidence files
Write-Host "[7/8] Verifying evidence files..."
$evidencePath = Join-Path $ModuleRoot "evidence"
if (Test-Path $evidencePath) {
    $evidenceFiles = Get-ChildItem $evidencePath -File -ErrorAction SilentlyContinue
    if ($evidenceFiles.Count -gt 0) {
        Record-Finding "Evidence" "evidence/" "PASS" "$($evidenceFiles.Count) files"
        foreach ($file in $evidenceFiles) {
            Record-Finding "Evidence" "  $($file.Name)" "PASS" "$($file.Length) bytes"
        }
    } else {
        Record-Finding "Evidence" "evidence/" "PARTIAL" "Directory exists but is empty"
    }
} else {
    Record-Finding "Evidence" "evidence/" "PARTIAL" "Directory not found"
}
Write-Host ""

# Summary
Write-Host "[8/8] Verification Summary..."
Write-Host ""
Write-Host "========================================"
Write-Host "Results: PASS=$passCount FAIL=$failCount"
Write-Host "========================================"
Write-Host ""

if ($failCount -eq 0) {
    Write-Host "✓ Verification PASS" -ForegroundColor Green
    Write-Host "Bridge module is ready for deployment"
    Write-Host ""

    # Export findings as JSON
    $findingsJson = @{
        verification_timestamp = Get-Date -Format "o"
        module_id = "Mrliou_MRL_RooClaudeCode_BridgeNeuralLink_v1"
        module_root = $ModuleRoot
        pass_count = $passCount
        fail_count = $failCount
        findings = $findings
    }

    $outputPath = Join-Path $ModuleRoot "evidence\verify_result.json"
    $findingsJson | ConvertTo-Json -Depth 10 | Out-File -FilePath $outputPath -Encoding UTF8
    Write-Host "Verification results saved to: evidence/verify_result.json"
    Write-Host ""

    exit 0
} else {
    Write-Host "✗ Verification FAIL - $failCount issues found" -ForegroundColor Red
    Write-Host ""
    exit 1
}
