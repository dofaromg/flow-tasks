[CmdletBinding()]
param(
    [Parameter(Mandatory = $false)]
    [string]$ConfigPath = "..\config\MRL_runtime.local.example.json",

    [Parameter(Mandatory = $false)]
    [string]$DataDirectory = "..\MRL_runtime_data",

    [Parameter(Mandatory = $false)]
    [int]$Port = 7811
)

$ErrorActionPreference = "Stop"
$ScriptDirectory = Split-Path -Parent $MyInvocation.MyCommand.Path
$PackageRoot = (Resolve-Path (Join-Path $ScriptDirectory "..")).Path
$ResolvedConfig = (Resolve-Path (Join-Path $ScriptDirectory $ConfigPath)).Path
$ResolvedData = Join-Path $ScriptDirectory $DataDirectory

if (-not (Test-Path $ResolvedData)) {
    New-Item -ItemType Directory -Path $ResolvedData | Out-Null
}

Push-Location $PackageRoot
try {
    python -m runtime.MRL_apiworks_gateway_v1 `
        --config $ResolvedConfig `
        --data-dir $ResolvedData `
        --host 127.0.0.1 `
        --port $Port
}
finally {
    Pop-Location
}

