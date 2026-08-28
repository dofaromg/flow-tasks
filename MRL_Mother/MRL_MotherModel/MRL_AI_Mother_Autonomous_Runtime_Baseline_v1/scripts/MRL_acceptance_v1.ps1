[CmdletBinding()]
param(
    [Parameter(Mandatory = $false)]
    [string]$GatewayUrl = "http://127.0.0.1:7811"
)

$ErrorActionPreference = "Stop"
$ScriptDirectory = Split-Path -Parent $MyInvocation.MyCommand.Path
$PackageRoot = (Resolve-Path (Join-Path $ScriptDirectory "..")).Path
$GatewayUri = [Uri]$GatewayUrl
$LoopbackHosts = @("127.0.0.1", "localhost", "::1")
if ($GatewayUri.Scheme -ne "http" -or $LoopbackHosts -notcontains $GatewayUri.Host) {
    throw "MRL acceptance requires an HTTP loopback gateway"
}

Push-Location $PackageRoot
try {
    python scripts/MRL_verify_package_v1.py
    if ($LASTEXITCODE -ne 0) { throw "MRL package verification failed" }

    python -m unittest discover -s tests -v
    if ($LASTEXITCODE -ne 0) { throw "MRL autonomous runtime tests failed" }

    $Health = Invoke-RestMethod -Method Get -Uri "$GatewayUrl/health"
    if (-not $Health.ready) {
        throw "MRL local model runtime is not ready; autonomy Gate remains OPEN"
    }
    if ($Health.model.external_model_required) {
        throw "MRL autonomy Gate rejected an external model dependency"
    }

    $SessionId = "MRL_session_acceptance_$([DateTimeOffset]::UtcNow.ToUnixTimeSeconds())"
    $Request = @{
        prompt = "MRL autonomous runtime acceptance"
        world_id = "MRL_acceptance_world"
        session_id = $SessionId
    } | ConvertTo-Json
    $Result = Invoke-RestMethod `
        -Method Post `
        -Uri "$GatewayUrl/v1/mother/run" `
        -ContentType "application/json" `
        -Body $Request
    if (-not $Result.ok) { throw "MRL inference loop failed" }
    if (-not $Result.passport.passport_hash) { throw "MRL passport was not issued" }
    if (-not $Result.evidence_ref) { throw "MRL evidence was not recorded" }

    $Recall = Invoke-RestMethod -Method Get -Uri "$GatewayUrl/v1/memory/recall?world_id=MRL_acceptance_world&session_id=$SessionId"
    if ($Recall.records.Count -ne 2) { throw "MRL memory replay expected exactly two records" }

    Write-Host "MRL_AI_MOTHER_AUTONOMOUS_RUNTIME_ACCEPTANCE_PASS"
}
finally {
    Pop-Location
}
