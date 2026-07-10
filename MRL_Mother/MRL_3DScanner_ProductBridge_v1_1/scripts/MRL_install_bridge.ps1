$ErrorActionPreference = "Stop"
$root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$backend = Join-Path $root "backend\MRL_3D_Reconstruction_Server"
$included = Join-Path $root "included"
$log = Join-Path $root "install.log"
"[MRL] install start $(Get-Date -Format o)" | Out-File $log -Encoding utf8
New-Item -ItemType Directory -Force -Path (Join-Path $backend "storage") | Out-Null
Set-Location $backend
npm install | Tee-Object -FilePath $log -Append
$srcZip = Join-Path $included "mrl3d_ai_reconstruction-1.0.0-src.zip"
if (Test-Path $srcZip) {
  python -m pip install $srcZip | Tee-Object -FilePath $log -Append
} else {
  "[MRL] mrl3d source zip not found; runner will fail until mrl3d is installed" | Tee-Object -FilePath $log -Append
}
"INSTALL PASS" | Tee-Object -FilePath $log -Append
