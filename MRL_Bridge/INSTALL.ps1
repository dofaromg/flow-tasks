# MRL_Bridge v3.1.0 一鍵部署腳本 (Windows / PowerShell)
# origin_signature: MrLiouWord
# 用法: 解壓封包後,在解壓目錄執行: .\INSTALL.ps1

$ErrorActionPreference = "Stop"
$here = Split-Path -Parent $MyInvocation.MyCommand.Path
$nssm = "D:\nssm\nssm-2.24\win64\nssm.exe"
$node = "D:\MrlToolchain\node\node.exe"
$target = "D:\mrl\bridge"

Write-Host "=== MRL_Bridge v3.1.0 部署 ===" -ForegroundColor Cyan
Write-Host "Source: $here\bridge\"
Write-Host "Target: $target"
Write-Host ""

# 1. 檢查 Node
if (!(Test-Path $node)) { Write-Error "Node.js 不在 $node — 請先安裝"; exit 1 }
Write-Host "✓ Node $(& $node --version)"

# 2. 檢查 nssm
if (!(Test-Path $nssm)) { Write-Error "nssm 不在 $nssm — 請先安裝"; exit 1 }
Write-Host "✓ nssm 存在"

# 3. 確認 PG/Redis 服務
$pgState = (Get-Service postgresql* -ErrorAction SilentlyContinue | Select-Object -First 1).Status
$redisState = (Get-Service mrl_redis -ErrorAction SilentlyContinue).Status
Write-Host "✓ PostgreSQL: $pgState"
Write-Host "✓ Redis: $redisState"

# 4. 複製檔案
Write-Host "`n[1/5] 複製檔案到 $target..."
New-Item -ItemType Directory -Force -Path $target | Out-Null
Copy-Item -Path "$here\bridge\*" -Destination $target -Recurse -Force
New-Item -ItemType Directory -Force -Path "$target\logs" | Out-Null
Write-Host "  完成"

# 5. npm install
Write-Host "`n[2/5] npm install..."
Push-Location $target
& "D:\MrlToolchain\node\npm.cmd" install --no-fund --no-audit
Pop-Location
Write-Host "  完成"

# 6. 註冊 nssm service (若不存在)
Write-Host "`n[3/5] 註冊 Windows Service MRL_Bridge..."
$existing = & $nssm get MRL_Bridge Status 2>&1
if ($LASTEXITCODE -ne 0) {
    & $nssm install MRL_Bridge $node "$target\server.js"
    & $nssm set MRL_Bridge AppDirectory $target
    & $nssm set MRL_Bridge Start SERVICE_AUTO_START
    & $nssm set MRL_Bridge AppStdout "$target\logs\nssm_stdout.log"
    & $nssm set MRL_Bridge AppStderr "$target\logs\nssm_stderr.log"
    Write-Host "  服務已註冊"
} else {
    Write-Host "  服務已存在,跳過註冊"
}

# 7. 啟動
Write-Host "`n[4/5] 啟動服務..."
& $nssm start MRL_Bridge
Start-Sleep -Seconds 5

# 8. 健康檢查
Write-Host "`n[5/5] 健康檢查..."
try {
    $h = Invoke-RestMethod -Uri "http://127.0.0.1:7800/health" -TimeoutSec 10
    Write-Host "✓ Service: $($h.service)"
    Write-Host "✓ Version: $($h.version)"
    Write-Host "✓ Origin: $($h.origin_signature)"
    Write-Host "✓ PG: $($h.pg)"
    Write-Host "✓ Redis: $($h.redis)"
    Write-Host "`n=== 部署成功 ===" -ForegroundColor Green
} catch {
    Write-Error "健康檢查失敗: $_"
    Write-Host "查看 logs: $target\logs\nssm_stderr.log"
}
