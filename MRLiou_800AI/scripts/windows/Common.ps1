Set-StrictMode -Version Latest

function Get-MRLProjectRoot {
    return (Resolve-Path (Join-Path $PSScriptRoot '..\..')).Path
}

function Test-MRLAdministrator {
    $identity = [Security.Principal.WindowsIdentity]::GetCurrent()
    $principal = New-Object Security.Principal.WindowsPrincipal($identity)
    return $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
}

function Assert-MRLAdministrator {
    if (-not (Test-MRLAdministrator)) {
        throw 'Run PowerShell as Administrator for this operation.'
    }
}

function Get-MRLPythonLauncher {
    $candidates = @(
        [PSCustomObject]@{ File = 'py.exe'; Prefix = @('-3') },
        [PSCustomObject]@{ File = 'python.exe'; Prefix = @() }
    )

    foreach ($candidate in $candidates) {
        $command = Get-Command $candidate.File -ErrorAction SilentlyContinue
        if (-not $command) { continue }
        try {
            $args = @($candidate.Prefix) + @('-c', 'import sys; print(".".join(map(str, sys.version_info[:3])))')
            $versionText = (& $command.Source @args 2>$null | Select-Object -First 1).Trim()
            if ($LASTEXITCODE -eq 0 -and ([Version]$versionText -ge [Version]'3.10.0')) {
                return [PSCustomObject]@{ File = $command.Source; Prefix = @($candidate.Prefix); Version = $versionText }
            }
        } catch {
            continue
        }
    }
    throw 'Python 3.10 or newer was not found in PATH. Install 64-bit Python and enable Add Python to PATH.'
}

function Invoke-MRLPythonLauncher {
    param(
        [Parameter(Mandatory = $true)]$Launcher,
        [Parameter(Mandatory = $true)][string[]]$Arguments
    )
    $allArgs = @($Launcher.Prefix) + @($Arguments)
    & $Launcher.File @allArgs
    if ($LASTEXITCODE -ne 0) {
        throw "Python command failed with exit code $LASTEXITCODE."
    }
}

function Get-MRLVirtualPython {
    $root = Get-MRLProjectRoot
    $python = Join-Path $root '.venv\Scripts\python.exe'
    if (-not (Test-Path $python)) {
        throw 'The virtual environment is missing. Run Install-WindowsServer.ps1 first.'
    }
    return $python
}

function Get-MRLRuntimeConfig {
    $root = Get-MRLProjectRoot
    $configPath = Join-Path $root 'config\windows_server.runtime.json'
    if (-not (Test-Path $configPath)) {
        return [PSCustomObject]@{
            listen_address = '127.0.0.1'
            port = 8787
            project_root = $root
            task_name = 'MRLiou-800AI-Runtime'
        }
    }
    return (Get-Content $configPath -Raw | ConvertFrom-Json)
}

function Get-MRLApiToken {
    $root = Get-MRLProjectRoot
    $tokenPath = Join-Path $root 'secrets\api_token.txt'
    if (-not (Test-Path $tokenPath)) {
        return ''
    }
    return (Get-Content $tokenPath -Raw).Trim()
}

function Get-MRLLocalHealthUri {
    $config = Get-MRLRuntimeConfig
    return "http://127.0.0.1:$($config.port)/health"
}
