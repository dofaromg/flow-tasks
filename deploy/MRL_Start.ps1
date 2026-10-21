# MRL_Start.ps1 — DL580(Windows) 一鍵啟動 MRL 統一系統
# origin_signature: MrLiouWord
# 怎麼過去就怎麼回來
#
# 啟動順序：
#   1. 檢查 Docker / Ollama
#   2. 建立資料目錄 (D:\MRL_runtime)
#   3. docker compose -f docker-compose.unified.yml up -d
#   4. 健康檢查
#
# 服務：
#   mrl-engine  :7700  粒子引擎 (7 核心 Workers)
#   mrl-product :3000  付費產品平台
#   mrl-ai      :8787  AI SuperComputer (fusion)
#   mrl-db      :5432  PostgreSQL
#   mrl-redis   :6379  Redis
#   mrl-nginx   :80    統一入口
$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$MrlHome = (Resolve-Path (Join-Path $ScriptDir "..")).Path
$MrlDataRoot = if ($env:MRL_DATA_ROOT) { $env:MRL_DATA_ROOT } else { "D:\MRL_runtime" }

Write-Host "============================================" -ForegroundColor Cyan
Write-Host " MRL Unified System — DL580 Startup" -ForegroundColor Cyan
Write-Host " origin_signature: MrLiouWord" -ForegroundColor DarkGray
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

# ── 1. 前置檢查 ──
Write-Host "[1/4] 前置檢查..." -ForegroundColor Yellow

# Docker
$docker = Get-Command docker -ErrorAction SilentlyContinue
if (-not $docker) {
    throw "Docker 未安裝。請安裝 Docker Desktop for Windows。"
}
$dockerVersion = docker --version 2>&1
Write-Host "  Docker: $dockerVersion" -ForegroundColor Green

# Docker Compose
$composeCheck = docker compose version 2>&1
if ($LASTEXITCODE -ne 0) {
    throw "Docker Compose 不可用。請確認 Docker Desktop 已啟動。"
}
Write-Host "  Compose: $composeCheck" -ForegroundColor Green

# Ollama (可選)
$ollama = Get-Command ollama -ErrorAction SilentlyContinue
if ($ollama) {
    $ollamaStatus = ollama list 2>&1
    Write-Host "  Ollama: 已安裝 (本地 AI 可用)" -ForegroundColor Green
} else {
    Write-Host "  Ollama: 未安裝 (AI 將使用外部 API 或離線模式)" -ForegroundColor DarkYellow
}

# ── 2. 資料目錄 ──
Write-Host ""
Write-Host "[2/4] 建立資料目錄..." -ForegroundColor Yellow

New-Item -ItemType Directory -Force -Path $MrlDataRoot | Out-Null
New-Item -ItemType Directory -Force -Path (Join-Path $MrlDataRoot "pgdata") | Out-Null
New-Item -ItemType Directory -Force -Path (Join-Path $MrlDataRoot "redis") | Out-Null
New-Item -ItemType Directory -Force -Path (Join-Path $MrlDataRoot "product") | Out-Null
Write-Host "  MRL_DATA_ROOT = $MrlDataRoot" -ForegroundColor Green

# ── 3. 啟動 ──
Write-Host ""
Write-Host "[3/4] 啟動 MRL 統一系統..." -ForegroundColor Yellow

Set-Location $MrlHome

# 檢查 .env 是否存在
if (-not (Test-Path ".env")) {
    if (Test-Path ".env.mrl.example") {
        Copy-Item ".env.mrl.example" ".env"
        Write-Host "  已從 .env.mrl.example 建立 .env (請編輯填入 API Keys)" -ForegroundColor DarkYellow
    }
}

docker compose -f docker-compose.unified.yml up -d --build 2>&1 | ForEach-Object {
    Write-Host "  $_" -ForegroundColor DarkGray
}

if ($LASTEXITCODE -ne 0) {
    throw "Docker Compose 啟動失敗。請檢查錯誤訊息。"
}

# ── 4. 健康檢查 ──
Write-Host ""
Write-Host "[4/4] 健康檢查..." -ForegroundColor Yellow

Start-Sleep -Seconds 10

$healthScript = Join-Path $ScriptDir "MRL_HealthCheck.ps1"
if (Test-Path $healthScript) {
    & $healthScript
} else {
    $services = @(
        @{ Name = "Engine";  Port = 7700; Path = "/health" },
        @{ Name = "Product"; Port = 3000; Path = "/health" },
        @{ Name = "AI";      Port = 8787; Path = "/health" },
        @{ Name = "800AI";   Port = 8800; Path = "/health" },
        @{ Name = "Bridge";  Port = 7800; Path = "/health" },
        @{ Name = "Platform";Port = 8790; Path = "/health" },
        @{ Name = "RuntimeOS";Port = 8788; Path = "/api/mrl/health" },
        @{ Name = "Gateway"; Port = 80;   Path = "/health" }
    )
    foreach ($svc in $services) {
        try {
            $url = "http://localhost:$($svc.Port)$($svc.Path)"
            $resp = Invoke-WebRequest -Uri $url -TimeoutSec 5 -UseBasicParsing -ErrorAction Stop
            Write-Host "  $($svc.Name) (:$($svc.Port)): OK" -ForegroundColor Green
        } catch {
            Write-Host "  $($svc.Name) (:$($svc.Port)): 啟動中... (稍後重試)" -ForegroundColor DarkYellow
        }
    }
}

# ── 結果 ──
Write-Host ""
Write-Host "============================================" -ForegroundColor Cyan
Write-Host " MRL 系統已啟動" -ForegroundColor Green
Write-Host ""
Write-Host " 統一入口:   http://localhost" -ForegroundColor White
Write-Host " 粒子引擎:   http://localhost:7700" -ForegroundColor White
Write-Host " 產品平台:   http://localhost:3000" -ForegroundColor White
Write-Host " AI 引擎:    http://localhost:8787" -ForegroundColor White
Write-Host " 800AI:      http://localhost:8800" -ForegroundColor White
Write-Host " Bridge:     http://localhost:7800" -ForegroundColor White
Write-Host " Platform:   http://localhost:8790" -ForegroundColor White
Write-Host " RuntimeOS:  http://localhost:8788" -ForegroundColor White
Write-Host " PostgreSQL:  localhost:5432" -ForegroundColor DarkGray
Write-Host " Redis:       localhost:6379" -ForegroundColor DarkGray
Write-Host ""
Write-Host " 健康檢查: .\deploy\MRL_HealthCheck.ps1" -ForegroundColor DarkGray
Write-Host " 停止: docker compose -f docker-compose.unified.yml down" -ForegroundColor DarkGray
Write-Host " 日誌: docker compose -f docker-compose.unified.yml logs -f" -ForegroundColor DarkGray
Write-Host "============================================" -ForegroundColor Cyan
