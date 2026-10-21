[CmdletBinding()]
param(
    [string]$ListenAddress = '127.0.0.1',
    [ValidateRange(1, 65535)][int]$Port = 8787,
    [switch]$InstallStartupTask,
    [switch]$OpenFirewall,
    [string]$RemoteAddress = 'LocalSubnet',
    [string]$Wheelhouse = ''
)

$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot 'Common.ps1')

if ($InstallStartupTask -or $OpenFirewall) {
    Assert-MRLAdministrator
}

$root = Get-MRLProjectRoot
Set-Location $root

$launcher = Get-MRLPythonLauncher
Write-Host "Python $($launcher.Version) detected."

$venvPython = Join-Path $root '.venv\Scripts\python.exe'
if (-not (Test-Path $venvPython)) {
    Invoke-MRLPythonLauncher -Launcher $launcher -Arguments @('-m', 'venv', '.venv')
}

if ($Wheelhouse) {
    $resolvedWheelhouse = (Resolve-Path $Wheelhouse).Path
    & $venvPython -m pip install --no-index --find-links $resolvedWheelhouse -e $root
} else {
    & $venvPython -m pip install --upgrade pip setuptools wheel
    if ($LASTEXITCODE -ne 0) { throw 'Failed to update Python packaging tools.' }
    & $venvPython -m pip install -e $root
}
if ($LASTEXITCODE -ne 0) { throw 'Package installation failed.' }

$directories = @('logs', 'runs', 'data\raw', 'data\processed', 'data\snapshots', 'secrets')
foreach ($relative in $directories) {
    New-Item -ItemType Directory -Path (Join-Path $root $relative) -Force | Out-Null
}

$tokenPath = Join-Path $root 'secrets\api_token.txt'
if (-not (Test-Path $tokenPath)) {
    $bytes = New-Object byte[] 32
    $rng = [System.Security.Cryptography.RandomNumberGenerator]::Create()
    try { $rng.GetBytes($bytes) } finally { $rng.Dispose() }
    $token = -join ($bytes | ForEach-Object { $_.ToString('x2') })
    [System.IO.File]::WriteAllText($tokenPath, $token, (New-Object System.Text.UTF8Encoding($false)))
}

try {
    $currentUser = [Security.Principal.WindowsIdentity]::GetCurrent().Name
    & icacls.exe $tokenPath /inheritance:r | Out-Null
    & icacls.exe $tokenPath /grant:r '*S-1-5-18:(R)' '*S-1-5-32-544:(F)' "${currentUser}:(F)" | Out-Null
} catch {
    Write-Warning 'Could not harden token ACL automatically. Review the secrets directory permissions.'
}

$configPath = Join-Path $root 'config\windows_server.runtime.json'
$config = [ordered]@{
    listen_address = $ListenAddress
    port = $Port
    project_root = $root
    task_name = 'MRLiou-800AI-Runtime'
    installed_at_utc = [DateTime]::UtcNow.ToString('o')
    authentication = 'X-MRL-Token or Authorization: Bearer'
}
$config | ConvertTo-Json | Set-Content -Path $configPath -Encoding UTF8

& (Join-Path $PSScriptRoot 'Verify-WindowsServer.ps1') -SkipLiveApi

if ($OpenFirewall) {
    & (Join-Path $PSScriptRoot 'Open-Firewall.ps1') -Port $Port -RemoteAddress $RemoteAddress
}
if ($InstallStartupTask) {
    & (Join-Path $PSScriptRoot 'Register-StartupTask.ps1')
    Start-Sleep -Seconds 2
    & (Join-Path $PSScriptRoot 'Verify-WindowsServer.ps1')
}

Write-Host 'Windows Server installation completed.'
Write-Host "Project root: $root"
Write-Host "Runtime config: $configPath"
Write-Host "API token file: $tokenPath"
Write-Host "Health endpoint: http://127.0.0.1:$Port/health"
if ($ListenAddress -ne '127.0.0.1' -and $ListenAddress -ne 'localhost' -and -not $OpenFirewall) {
    Write-Warning 'The runtime is configured for network access, but no firewall rule was created.'
}
