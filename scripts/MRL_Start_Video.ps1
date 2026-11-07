# origin_signature: MrLiouWord; canonical_authority: Mr.liou
[CmdletBinding()]
param(
    [Parameter(Mandatory=$true)][string]$Python,
    [Parameter(Mandatory=$true)][string]$Font,
    [string]$DataRoot = 'D:\mrl\video\versions',
    [string]$SourceRoot = 'D:\mrl\video\inputs',
    [int]$Port = 7812,
    [ValidateRange(1,4)][int]$SceneWorkers = 2
)
$ErrorActionPreference = 'Stop'
$RepoRoot = Split-Path -Parent $PSScriptRoot
if (!(Test-Path -LiteralPath $Python -PathType Leaf)) { throw 'Python executable unavailable' }
if (!(Test-Path -LiteralPath $Font -PathType Leaf)) { throw 'Configure a local Traditional Chinese font' }
if (!$env:MRL_VIDEO_API_KEY -and !$env:MRL_BRIDGE_API_KEY) { throw 'Bind MRL_VIDEO_API_KEY or existing MRL_BRIDGE_API_KEY' }
& $Python -c 'import PIL, fontTools' 
if ($LASTEXITCODE -ne 0) { throw 'Install MRL_Video/requirements.txt in the selected Python environment' }
Get-Command ffmpeg -ErrorAction Stop | Out-Null
Get-Command ffprobe -ErrorAction Stop | Out-Null
New-Item -ItemType Directory -Path $DataRoot -Force | Out-Null
New-Item -ItemType Directory -Path $SourceRoot -Force | Out-Null
Push-Location $RepoRoot
try {
    # Foreground process: run under the existing service supervisor for automatic restart.
    # No automatic package installs, credential generation, firewall or service changes.
    & $Python -m MRL_Video --root $DataRoot --source-root $SourceRoot --font $Font serve --port $Port --workers $SceneWorkers
    if ($LASTEXITCODE -ne 0) { throw 'MRL_Video stopped with failure' }
} finally { Pop-Location }
