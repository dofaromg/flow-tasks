# MRL_HealthCheck.ps1 — DL580 統一健康檢查
# origin_signature: MrLiouWord
# 怎麼過去就怎麼回來
#
# 讀取 config/MRL_ENTRY_INDEX.json，逐一檢查所有服務健康狀態
# Usage: .\deploy\MRL_HealthCheck.ps1

$ErrorActionPreference = "Continue"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$MrlHome = (Resolve-Path (Join-Path $ScriptDir "..")).Path
$IndexPath = Join-Path $MrlHome "config\MRL_ENTRY_INDEX.json"

if (-not (Test-Path $IndexPath)) {
    Write-Host "ERROR: MRL_ENTRY_INDEX.json not found at $IndexPath" -ForegroundColor Red
    exit 1
}

$index = Get-Content $IndexPath -Raw | ConvertFrom-Json

Write-Host "============================================" -ForegroundColor Cyan
Write-Host " MRL System Health Check" -ForegroundColor Cyan
Write-Host " origin_signature: $($index.origin_signature)" -ForegroundColor DarkGray
Write-Host " snapshot: $($index.snapshot_date)" -ForegroundColor DarkGray
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

$total = 0
$healthy = 0
$unhealthy = 0
$skipped = 0

foreach ($svc in $index.services) {
    $total++
    $name = $svc.service_name
    $port = $svc.port
    $endpoint = $svc.health_endpoint

    if (-not $port) {
        Write-Host "  SKIP  $name (no port)" -ForegroundColor DarkGray
        $skipped++
        continue
    }

    if (-not $endpoint) {
        $endpoint = "/"
    }

    $url = "http://127.0.0.1:$port$endpoint"

    try {
        $resp = Invoke-WebRequest -Uri $url -TimeoutSec 3 -UseBasicParsing -ErrorAction Stop
        $code = $resp.StatusCode

        if ($code -eq 200) {
            Write-Host "  OK    $name (:$port) $endpoint" -ForegroundColor Green
            $healthy++
        } else {
            Write-Host "  WARN  $name (:$port) $endpoint -> HTTP $code" -ForegroundColor Yellow
            $unhealthy++
        }
    } catch {
        $errMsg = $_.Exception.Message
        if ($errMsg -match "404") {
            Write-Host "  404   $name (:$port) $endpoint (service alive, endpoint missing)" -ForegroundColor DarkYellow
            $healthy++
        } elseif ($errMsg -match "連線") {
            Write-Host "  DOWN  $name (:$port) connection refused" -ForegroundColor Red
            $unhealthy++
        } else {
            Write-Host "  FAIL  $name (:$port) $errMsg" -ForegroundColor Red
            $unhealthy++
        }
    }
}

Write-Host ""
Write-Host "============================================" -ForegroundColor Cyan
Write-Host " Results: $healthy OK / $unhealthy FAIL / $skipped SKIP (of $total)" -ForegroundColor White

if ($unhealthy -eq 0) {
    Write-Host " Status: ALL SERVICES HEALTHY" -ForegroundColor Green
} else {
    Write-Host " Status: $unhealthy SERVICE(S) NEED ATTENTION" -ForegroundColor Yellow
}

Write-Host "============================================" -ForegroundColor Cyan

# ── Windows Services check ──
Write-Host ""
Write-Host " Windows Services (NSSM):" -ForegroundColor Cyan
$mrlServices = Get-Service | Where-Object { $_.Name -match "MRL|mrl" } | Sort-Object Name

foreach ($s in $mrlServices) {
    $color = switch ($s.Status) {
        "Running" { "Green" }
        "Paused"  { "Yellow" }
        default   { "Red" }
    }
    Write-Host "  $($s.Status.ToString().PadRight(8)) $($s.Name)" -ForegroundColor $color
}

$running = ($mrlServices | Where-Object { $_.Status -eq "Running" }).Count
$paused = ($mrlServices | Where-Object { $_.Status -eq "Paused" }).Count
$stopped = ($mrlServices | Where-Object { $_.Status -eq "Stopped" }).Count

Write-Host ""
Write-Host " Services: $running Running / $paused Paused / $stopped Stopped" -ForegroundColor White
Write-Host "============================================" -ForegroundColor Cyan
