param(
    [string]$Source,

    [Parameter(Mandatory = $true)]
    [string]$SeedId,

    [string]$Storage = "D:\MRL_Mother\memory",
    [string]$SourceType = "auto",
    [string]$TrustLevel = "medium",

    [ValidateSet("Absorb", "Verify", "Rollback")]
    [string]$Action = "Absorb",

    [int]$TargetVersion,

    [string]$EvidenceDirectory = "D:\MRL_Mother\evidence"
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

$Arguments = @(
    "$ScriptRoot\src\mother_growth_loop.py",
    "--seed-id", $SeedId,
    "--storage", $Storage
)

switch ($Action) {
    "Absorb" {
        if ([string]::IsNullOrWhiteSpace($Source)) {
            throw "-Source is required when -Action Absorb is selected."
        }
        $Arguments += @($Source, "--source-type", $SourceType, "--trust-level", $TrustLevel)
    }
    "Verify" {
        $Arguments += "--verify-only"
    }
    "Rollback" {
        if ($TargetVersion -lt 1) {
            throw "-TargetVersion must be a positive integer when -Action Rollback is selected."
        }
        $Arguments += @("--rollback-version", $TargetVersion)
    }
}

$StartedAt = [DateTime]::UtcNow
$Output = & $Python @Arguments 2>&1
$ExitCode = $LASTEXITCODE
$Output | ForEach-Object { Write-Host $_ }

New-Item -ItemType Directory -Force -Path $EvidenceDirectory | Out-Null
$Evidence = [ordered]@{
    schema_version = "mrliou.mother-growth.dl580-evidence.v1"
    origin_signature = "MrLiouWord"
    hostname = $env:COMPUTERNAME
    action = $Action
    seed_id = $SeedId
    storage = $Storage
    source = if ($Action -eq "Absorb") { $Source } else { $null }
    target_version = if ($Action -eq "Rollback") { $TargetVersion } else { $null }
    python = $Python
    started_at_utc = $StartedAt.ToString("o")
    completed_at_utc = [DateTime]::UtcNow.ToString("o")
    exit_code = $ExitCode
    output = ($Output -join [Environment]::NewLine)
}
$SafeSeedId = ($SeedId -replace '[^A-Za-z0-9._-]', '_').Trim('.', '_')
if ([string]::IsNullOrWhiteSpace($SafeSeedId)) { $SafeSeedId = "seed" }
$EvidenceName = "mother_growth_{0}_{1}_{2}.json" -f $Action.ToLowerInvariant(), $SafeSeedId, ([DateTime]::UtcNow.ToString("yyyyMMddTHHmmssfffZ"))
$EvidencePath = Join-Path $EvidenceDirectory $EvidenceName
$Evidence | ConvertTo-Json -Depth 20 | Set-Content -LiteralPath $EvidencePath -Encoding UTF8
Write-Host "Evidence: $EvidencePath"

if ($ExitCode -ne 0) {
    throw "Mother growth loop $Action failed with exit code $ExitCode. Evidence: $EvidencePath"
}
