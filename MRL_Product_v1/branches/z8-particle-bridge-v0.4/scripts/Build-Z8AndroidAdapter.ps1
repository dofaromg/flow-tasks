[CmdletBinding()]
param(
    [string]$ProjectRoot = (Split-Path -Parent $PSScriptRoot),
    [string]$OutputDirectory = (Join-Path (Split-Path -Parent $PSScriptRoot) 'artifacts')
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
if (-not $env:ANDROID_SDK_ROOT -and -not $env:ANDROID_HOME) {
    throw 'ANDROID_SDK_ROOT or ANDROID_HOME must point to the local Android SDK.'
}
$gradle = (Get-Command gradle -ErrorAction Stop).Source
$androidRoot = Join-Path $ProjectRoot 'android'
Push-Location -LiteralPath $androidRoot
try {
    & $gradle --no-daemon :app:assembleDebug
    if ($LASTEXITCODE -ne 0) { throw "Android build failed with exit code $LASTEXITCODE." }
}
finally {
    Pop-Location
}

$sourceApk = Join-Path $androidRoot 'app\build\outputs\apk\debug\app-debug.apk'
if (-not (Test-Path -LiteralPath $sourceApk)) { throw "APK was not generated at $sourceApk." }
New-Item -ItemType Directory -Path $OutputDirectory -Force | Out-Null
$apk = Join-Path $OutputDirectory 'Mrliou_Z8_ParticleBridge_v0.4-debug.apk'
Copy-Item -LiteralPath $sourceApk -Destination $apk -Force
$digest = (Get-FileHash -LiteralPath $apk -Algorithm SHA256).Hash.ToLowerInvariant()
"$digest  $([IO.Path]::GetFileName($apk))" | Set-Content -LiteralPath "$apk.sha256" -Encoding ascii
Write-Host "APK: $apk"
Write-Host "SHA-256: $digest"
