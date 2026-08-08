# MRL_DL580_DeployRunner_v1 — DL580 母體節點啟動入口 (Windows / PowerShell)
# origin_signature=MrLiouWord
# DL580 為 MRL 內部母體自運行節點；GitHub/Cloud Code 為建構器與鏡像；APFS/Batch072 為部署/備份鏈，非母體本體。
$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$MrlHome = if ($env:MRL_HOME) { $env:MRL_HOME } else { (Resolve-Path (Join-Path $ScriptDir "..\..")).Path }
$MrlPort = if ($env:MRL_PORT) { $env:MRL_PORT } else { "8790" }
$OriginSignature = "MrLiouWord"

Set-Location $MrlHome

Write-Host "MRL_DL580_START"
Write-Host "origin_signature=$OriginSignature"
Write-Host "mode=權位區分模式"
Write-Host "node_role=DL580 母體自運行節點"
Write-Host "MRL_HOME=$MrlHome"
Write-Host "MRL_PORT=$MrlPort"

# 1. 部署前檢查（優先 .ps1，否則退回 bash .sh）
$checkPs1 = Join-Path $MrlHome "scripts\MRL_dl580_deploy_check.ps1"
$checkSh = Join-Path $MrlHome "scripts/MRL_dl580_deploy_check.sh"
if (Test-Path $checkPs1) {
  & $checkPs1
} elseif (Get-Command bash -ErrorAction SilentlyContinue) {
  bash $checkSh
} else {
  Write-Host "WARN: no deploy check runner available"
}

# 2. 安裝依賴（冪等）
if (-not (Test-Path (Join-Path $MrlHome "node_modules"))) {
  Write-Host "installing dependencies..."
  npm install
}

# 3. Bootstrap
npm run MRL_boot

# 4. 啟動 Runtime（母體自行運行）
Write-Host "starting MRL Runtime on port $MrlPort..."
node MRL_RuntimeServer.js
