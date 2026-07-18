param(
    [Parameter(Mandatory = $true)]
    [string]$Source,

    [Parameter(Mandatory = $true)]
    [string]$SeedId,

    [string]$Storage = "D:\MRL_Mother\memory",
    [string]$SourceType = "auto",
    [string]$TrustLevel = "medium"
)

$ErrorActionPreference = "Stop"
$ScriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$PythonCandidates = @(
    "D:\MrlToolchain\python\python.exe",
    "python"
)

$Python = $null
foreach ($Candidate in $PythonCandidates) {
    try {
        $Command = Get-Command $Candidate -ErrorAction Stop
        $Python = $Command.Source
        break
    }
    catch {
        continue
    }
}

if (-not $Python) {
    throw "Python runtime not found. Checked D:\MrlToolchain\python\python.exe and PATH."
}

& $Python "$ScriptRoot\src\mother_growth_loop.py" $Source --seed-id $SeedId --storage $Storage --source-type $SourceType --trust-level $TrustLevel

if ($LASTEXITCODE -ne 0) {
    throw "Mother growth loop verification failed with exit code $LASTEXITCODE."
}
