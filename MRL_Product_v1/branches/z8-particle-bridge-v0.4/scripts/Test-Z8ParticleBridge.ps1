[CmdletBinding()]
param(
    [string]$ProjectRoot = (Split-Path -Parent $PSScriptRoot)
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$node = (Get-Command node -ErrorAction Stop).Source
$major = [int]((& $node --version).TrimStart('v').Split('.')[0])
if ($major -lt 20) { throw 'Node.js 20 or newer is required.' }

Push-Location -LiteralPath $ProjectRoot
try {
    & $node --test
    if ($LASTEXITCODE -ne 0) { throw "Runtime tests failed with exit code $LASTEXITCODE." }
    & $node (Join-Path $ProjectRoot 'scripts\audit.mjs')
    if ($LASTEXITCODE -ne 0) { throw "Package audit failed with exit code $LASTEXITCODE." }
}
finally {
    Pop-Location
}
