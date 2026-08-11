[CmdletBinding()]
param(
    [string]$ProjectRoot = (Split-Path -Parent $PSScriptRoot)
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function Import-MrlDotEnv {
    param([string]$Path)
    if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) { return }
    foreach ($line in Get-Content -LiteralPath $Path) {
        $trimmed = $line.Trim()
        if (-not $trimmed -or $trimmed.StartsWith('#')) { continue }
        $separator = $trimmed.IndexOf('=')
        if ($separator -lt 1) { continue }
        $name = $trimmed.Substring(0, $separator).Trim()
        $value = $trimmed.Substring($separator + 1).Trim().Trim('"').Trim("'")
        [Environment]::SetEnvironmentVariable($name, $value, 'Process')
    }
}

$node = (Get-Command node -ErrorAction Stop).Source
Import-MrlDotEnv -Path (Join-Path $ProjectRoot '.env')
Set-Location -LiteralPath $ProjectRoot
& $node (Join-Path $ProjectRoot 'src\server.js')
exit $LASTEXITCODE
