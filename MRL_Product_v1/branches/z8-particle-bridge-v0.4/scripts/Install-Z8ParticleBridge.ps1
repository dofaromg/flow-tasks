[CmdletBinding()]
param(
    [string]$InstallRoot = 'D:\MRL_Product_v1\branches\z8-particle-bridge-v0.4'
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$sourceRoot = Split-Path -Parent $PSScriptRoot
$node = (Get-Command node -ErrorAction Stop).Source
$major = [int]((& $node --version).TrimStart('v').Split('.')[0])
if ($major -lt 20) { throw 'Node.js 20 or newer is required.' }

$sourceResolved = [IO.Path]::GetFullPath($sourceRoot).TrimEnd('\')
$installResolved = [IO.Path]::GetFullPath($InstallRoot).TrimEnd('\')
if ($sourceResolved -ne $installResolved) {
    New-Item -ItemType Directory -Path $installResolved -Force | Out-Null
    $items = @(
        '.env.example', '.gitignore', 'BUILD.bazel', 'MODULE.bazel', 'README.md', 'package.json',
        'android', 'config', 'docs', 'scripts', 'src', 'test'
    )
    foreach ($item in $items) {
        $source = Join-Path $sourceResolved $item
        if (Test-Path -LiteralPath $source) {
            Copy-Item -LiteralPath $source -Destination $installResolved -Recurse -Force
        }
    }
}

$envPath = Join-Path $installResolved '.env'
if (-not (Test-Path -LiteralPath $envPath)) {
    Copy-Item -LiteralPath (Join-Path $installResolved '.env.example') -Destination $envPath
}
New-Item -ItemType Directory -Path (Join-Path $installResolved 'data') -Force | Out-Null
New-Item -ItemType Directory -Path (Join-Path $installResolved 'logs') -Force | Out-Null

& (Join-Path $installResolved 'scripts\Test-Z8ParticleBridge.ps1') -ProjectRoot $installResolved
Write-Host "Installed independent branch at $installResolved"
Write-Host "Edit $envPath, keep Z8_BRIDGE_MODE=dry-run, then run scripts\Start-Z8ParticleBridge.ps1."
