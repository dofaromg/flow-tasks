#requires -Version 5.1
<#
MRL_Rename_20261014_revert.ps1   origin_signature: MrLiouWord

ROOT 2026-10-14: every name changed by D:\MRL_Mother\MRL_Rename_20261014.log goes back.
The script reads that log on DL580 and reverses it:
  1. REFFIXED files    -> original references (MRL_DL580 -> MRL_CLAUDE_DL580), backup first;
                          done first, while the logged paths are still the current ones
  2. RENAMED paths     -> original names, newest first (a folder before the files inside it)
  3. PGDB databases    -> original database names (needs psql; prompts for the password)
Nothing is deleted or overwritten. A path whose original name is already taken is reported
as CONFLICT and left alone. If any action record in the log cannot be read, nothing is
changed. Every action is written to a receipt beside the log.
Default invocation is evidence-only preflight; exit 3 means restoration is NOT VERIFIED.
Apply is held pending the DL580 log, authoritative per-item names and database configuration
audit. This boundary is intentional: neither the log nor a historical name proves current
canonical authority. The historical restoration implementation below remains for review.
Lineage: 8386e5b safeguards; a459a758 user-requested revert retained in Git history.
Exit 0 is reserved for a future fully verified restoration.
#>
[CmdletBinding()]
param(
    [string]$LogPath = 'D:\MRL_Mother\MRL_Rename_20261014.log',
    [string]$PsqlPath = 'D:\pgsql\bin\psql.exe',
    [string]$PgHost = '127.0.0.1',
    [string]$PgUser = 'postgres',
    [switch]$Apply
)
$ErrorActionPreference = 'Stop'
if (-not (Test-Path -LiteralPath $LogPath)) { throw "Rename log not found: $LogPath" }
$stamp = (Get-Date -Format 'yyyyMMdd_HHmmss_fff') + '_' + [Guid]::NewGuid().ToString('N')
$base = [IO.Path]::GetDirectoryName([IO.Path]::GetFullPath($LogPath))
if ($base -notmatch '^[Dd]:\\') { throw 'Evidence and receipts must remain on DL580 D:.' }
$receipt = [IO.Path]::Combine($base, "MRL_Rename_20261014_revert_$stamp.log")
$backup = [IO.Path]::Combine($base, "MRL_Rename_20261014_revert_$stamp.backup")
$counts = @{}
function Note([string]$kind, [string]$text) {
    $counts[$kind] = 1 + [int]$counts[$kind]
    $line = "$kind`t$text"
    Add-Content -LiteralPath $receipt -Value $line -Encoding UTF8
    Write-Output $line
}

Note 'START' "$((Get-Date).ToString('o')) log=$LogPath origin_signature=MrLiouWord canonical_authority=Mr.liou"
$logHash = (Get-FileHash -LiteralPath $LogPath -Algorithm SHA256).Hash
$logInfo = Get-Item -LiteralPath $LogPath
Note 'LOG_EVIDENCE' "sha256=$logHash bytes=$($logInfo.Length) created_utc=$($logInfo.CreationTimeUtc.ToString('o')) modified_utc=$($logInfo.LastWriteTimeUtc.ToString('o'))"
if ($Apply) {
    Note 'AUTHORITY_HOLD' 'Per-item name direction and PostgreSQL/configuration consistency have not been verified; no restoration was attempted.'
    exit 3
}

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
$unparsed = New-Object System.Collections.ArrayList
$open = $null
$lineNo = 0
$logEncoding = New-Object Text.UTF8Encoding -ArgumentList $false, $true
foreach ($line in ([IO.File]::ReadAllLines($LogPath, $logEncoding))) {
    $lineNo++
    $t = "$line".Trim()
    if (-not $t) { continue }
    # A console copy of the log can wrap a record onto the next line or drop the tab
    # between its two paths; a drive letter only ever starts a path.
    if ($open -eq 'RENAMED' -and $t -cmatch '^[A-Za-z]:\\') { $pairs[$pairs.Count - 1][1] = $t; $open = $null; continue }
    if ($open -eq 'REFFIXED' -and $t -cmatch '^\d+$') { $refFixed[$refFixed.Count - 1][1] = [int]$t; $open = $null; continue }
    if ($open -eq 'SKIP' -and $t -cmatch '^[A-Za-z]:\\') { $open = $null; continue }
    if ($open -eq 'SKIP') { [void]$unparsed.Add("missing SKIP_EXISTS continuation before line $lineNo") }
    $open = $null
    if ($t -cmatch '^RENAMED\s+([A-Za-z]:\\.+?)\s*([A-Za-z]:\\.+)$') { [void]$pairs.Add(@($Matches[1], $Matches[2])) }
    elseif ($t -cmatch '^RENAMED\s+([A-Za-z]:\\.+)$') { [void]$pairs.Add(@($Matches[1], $null)); $open = 'RENAMED' }
    elseif ($t -cmatch '^REFFIXED\s+([A-Za-z]:\\.+?)\s+(\d+)$') { [void]$refFixed.Add(@($Matches[1], [int]$Matches[2])) }
    elseif ($t -cmatch '^REFFIXED\s+([A-Za-z]:\\.+)$') { [void]$refFixed.Add(@($Matches[1], $null)); $open = 'REFFIXED' }
    elseif ($t -cmatch '^PGDB\s+([a-z_][a-z0-9_]*)\s+([a-z_][a-z0-9_]*)\s+ALTER DATABASE$') { [void]$dbPairs.Add(@($Matches[1], $Matches[2])) }
    elseif ($t -cmatch '^SKIP_EXISTS\s+([A-Za-z]:\\.+?)\s*([A-Za-z]:\\.+)$') { }
    elseif ($t -cmatch '^SKIP_EXISTS\s+([A-Za-z]:\\.+)$') { $open = 'SKIP' }
    elseif ($t -cmatch '^(start|REFS_START|REF|done2|PHASE2_START)(?:\s|$)') { }
    else { [void]$unparsed.Add("line $lineNo`t$t") }
}
if ($open -eq 'SKIP') { [void]$unparsed.Add('missing SKIP_EXISTS continuation at end of log') }

# Do not infer a missing target from another folder with the same leaf name.
# A console transcript is insufficient authority for any unresolved mapping.
foreach ($p in $pairs) {
    if (-not $p[1]) { [void]$unparsed.Add("no explicit target`t$($p[0])") }
}
foreach ($r in $refFixed) { if ($null -eq $r[1]) { [void]$unparsed.Add("no count`t$($r[0])") } }
Note 'PARSED' "renamed=$($pairs.Count) reffixed=$($refFixed.Count) databases=$($dbPairs.Count)"
if ($pairs.Count + $refFixed.Count + $dbPairs.Count -eq 0) { [void]$unparsed.Add('no RENAMED, REFFIXED or PGDB record found') }
if ($unparsed.Count) {
    foreach ($u in $unparsed) { Note 'UNPARSED' $u }
    Note 'ABORT' 'nothing changed; the log could not be read completely'
    exit 1
}


# Evidence-only preflight. No Rename-Item, file rewrite, backup mutation or ALTER DATABASE
# is reachable through the current entry point. Candidates are observations, not approval.
foreach ($p in $pairs) {
    $o = $p[0]; $n = $p[1]
    Note 'CANDIDATE_PATH' "logged_original=$o`tlogged_current=$n"
    foreach ($path in @($o, $n)) {
        if (Test-Path -LiteralPath $path) {
            $item = Get-Item -LiteralPath $path -Force
            $h = 'DIRECTORY_NOT_HASHED'
            if (-not $item.PSIsContainer) { $h = (Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash }
            Note 'PATH_EVIDENCE' "$path`tdirectory=$($item.PSIsContainer) sha256=$h created_utc=$($item.CreationTimeUtc.ToString('o')) modified_utc=$($item.LastWriteTimeUtc.ToString('o'))"
        } else { Note 'PATH_MISSING' $path }
    }
    if ($o -eq $n) { Note 'PATH_INVALID' 'source and target are equal' }
    elseif ((Test-Path -LiteralPath $o) -and (Test-Path -LiteralPath $n)) { Note 'CONFLICT' "$n`t$o" }
}
$latin1 = [Text.Encoding]::GetEncoding(28591)
foreach ($r in $refFixed) {
    $file = $r[0]
    try {
        $item = Get-Item -LiteralPath $file -Force
        if ($item.PSIsContainer) { throw 'Reference target is a directory' }
        $bytes = [IO.File]::ReadAllBytes($file)
        $enc = $latin1
        if ($bytes.Length -ge 2 -and $bytes[0] -eq 0xFF -and $bytes[1] -eq 0xFE) { $enc = [Text.Encoding]::Unicode }
        elseif ($bytes.Length -ge 2 -and $bytes[0] -eq 0xFE -and $bytes[1] -eq 0xFF) { $enc = [Text.Encoding]::BigEndianUnicode }
        $text = $enc.GetString($bytes)
        Note 'REF_EVIDENCE' "$file`tsha256=$((Get-FileHash -LiteralPath $file -Algorithm SHA256).Hash) bytes=$($bytes.Length) logged_count=$($r[1]) current_token_count=$([regex]::Matches($text, 'MRL_DL580').Count) historical_token_count=$([regex]::Matches($text, 'MRL_CLAUDE_DL580').Count) created_utc=$($item.CreationTimeUtc.ToString('o')) modified_utc=$($item.LastWriteTimeUtc.ToString('o'))"
        Note 'AUTHORITY_PENDING_REF' "$file`tcounts alone cannot identify which references were originally changed"
    } catch { Note 'REF_FAILED' "$file`t$($_.Exception.Message)" }
}
foreach ($d in $dbPairs) {
    Note 'CANDIDATE_DATABASE' "logged_original=$($d[0]) logged_current=$($d[1])"
}
if ($dbPairs.Count) {
    if (-not (Test-Path -LiteralPath $PsqlPath -PathType Leaf)) { Note 'DB_FAILED' "psql not found: $PsqlPath" }
    else {
        $queries = @()
        foreach ($d in $dbPairs) {
            $o = $d[0]; $n = $d[1]
            $queries += "SELECT CASE WHEN EXISTS (SELECT 1 FROM pg_database WHERE datname='$o') AND EXISTS (SELECT 1 FROM pg_database WHERE datname='$n') THEN 'DB_CONFLICT' WHEN EXISTS (SELECT 1 FROM pg_database WHERE datname='$o') THEN 'DB_ORIGINAL_PRESENT' WHEN EXISTS (SELECT 1 FROM pg_database WHERE datname='$n') THEN 'DB_CURRENT_PRESENT' ELSE 'DB_MISSING' END || ' $o $n';"
            $queries += "SELECT 'DB_CONNECTIONS ' || datname || ' ' || count(*) FROM pg_stat_activity WHERE datname IN ('$o','$n') GROUP BY datname;"
        }
        # -w never prompts; -X ignores psql startup files. Only SELECT statements.
        $prev = $ErrorActionPreference
        try {
            $ErrorActionPreference = 'Continue'
            $out = ($queries -join "`n") | & $PsqlPath -h $PgHost -U $PgUser -d postgres -X -w -q -t -A -v ON_ERROR_STOP=1 2>&1
            $code = $LASTEXITCODE
        } finally { $ErrorActionPreference = $prev }
        foreach ($line in @($out)) { if ("$line".Trim()) { Note 'DB_PREFLIGHT' "$line" } }
        if ($code -ne 0) { Note 'DB_FAILED' "psql exit $code" }
    }
    Note 'DB_CONFIG_AUDIT_PENDING' 'Database catalog observations do not verify application settings, pool bindings, scheduled tasks or service health.'
}
$finalLogHash = (Get-FileHash -LiteralPath $LogPath -Algorithm SHA256).Hash
if ($finalLogHash -ne $logHash) { Note 'LOG_CHANGED' "before=$logHash after=$finalLogHash" }
Note 'PREFLIGHT_ONLY' 'No original asset or database was modified. Authority, directory hashes, reference identity and runtime consistency remain unverified.'
Note 'SUMMARY' ((($counts.GetEnumerator() | Sort-Object Name | ForEach-Object { "$($_.Name)=$($_.Value)" }) -join ' '))
Note 'HOLD' "$((Get-Date).ToString('o')) restoration=NOT_VERIFIED receipt=$receipt"
exit 3

# Historical implementation retained for provenance review, unreachable while authority
# is pending. Re-enable only after the supported preflight has resolved the evidence gaps.

# Byte-level edit keeps each file's encoding (UTF-8, ANSI or UTF-16) exactly as it was.
$latin1 = [Text.Encoding]::GetEncoding(28591)
foreach ($r in $refFixed) {
    $file = $r[0]; $n = $r[1]
    try {
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
    } catch { Note 'REF_FAILED' "$file`t$($_.Exception.Message)" }
}

for ($i = $pairs.Count - 1; $i -ge 0; $i--) {
    $old = $pairs[$i][0]; $new = $pairs[$i][1]
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

if ($dbPairs.Count) {
    if (-not (Test-Path -LiteralPath $PsqlPath)) { Note 'DB_FAILED' "psql not found: $PsqlPath" }
    else {
        $sql = ''
        $names = @()
        foreach ($d in $dbPairs) {
            $o = $d[0]; $n = $d[1]; $names += "'$o'", "'$n'"
            $sql += "SELECT CASE WHEN EXISTS (SELECT 1 FROM pg_database WHERE datname = '$o')" +
                " AND EXISTS (SELECT 1 FROM pg_database WHERE datname = '$n') THEN 'DB_CONFLICT $n $o'" +
                " WHEN EXISTS (SELECT 1 FROM pg_database WHERE datname = '$o') THEN 'DB_ALREADY $o'" +
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
$bad = 'CONFLICT', 'FAILED', 'MISSING', 'SKIP_PARENT_DIFFERS', 'REF_CHECK', 'REF_MISSING', 'REF_FAILED',
    'DB_FAILED', 'DB_MISSING', 'DB_BUSY', 'DB_CONFLICT'
if ($left -or @($bad | Where-Object { $counts[$_] }).Count) { exit 1 }
exit 0
