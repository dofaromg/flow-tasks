#requires -Version 5.1
<#
MRL_Rename_20261014_revert.ps1   origin_signature: MrLiouWord

ROOT 2026-10-14: every name changed by D:\MRL_Mother\MRL_Rename_20261014.log goes back.
The script reads that log on DL580 and reverses it:
  1. RENAMED paths     -> original names, newest first (a folder before the files inside it)
  2. REFFIXED files    -> original references (MRL_DL580 -> MRL_CLAUDE_DL580), backup first
  3. PGDB databases    -> original database names (needs psql; prompts for the password)
Nothing is deleted or overwritten. A path whose original name is already taken is reported
as CONFLICT and left alone. Every action is written to a receipt beside the log.
Exit 0 only when every original name is back.
#>
[CmdletBinding()]
param(
    [string]$LogPath = 'D:\MRL_Mother\MRL_Rename_20261014.log',
    [string]$PsqlPath = 'D:\pgsql\bin\psql.exe',
    [string]$PgHost = '127.0.0.1',
    [string]$PgUser = 'postgres'
)
$ErrorActionPreference = 'Stop'
if (-not (Test-Path -LiteralPath $LogPath)) { throw "Rename log not found: $LogPath" }
$stamp = Get-Date -Format 'yyyyMMdd_HHmmss'
$base = [IO.Path]::GetDirectoryName($LogPath)
$receipt = [IO.Path]::Combine($base, "MRL_Rename_20261014_revert_$stamp.log")
$backup = [IO.Path]::Combine($base, "MRL_Rename_20261014_revert_$stamp.backup")
$counts = @{}
function Note([string]$kind, [string]$text) {
    $counts[$kind] = 1 + [int]$counts[$kind]
    $line = "$kind`t$text"
    Add-Content -LiteralPath $receipt -Value $line -Encoding UTF8
    Write-Output $line
}

Note 'START' "$((Get-Date).ToString('o')) log=$LogPath"

# A rename job still running would race this revert; stop instead of fighting it.
$busy = @(Get-CimInstance Win32_Process | Where-Object {
    $_.ProcessId -ne $PID -and $_.Name -match '^(powershell|pwsh|python|node|cmd)' -and
    $_.CommandLine -and $_.CommandLine -match 'MRL_Rename' -and $_.CommandLine -notmatch '_revert'
})
if ($busy.Count) {
    foreach ($p in $busy) { Note 'ABORT_RENAME_JOB_RUNNING' "$($p.ProcessId) $($p.CommandLine)" }
    exit 2
}

$pairs = New-Object System.Collections.ArrayList
$refFixed = New-Object System.Collections.ArrayList
$dbPairs = New-Object System.Collections.ArrayList
foreach ($line in (Get-Content -LiteralPath $LogPath)) {
    if ($line -match '^RENAMED\s+([A-Za-z]:\\.+?)\s+([A-Za-z]:\\.+?)\s*$') { [void]$pairs.Add(@($Matches[1], $Matches[2])) }
    elseif ($line -match '^RENAMED\s+([A-Za-z]:\\.+?)\s*$') { [void]$pairs.Add(@($Matches[1], $null)) }
    elseif ($line -match '^REFFIXED\s+([A-Za-z]:\\.+?)\s+(\d+)\s*$') { [void]$refFixed.Add(@($Matches[1], [int]$Matches[2])) }
    elseif ($line -match '^PGDB\s+([a-z_][a-z0-9_]*)\s+([a-z_][a-z0-9_]*)\s+ALTER DATABASE\s*$') { [void]$dbPairs.Add(@($Matches[1], $Matches[2])) }
}
Note 'PARSED' "renamed=$($pairs.Count) reffixed=$($refFixed.Count) databases=$($dbPairs.Count)"

# A RENAMED line without a target takes the target this log gives the same name elsewhere.
$leafMap = @{}
foreach ($p in $pairs) { if ($p[1]) { $leafMap[[IO.Path]::GetFileName($p[0])] = [IO.Path]::GetFileName($p[1]) } }

for ($i = $pairs.Count - 1; $i -ge 0; $i--) {
    $old = $pairs[$i][0]; $new = $pairs[$i][1]
    if (-not $new) {
        $leaf = [IO.Path]::GetFileName($old)
        if (-not $leafMap.ContainsKey($leaf)) { Note 'UNRESOLVED' $old; continue }
        $new = [IO.Path]::Combine([IO.Path]::GetDirectoryName($old), $leafMap[$leaf])
        Note 'INFERRED' "$old`t$new"
    }
    if ([IO.Path]::GetDirectoryName($old) -ne [IO.Path]::GetDirectoryName($new)) { Note 'SKIP_PARENT_DIFFERS' "$new`t$old"; continue }
    $hasOld = Test-Path -LiteralPath $old
    $hasNew = Test-Path -LiteralPath $new
    if ($hasOld -and -not $hasNew) { Note 'ALREADY' $old; continue }
    if ($hasOld -and $hasNew) { Note 'CONFLICT' "$new`t$old"; continue }
    if (-not $hasNew) { Note 'MISSING' $new; continue }
    try {
        Rename-Item -LiteralPath $new -NewName ([IO.Path]::GetFileName($old)) -Force
        Note 'RESTORED' "$new`t$old"
    } catch { Note 'FAILED' "$new`t$($_.Exception.Message)" }
}

# Byte-level edit keeps each file's encoding (UTF-8, ANSI or UTF-16) exactly as it was.
$latin1 = [Text.Encoding]::GetEncoding(28591)
foreach ($r in $refFixed) {
    $file = $r[0]; $n = $r[1]
    if (-not (Test-Path -LiteralPath $file)) { Note 'REF_MISSING' $file; continue }
    $bytes = [IO.File]::ReadAllBytes($file)
    $enc = $latin1
    if ($bytes.Length -ge 2 -and $bytes[0] -eq 0xFF -and $bytes[1] -eq 0xFE) { $enc = [Text.Encoding]::Unicode }
    $text = $enc.GetString($bytes)
    $found = [regex]::Matches($text, 'MRL_DL580').Count
    if ($found -eq 0 -and [regex]::Matches($text, 'MRL_CLAUDE_DL580').Count -ge $n) { Note 'REF_ALREADY' $file; continue }
    if ($found -ne $n) { Note 'REF_CHECK' "$file`tfound=$found expected=$n left unchanged"; continue }
    $save = [IO.Path]::Combine($backup, ($file -replace ':', ''))
    [void][IO.Directory]::CreateDirectory([IO.Path]::GetDirectoryName($save))
    [IO.File]::Copy($file, $save, $false)
    [IO.File]::WriteAllBytes($file, $enc.GetBytes($text.Replace('MRL_DL580', 'MRL_CLAUDE_DL580')))
    Note 'REF_RESTORED' "$file`t$n backup=$save"
}

if ($dbPairs.Count) {
    if (-not (Test-Path -LiteralPath $PsqlPath)) { Note 'DB_FAILED' "psql not found: $PsqlPath" }
    else {
        $sql = ''
        $names = @()
        foreach ($d in $dbPairs) {
            $o = $d[0]; $n = $d[1]; $names += "'$o'", "'$n'"
            $sql += "SELECT CASE WHEN EXISTS (SELECT 1 FROM pg_database WHERE datname = '$o') THEN 'DB_ALREADY $o'" +
                " WHEN NOT EXISTS (SELECT 1 FROM pg_database WHERE datname = '$n') THEN 'DB_MISSING $n'" +
                " WHEN EXISTS (SELECT 1 FROM pg_stat_activity WHERE datname = '$n') THEN 'DB_BUSY $n'" +
                " ELSE 'DB_RENAMING $n -> $o' END;`n"
            $sql += "SELECT format('ALTER DATABASE %I RENAME TO %I', '$n', '$o')" +
                " WHERE EXISTS (SELECT 1 FROM pg_database WHERE datname = '$n')" +
                " AND NOT EXISTS (SELECT 1 FROM pg_database WHERE datname = '$o')" +
                " AND NOT EXISTS (SELECT 1 FROM pg_stat_activity WHERE datname = '$n') \gexec`n"
        }
        $sql += "SELECT 'DB_NOW ' || coalesce(string_agg(datname, ',' ORDER BY datname), '') FROM pg_database WHERE datname IN ($($names -join ','));`n"
        # psql prompts for the password on the console when no pgpass/PGPASSWORD is set.
        $prev = $ErrorActionPreference; $ErrorActionPreference = 'Continue'
        $out = $sql | & $PsqlPath -h $PgHost -U $PgUser -d postgres -X -q -t -A -v ON_ERROR_STOP=1 2>&1
        $code = $LASTEXITCODE
        $ErrorActionPreference = $prev
        foreach ($l in @($out)) {
            $t = "$l".Trim()
            if (-not $t) { continue }
            $parts = $t -split ' ', 2
            if ($parts[0] -like 'DB_*') { Note $parts[0] $(if ($parts.Count -gt 1) { $parts[1] } else { '' }) } else { Note 'DB_OUTPUT' $t }
        }
        if ($code -ne 0) { Note 'DB_FAILED' "psql exit $code" }
    }
}

# Read-only facts for the entry check, saved with the receipt.
try { foreach ($c in Get-NetConnectionProfile) { Note 'INFO_NET_PROFILE' "$($c.InterfaceAlias) $($c.NetworkCategory)" } } catch { Note 'INFO_NET_PROFILE' $_.Exception.Message }
try { foreach ($c in @(Get-NetTCPConnection -LocalPort 3389 -State Established -ErrorAction SilentlyContinue)) { Note 'INFO_RDP_FROM' "$($c.RemoteAddress)" } } catch { Note 'INFO_RDP_FROM' $_.Exception.Message }

$left = 0
foreach ($p in $pairs) { if (-not (Test-Path -LiteralPath $p[0])) { $left++; Note 'NOT_BACK' $p[0] } }
Note 'SUMMARY' ((($counts.GetEnumerator() | Sort-Object Name | ForEach-Object { "$($_.Name)=$($_.Value)" }) -join ' '))
Note 'DONE' "$((Get-Date).ToString('o')) original_names_missing=$left receipt=$receipt"
$bad = 'CONFLICT', 'FAILED', 'MISSING', 'UNRESOLVED', 'SKIP_PARENT_DIFFERS', 'REF_CHECK', 'REF_MISSING', 'DB_FAILED', 'DB_MISSING', 'DB_BUSY'
if ($left -or @($bad | Where-Object { $counts[$_] }).Count) { exit 1 }
exit 0
