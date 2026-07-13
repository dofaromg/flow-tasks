# MRL_FlowContainer_Start.ps1 — DL580 FlowContainer 原生啟動
# origin_signature: MrLiouWord
# 怎麼過去就怎麼回來
#
# FlowContainer 用 MRL 自有運行時取代 Docker
# 每個服務以原生子進程啟動，Merkle 鏈追蹤所有事件
$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$MrlHome = (Resolve-Path (Join-Path $ScriptDir "..")).Path

Write-Host "============================================" -ForegroundColor Cyan
Write-Host " FlowContainer — MRL Native Runtime" -ForegroundColor Cyan
Write-Host " origin_signature: MrLiouWord" -ForegroundColor DarkGray
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

# Check Python
$py = Get-Command python -ErrorAction SilentlyContinue
if (-not $py) {
    throw "Python not found. Ensure D:\MrlToolchain\python.exe is in PATH."
}
Write-Host "  Python: $(python --version 2>&1)" -ForegroundColor Green

# Check Node
$nd = Get-Command node -ErrorAction SilentlyContinue
if (-not $nd) {
    throw "Node.js not found. Ensure D:\MrlToolchain\node.exe is in PATH."
}
Write-Host "  Node: $(node --version 2>&1)" -ForegroundColor Green

Write-Host ""

Set-Location $MrlHome

python MRL_Mother\04_runtime\flowcontainer.py start `
  --config config\flowcontainer.json `
  --base-dir $MrlHome
