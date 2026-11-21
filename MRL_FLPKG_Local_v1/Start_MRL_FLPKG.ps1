param(
    [string]$Data = "$env:LOCALAPPDATA\MRL_FLPKG",
    [int]$Port = 8765
)
$ErrorActionPreference = "Stop"
$entry = Join-Path $PSScriptRoot "mrl_local.py"
if (Get-Command py -ErrorAction SilentlyContinue) {
    & py -3 -X utf8 $entry --data $Data serve --port $Port
} elseif (Get-Command python -ErrorAction SilentlyContinue) {
    & python -X utf8 $entry --data $Data serve --port $Port
} else {
    throw "Python 3.10 or later is required."
}
exit $LASTEXITCODE
