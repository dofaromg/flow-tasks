# START_MRL.ps1 — MRL 企業級執行平台 一鍵啟動 (Windows)
# origin_signature=MrLiouWord ; 零依賴 (Node >=18)
$ErrorActionPreference = "Stop"
Set-Location (Split-Path -Parent $MyInvocation.MyCommand.Path)
if (-not $env:MRL_PORT) { $env:MRL_PORT = "8788" }
$py = Get-Command node -ErrorAction SilentlyContinue
if (-not $py) { throw "需要 Node.js >=18。請先安裝 Node。" }
Write-Host "MRL Enterprise Runtime starting on http://localhost:$($env:MRL_PORT) (origin_signature=MrLiouWord)"
Write-Host "驗證: curl.exe http://localhost:$($env:MRL_PORT)/health"
node MRL_API/MRL_RuntimeServer.js
