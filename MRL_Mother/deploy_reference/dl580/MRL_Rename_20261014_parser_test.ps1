#requires -Version 5.1
# origin_signature: MrLiouWord
# Synthetic parser regressions only. No DL580 credentials, data, or network.
param([string]$SourcePath = (Join-Path $PSScriptRoot 'MRL_Rename_20261014_revert.ps1'))
$ErrorActionPreference = 'Stop'
$source = [IO.File]::ReadAllText($SourcePath).Replace([Environment]::NewLine, [string][char]10)
$tokens = $null; $errors = $null
$null = [Management.Automation.Language.Parser]::ParseInput($source, [ref]$tokens, [ref]$errors)
if ($errors.Count) { throw ($errors | Out-String) }
$start = $source.IndexOf('$pairs = New-Object')
$finish = $source.IndexOf("Note 'PARSED'", $start)
if ($start -lt 0 -or $finish -le $start) { throw 'Production parser boundaries not found' }
$parseBlock = [scriptblock]::Create($source.Substring($start, $finish - $start))
$root = Join-Path ([IO.Path]::GetTempPath()) ('MRL_Rename_Synthetic_' + [Guid]::NewGuid().ToString('N'))
$null = New-Item -ItemType Directory -Path $root
$passed = 0
function Check([string]$Name, [string[]]$Lines, [bool]$Reject, [int]$Paths = 1, [int]$References = 0, [int]$Databases = 0) {
    $LogPath = Join-Path $root ($Name + '.log')
    [IO.File]::WriteAllLines($LogPath, $Lines, (New-Object Text.UTF8Encoding -ArgumentList $false, $true))
    $before = (Get-FileHash -LiteralPath $LogPath -Algorithm SHA256).Hash
    . $parseBlock
    if ([bool]$unparsed.Count -ne $Reject) { throw "$Name reject=$($unparsed.Count) expected=$Reject" }
    if (-not $Reject -and ($pairs.Count -ne $Paths -or $refFixed.Count -ne $References -or $dbPairs.Count -ne $Databases)) { throw "$Name action count mismatch" }
    if ((Get-FileHash -LiteralPath $LogPath -Algorithm SHA256).Hash -ne $before) { throw "$Name modified input" }
    if (-not $Reject -and $Paths -gt 0 -and $pairs[0][0] -ne 'D:\Synthetic Old\Original') { throw "$Name original name changed" }
    $script:passed++
    Write-Output "PASS $Name"
}
$valid = 'RENAMED D:\Synthetic Old\Original' + [char]9 + 'D:\Synthetic Old\Current'
try {
    Check 'valid' @($valid) $false
    Check 'producer_info' @('start 2026-10-14','REFS_START','REF example','done2','PHASE2_START 2',$valid) $false
    Check 'unknown' @($valid,'UNEXPECTED record') $true
    Check 'prefixed_action' @($valid,'timestamp RENAMED D:\a D:\b') $true
    Check 'lowercase_action' @($valid,'renamed D:\a D:\b') $true
    Check 'lowercase_info' @($valid,'refs_start') $true
    Check 'unknown_suffix' @($valid,'REFS_START_BROKEN') $true
    Check 'wrapped_path' @('RENAMED D:\Synthetic Old\Original','D:\Synthetic Old\Current') $false
    Check 'missing_target' @($valid,'RENAMED D:\no_target') $true
    Check 'wrapped_reference' @($valid,'REFFIXED D:\Synthetic\config.json','2') $false 1 1
    Check 'missing_reference_count' @($valid,'REFFIXED D:\Synthetic\config.json') $true
    Check 'skip_pair' @($valid,'SKIP_EXISTS D:\old D:\current') $false
    Check 'skip_wrapped' @($valid,'SKIP_EXISTS D:\old','D:\current') $false
    Check 'skip_incomplete_eof' @($valid,'SKIP_EXISTS D:\old') $true
    Check 'skip_incomplete_followed' @('SKIP_EXISTS D:\old',$valid) $true
    Check 'skip_malformed' @($valid,'SKIP_EXISTS garbage') $true
    Check 'database' @($valid,'PGDB mrl_claude_reverse mrl_reverse ALTER DATABASE') $false 1 0 1
    $hold = "exit 3" + [char]10 + [char]10 + "# Historical"
    if ($source.IndexOf('if ($Apply)') -ge $start -or $source.IndexOf($hold) -lt 0) { throw 'Restoration hold missing' }
    Write-Output "PASS PowerShell syntax and restoration hold"
    Write-Output "PARSER_SYNTHETIC_PASS cases=$passed runtime=NOT_DL580"
} finally { Remove-Item -LiteralPath $root -Recurse -Force }
