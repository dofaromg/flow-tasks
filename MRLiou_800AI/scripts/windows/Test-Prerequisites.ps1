[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot 'Common.ps1')

$launcher = Get-MRLPythonLauncher
$result = [ordered]@{
    os = [Environment]::OSVersion.VersionString
    powershell = $PSVersionTable.PSVersion.ToString()
    administrator = Test-MRLAdministrator
    python = $launcher.Version
    git = [bool](Get-Command git.exe -ErrorAction SilentlyContinue)
    github_cli = [bool](Get-Command gh.exe -ErrorAction SilentlyContinue)
}

$result | ConvertTo-Json
