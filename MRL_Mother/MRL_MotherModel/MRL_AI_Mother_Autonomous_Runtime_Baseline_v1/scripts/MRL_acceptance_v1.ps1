[CmdletBinding()]
param(
    [Parameter(Mandatory = $false)]
    [string]$GatewayUrl = "http://127.0.0.1:7811",
    [Parameter(Mandatory = $true)]
    [ValidatePattern("^[0-9a-f]{40}$")]
    [string]$GitHead,
    [Parameter(Mandatory = $true)]
    [ValidatePattern("^MRL_[A-Za-z0-9_.:-]+$")]
    [string]$HardwareId,
    [Parameter(Mandatory = $true)]
    [ValidatePattern("^MRL_[A-Za-z0-9_.:-]+$")]
    [string]$OperatorId,
    [Parameter(Mandatory = $true)]
    [string]$ModelArtifactPath,
    [Parameter(Mandatory = $true)]
    [string]$ModelReleaseManifestPath,
    [Parameter(Mandatory = $true)]
    [string]$ReceiptPath,
    [Parameter(Mandatory = $true)]
    [switch]$ExternalModelDisconnected
)

$ErrorActionPreference = "Stop"
$ScriptDirectory = Split-Path -Parent $MyInvocation.MyCommand.Path
$PackageRoot = (Resolve-Path (Join-Path $ScriptDirectory "..")).Path
$GatewayUri = [Uri]$GatewayUrl
$LoopbackHosts = @("127.0.0.1", "localhost", "::1")
if ($GatewayUri.Scheme -ne "http" -or $LoopbackHosts -notcontains $GatewayUri.Host) {
    throw "MRL acceptance requires an HTTP loopback gateway"
}
if (-not $ExternalModelDisconnected.IsPresent) {
    throw "MRL acceptance requires an explicit external-model-disconnected observation"
}
$ResolvedModelArtifact = (Resolve-Path $ModelArtifactPath).Path
$ResolvedModelReleaseManifest = (Resolve-Path $ModelReleaseManifestPath).Path
$ModelRelease = Get-Content -Raw -Path $ResolvedModelReleaseManifest | ConvertFrom-Json
if ($ModelRelease.origin_signature -ne "MrLiouWord") {
    throw "MRL model release manifest origin signature mismatch"
}
if ($ModelRelease.release_id -notmatch "^MRL_[A-Za-z0-9_.:-]+$") {
    throw "MRL model release manifest release_id is invalid"
}
if ($ModelRelease.sha256 -notmatch "^[0-9a-f]{64}$") {
    throw "MRL model release manifest SHA-256 is invalid"
}
$ActualModelSha256 = (Get-FileHash -Algorithm SHA256 -Path $ResolvedModelArtifact).Hash.ToLowerInvariant()
if ($ActualModelSha256 -ne $ModelRelease.sha256.ToLowerInvariant()) {
    throw "MRL model artifact SHA-256 does not match the expected release hash"
}
$ActualModelSize = (Get-Item -LiteralPath $ResolvedModelArtifact).Length
if ($ActualModelSize -ne [long]$ModelRelease.size) {
    throw "MRL model artifact size does not match the release manifest"
}
$ModelReleaseManifestSha256 = (Get-FileHash -Algorithm SHA256 -Path $ResolvedModelReleaseManifest).Hash.ToLowerInvariant()

function Get-MrlSha256([string]$Text) {
    $Bytes = [System.Text.Encoding]::UTF8.GetBytes($Text)
    $Hash = [System.Security.Cryptography.SHA256]::Create()
    try {
        return ([System.BitConverter]::ToString($Hash.ComputeHash($Bytes))).Replace("-", "").ToLowerInvariant()
    }
    finally {
        $Hash.Dispose()
    }
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
    $RequestSha256 = Get-MrlSha256 $Request
    $Result = Invoke-RestMethod `
        -Method Post `
        -Uri "$GatewayUrl/v1/mother/run" `
        -ContentType "application/json" `
        -Body $Request
    if (-not $Result.ok) { throw "MRL inference loop failed" }
    if (-not $Result.passport.passport_hash) { throw "MRL passport was not issued" }
    if (-not $Result.evidence_ref) { throw "MRL evidence was not recorded" }
    if ($Result.model -ne $ModelRelease.model_name) { throw "MRL runtime model does not match the release manifest" }
    if (@($ModelRelease.runtime | ForEach-Object { $_.ToString().ToLowerInvariant() }) -notcontains $Result.backend.ToLowerInvariant()) {
        throw "MRL runtime backend is not authorized by the release manifest"
    }
    $ResultJson = $Result | ConvertTo-Json -Depth 20 -Compress
    $ResultSha256 = Get-MrlSha256 $ResultJson

    $Recall = Invoke-RestMethod -Method Get -Uri "$GatewayUrl/v1/memory/recall?world_id=MRL_acceptance_world&session_id=$SessionId"
    if ($Recall.records.Count -ne 2) { throw "MRL memory replay expected exactly two records" }

    $FinalHealth = Invoke-RestMethod -Method Get -Uri "$GatewayUrl/health"
    if (-not $FinalHealth.ready) { throw "MRL runtime became unhealthy after inference" }
    $Receipt = [ordered]@{
        schema = "MRL_AI_Mother_Live_Acceptance_v1"
        canonical_id = "MRL_AI_Mother_Autonomous_Runtime_Baseline_v1"
        origin_signature = "MrLiouWord"
        git_head = $GitHead
        hardware_id = $HardwareId
        runtime_id = $FinalHealth.runtime_id
        backend = $Result.backend
        model = $Result.model
        model_endpoint = $Health.model.endpoint
        model_release_id = $ModelRelease.release_id
        model_release_manifest_sha256 = $ModelReleaseManifestSha256
        model_artifact_sha256 = $ActualModelSha256
        model_artifact_size_bytes = $ActualModelSize
        model_sha256_verified = $true
        health_ready = [bool]$FinalHealth.ready
        memory_chain_head = $FinalHealth.memory.head
        evidence_chain_head = $FinalHealth.evidence.head
        passport_hash = $Result.passport.passport_hash
        return_anchor = $Result.passport.return_anchor
        evidence_ref = $Result.evidence_ref
        request_sha256 = $RequestSha256
        result_sha256 = $ResultSha256
        external_model_disconnected = $true
        accepted_at = [DateTimeOffset]::UtcNow.ToString("o")
        operator_id = $OperatorId
        acceptance_gate = "MRL_AI_MOTHER_AUTONOMOUS_RUNTIME_ACCEPTANCE_PASS"
    }
    $ReceiptDirectory = Split-Path -Parent $ReceiptPath
    if ($ReceiptDirectory) { New-Item -ItemType Directory -Force -Path $ReceiptDirectory | Out-Null }
    $Receipt | ConvertTo-Json -Depth 20 | Set-Content -Encoding UTF8 -Path $ReceiptPath

    python scripts/MRL_verify_live_acceptance_receipt_v1.py $ReceiptPath
    if ($LASTEXITCODE -ne 0) { throw "MRL live acceptance receipt verification failed" }

    Write-Host "MRL_AI_MOTHER_AUTONOMOUS_RUNTIME_ACCEPTANCE_PASS"
}
finally {
    Pop-Location
}
