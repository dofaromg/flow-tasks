[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)] [string[]]$Files,
    [Parameter(Mandatory = $true)] [string]$Purpose,
    [Parameter(Mandatory = $true)] [string]$HardwareId,
    [Parameter(Mandatory = $true)] [string]$ModelReleaseId,
    [Parameter(Mandatory = $false)] [string]$Output = ".\MRL_return_bundle.zip",
    [Parameter(Mandatory = $false)] [string]$Policy = "..\config\MRL_return_policy.example.json",
    [Parameter(Mandatory = $true)] [switch]$Consent
)

$ErrorActionPreference = "Stop"
$ScriptDirectory = Split-Path -Parent $MyInvocation.MyCommand.Path
$PackageRoot = (Resolve-Path (Join-Path $ScriptDirectory "..")).Path
$ResolvedPolicy = (Resolve-Path (Join-Path $ScriptDirectory $Policy)).Path

Push-Location $PackageRoot
try {
    python -m runtime.MRL_return_bundle_v1 `
        --policy $ResolvedPolicy `
        --output $Output `
        --purpose $Purpose `
        --hardware-id $HardwareId `
        --model-release-id $ModelReleaseId `
        --consent `
        @Files
    if ($LASTEXITCODE -ne 0) { throw "MRL return bundle creation failed" }
}
finally {
    Pop-Location
}
