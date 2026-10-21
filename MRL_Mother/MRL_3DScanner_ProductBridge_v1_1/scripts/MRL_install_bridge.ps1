#requires -Version 5.1
[CmdletBinding()]
param([string]$PythonPath='python', [string]$NpmPath='npm.cmd')
$ErrorActionPreference='Stop'
$root=Split-Path $PSScriptRoot -Parent
$backend=Join-Path $root 'backend\MRL_3D_Reconstruction_Server'
$logDir=Join-Path $root '.bridge\logs'; New-Item -ItemType Directory $logDir -Force | Out-Null
$log=Join-Path $logDir ('install_' + (Get-Date -Format 'yyyyMMdd_HHmmss_fff') + '.log')
Push-Location $backend
try {
    & $NpmPath ci --ignore-scripts 2>&1 | Tee-Object $log -Append
    if ($LASTEXITCODE -ne 0) { throw 'npm ci failed' }
    $zip=Join-Path $root 'included\mrl3d_ai_reconstruction-1.0.0-src.zip'
    if (-not (Test-Path $zip)) { throw 'Original MRL package missing; refusing false install PASS' }
    & $PythonPath -m pip install $zip 2>&1 | Tee-Object $log -Append
    if ($LASTEXITCODE -ne 0) { throw 'MRL Python package install failed' }
    'DEPENDENCY_INSTALL_PASS (COLMAP and actual reconstruction acceptance are separate)' | Tee-Object $log -Append
} finally { Pop-Location }
