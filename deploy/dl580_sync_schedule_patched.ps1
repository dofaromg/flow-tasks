# ============================================================
# MRL_structural_memory — DL580 定期更新排程（patched）
# 用法: 放到 Task Scheduler 每日或每小時跑
# 需求: 先在系統或工作排程帳號下設定環境變數 CF_API_TOKEN_MRL
# ============================================================

$ErrorActionPreference = 'Stop'

$ACCT   = "0b36a4577da7fced6df2e062fa5f6fa2"
$DB     = "7980baaf-48d3-43cc-8be7-dd8c9590f3d1"
$TOKEN  = $env:CF_API_TOKEN_MRL
if ([string]::IsNullOrWhiteSpace($TOKEN)) {
    throw "Missing environment variable: CF_API_TOKEN_MRL"
}

$D1URL  = "https://api.cloudflare.com/client/v4/accounts/$ACCT/d1/database/$DB/query"
$HDR    = @{ "Authorization" = "Bearer $TOKEN" }
$ROOT   = "D:\MRL_Mother"
$LOG    = "D:\MRL_Mother\sync_log.txt"
$ERRLOG = "D:\MRL_Mother\sync_error_log.txt"
$NOW    = Get-Date -Format "yyyy-MM-ddTHH:mm:ss"

$stats = [ordered]@{
    attempted = 0
    ok = 0
    fail = 0
    dirs = 0
    files = 0
    proc_snapshots = 0
    port_snapshots = 0
    trace_rows = 0
}
$errors = New-Object System.Collections.Generic.List[string]

function Escape-Sql([string]$value) {
    if ($null -eq $value) { return "" }
    return ($value -replace "'", "''")
}

function Write-LocalLog([string]$message) {
    Add-Content -Path $LOG -Value $message
}

function Write-LocalError([string]$message) {
    Add-Content -Path $ERRLOG -Value $message
}

function Send-D1([string]$sql, [string]$label) {
    $script:stats.attempted++
    $bodyObj = @{ sql = $sql }
    $bodyBytes = [System.Text.Encoding]::UTF8.GetBytes(($bodyObj | ConvertTo-Json -Compress -Depth 10))

    try {
        $resp = Invoke-RestMethod -Uri $D1URL -Method POST -Headers $HDR -Body $bodyBytes -ContentType "application/json; charset=utf-8"
        if ($resp.success -eq $true) {
            $script:stats.ok++
            return $true
        }

        $script:stats.fail++
        $err = "$label : D1 returned success=false : " + (($resp.errors | ConvertTo-Json -Compress -Depth 10) 2>$null)
        $script:errors.Add($err)
        Write-LocalError "[$NOW] $err"
        return $false
    }
    catch {
        $script:stats.fail++
        $err = "$label : EXCEPTION : $($_.Exception.Message)"
        $script:errors.Add($err)
        Write-LocalError "[$NOW] $err"
        return $false
    }
}

Write-Host "=== MRL_structural_memory Sync @ $NOW ===" -ForegroundColor Cyan

# ── 1. 頂層目錄快照（真正 upsert） ──
$topDirs = Get-ChildItem -Path $ROOT -Directory -ErrorAction SilentlyContinue
foreach ($dir in $topDirs) {
    $childCount = (Get-ChildItem -Path $dir.FullName -Recurse -File -ErrorAction SilentlyContinue | Measure-Object).Count
    $totalSize  = (Get-ChildItem -Path $dir.FullName -Recurse -File -ErrorAction SilentlyContinue | Measure-Object -Property Length -Sum).Sum
    $sizeMB     = [math]::Round((($totalSize | ForEach-Object { $_ }) / 1MB), 2)
    $memId      = "mem-arch-$($dir.Name.ToLower() -replace '[^a-z0-9_-]','-')"
    $memKey     = Escape-Sql ("architecture:" + $dir.Name)
    $srcLoc     = Escape-Sql $dir.FullName
    $memValue   = Escape-Sql ((@{
        dir_name      = $dir.Name
        path          = $dir.FullName
        file_count    = $childCount
        total_size_mb = $sizeMB
        created       = $dir.CreationTime.ToString("yyyy-MM-ddTHH:mm:ss")
        modified      = $dir.LastWriteTime.ToString("yyyy-MM-ddTHH:mm:ss")
        synced_at     = $NOW
    } | ConvertTo-Json -Compress -Depth 10))

    $sql = @"
INSERT INTO MRL_structural_memory
(memory_id, memory_type, vault_layer, memory_key, memory_value, source_location, source_type, sphere_sector, status, origin_signature)
VALUES
('$memId', 'architecture_snapshot', 'L1', '$memKey', '$memValue', '$srcLoc', 'dl580_file', 'mother', 'active', 'MrLiouWord')
ON CONFLICT(memory_id) DO UPDATE SET
  memory_value=excluded.memory_value,
  source_location=excluded.source_location,
  status=excluded.status,
  updated_at=strftime('%s','now')
"@

    if (Send-D1 $sql "dir:$($dir.Name)") { $script:stats.dirs++ }
}

# ── 2. 關鍵檔案快照 ──
$keyFiles = Get-ChildItem -Path $ROOT -Recurse -Depth 2 -File -Include "*.py","*.js","*.json","*.zip","*.sql","*.toml","*.yaml","*.md" -ErrorAction SilentlyContinue
foreach ($f in $keyFiles) {
    $relPath  = $f.FullName.Replace($ROOT, "").TrimStart("\")
    $safeName = ($relPath -replace '[^a-zA-Z0-9_.-]','-').ToLower()
    if ($safeName.Length -gt 60) { $safeName = $safeName.Substring(0, 60) }
    $memId    = "mem-file-$safeName"
    $memKey   = Escape-Sql ("file_index:" + $relPath)
    $srcLoc   = Escape-Sql $f.FullName
    $memValue = Escape-Sql ((@{
        file_name     = $f.Name
        relative_path = $relPath
        full_path     = $f.FullName
        extension     = $f.Extension
        size_bytes    = $f.Length
        modified      = $f.LastWriteTime.ToString("yyyy-MM-ddTHH:mm:ss")
        synced_at     = $NOW
    } | ConvertTo-Json -Compress -Depth 10))

    $sql = @"
INSERT INTO MRL_structural_memory
(memory_id, memory_type, vault_layer, memory_key, memory_value, source_location, source_type, sphere_sector, status, origin_signature)
VALUES
('$memId', 'deployment_state', 'L2', '$memKey', '$memValue', '$srcLoc', 'dl580_file', 'mother', 'active', 'MrLiouWord')
ON CONFLICT(memory_id) DO UPDATE SET
  memory_value=excluded.memory_value,
  source_location=excluded.source_location,
  status=excluded.status,
  updated_at=strftime('%s','now')
"@

    if (Send-D1 $sql "file:$relPath") { $script:stats.files++ }
}

# ── 3. 健康檢查快照 ──
$procs = @("node","python","python3","uvicorn","gunicorn","pm2") |
    ForEach-Object { Get-Process -Name $_ -ErrorAction SilentlyContinue } |
    Where-Object { $_ -ne $null }
$procInfo = if ($procs) {
    ($procs | ForEach-Object { $_.ProcessName + ":" + $_.Id + ":" + [math]::Round($_.WorkingSet64/1MB,1) + "MB" }) -join ","
} else {
    "none"
}
$procInfoEsc = Escape-Sql $procInfo
$sqlProc = @"
INSERT INTO MRL_structural_memory
(memory_id, memory_type, vault_layer, memory_key, memory_value, source_location, source_type, sphere_sector, status, origin_signature)
VALUES
('mem-proc-snapshot', 'health_checkpoint', 'L1', 'process:running_snapshot', '$procInfoEsc', 'dl580:tasklist', 'dl580_process', 'mother', 'active', 'MrLiouWord')
ON CONFLICT(memory_id) DO UPDATE SET
  memory_value=excluded.memory_value,
  updated_at=strftime('%s','now')
"@
if (Send-D1 $sqlProc "process_snapshot") { $script:stats.proc_snapshots++ }

$ports = @(3000, 3004, 8787, 8788)
$portInfo = ($ports | ForEach-Object {
    $p = $_
    $c = Get-NetTCPConnection -LocalPort $p -State Listen -ErrorAction SilentlyContinue
    "$p=" + $(if($c){"listening"}else{"closed"})
}) -join ","
$portInfoEsc = Escape-Sql $portInfo
$sqlPort = @"
INSERT INTO MRL_structural_memory
(memory_id, memory_type, vault_layer, memory_key, memory_value, source_location, source_type, sphere_sector, status, origin_signature)
VALUES
('mem-port-snapshot', 'health_checkpoint', 'L1', 'network:port_status', '$portInfoEsc', 'dl580:netstat', 'dl580_process', 'mother', 'active', 'MrLiouWord')
ON CONFLICT(memory_id) DO UPDATE SET
  memory_value=excluded.memory_value,
  updated_at=strftime('%s','now')
"@
if (Send-D1 $sqlPort "port_status") { $script:stats.port_snapshots++ }

# ── 4. 寫 trace_log ──
$traceId = "trace-sync-" + (Get-Date -Format "yyyyMMdd-HHmmss")
$traceMeta = Escape-Sql ((@{
    attempted      = $stats.attempted
    ok             = $stats.ok
    fail           = $stats.fail
    dirs_ok        = $stats.dirs
    files_ok       = $stats.files
    proc_ok        = $stats.proc_snapshots
    port_ok        = $stats.port_snapshots
    source_root    = $ROOT
    top_dirs_seen  = $topDirs.Count
    key_files_seen = $keyFiles.Count
    timestamp      = $NOW
} | ConvertTo-Json -Compress -Depth 10))

$sqlTrace = @"
INSERT OR IGNORE INTO MRL_trace_log
(trace_id, operation, entity_id, entity_type, actor, delta_summary, batch_id, origin_signature)
VALUES
('$traceId', 'structural_memory_sync', 'DL580', 'server', 'DL580-scheduler', '$traceMeta', 'scheduled-sync', 'MrLiouWord')
"@
if (Send-D1 $sqlTrace "trace") { $script:stats.trace_rows++ }

# ── 結果 ──
$result = "[$NOW] Sync complete: attempted=$($stats.attempted) ok=$($stats.ok) fail=$($stats.fail) dirs_ok=$($stats.dirs) files_ok=$($stats.files) proc_ok=$($stats.proc_snapshots) port_ok=$($stats.port_snapshots) trace_ok=$($stats.trace_rows)"
Write-Host ""
Write-Host "=== RESULT ===" -ForegroundColor Cyan
Write-Host $result -ForegroundColor $(if($stats.fail -gt 0){"Yellow"}else{"Green"})
Write-LocalLog $result

if ($errors.Count -gt 0) {
    Write-Host "Errors:" -ForegroundColor Red
    $errors | Select-Object -First 10 | ForEach-Object { Write-Host "  $_" -ForegroundColor Red }
}
