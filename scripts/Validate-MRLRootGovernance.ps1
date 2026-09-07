[CmdletBinding()]
param(
    [string]$Base,
    [string]$Head,
    [string]$Ref
)

$ErrorActionPreference = "Stop"
$ScriptPath = Join-Path $PSScriptRoot "validate_mrl_governance.py"
$Python = Get-Command python -ErrorAction SilentlyContinue
if (-not $Python) {
    $Python = Get-Command py -ErrorAction SilentlyContinue
}
if (-not $Python) {
    throw "Python runtime not found. Install Python 3 or run the GitHub governance gate."
}

$Arguments = @($ScriptPath)
if ($Base -and $Head) {
    $Arguments += @("--base", $Base, "--head", $Head)
} elseif ($Ref) {
    $Arguments += @("--ref", $Ref)
}
& $Python.Source @Arguments
if ($LASTEXITCODE -ne 0) {
    throw "MRL root governance validation failed with exit code $LASTEXITCODE"
}
