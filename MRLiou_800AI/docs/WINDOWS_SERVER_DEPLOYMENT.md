# Windows Server Deployment

This package uses Windows PowerShell, a Python virtual environment, a generated API token, and a native Windows Scheduled Task. It does not require systemd, WSL, NSSM, or Docker.

## Supported runtime assumptions

- Windows Server with Windows PowerShell 5.1 or PowerShell 7.
- 64-bit Python 3.10 or newer in `PATH`.
- Administrator PowerShell for startup-task and firewall operations.
- Git for Windows and GitHub CLI only when pushing to GitHub.

## Recommended installation directory

Use a short local path outside OneDrive, for example:

```powershell
C:\MRLiou\MRLiou_800AI
```

## Local-only installation

```powershell
Set-ExecutionPolicy -Scope Process Bypass -Force
cd C:\MRLiou\MRLiou_800AI
.\scripts\windows\Install-WindowsServer.ps1 -InstallStartupTask
```

This binds the API to `127.0.0.1:8787`. No inbound firewall rule is required.

## Local-area-network installation

```powershell
Set-ExecutionPolicy -Scope Process Bypass -Force
cd C:\MRLiou\MRLiou_800AI
.\scripts\windows\Install-WindowsServer.ps1 `
  -ListenAddress 0.0.0.0 `
  -Port 8787 `
  -InstallStartupTask `
  -OpenFirewall `
  -RemoteAddress LocalSubnet
```

The firewall rule is limited to Domain and Private profiles and to `LocalSubnet` by default. Do not expose this HTTP service directly to the public Internet. Place IIS, a VPN, or a trusted reverse proxy in front of it when remote Internet access is required.

## Authentication

The installer generates:

```text
secrets\api_token.txt
```

The token is ignored by Git and ACL-restricted. `/health` is public; all other API endpoints require one of:

```http
X-MRL-Token: <token>
Authorization: Bearer <token>
```

PowerShell example:

```powershell
$Token = (Get-Content .\secrets\api_token.txt -Raw).Trim()
$Headers = @{ 'X-MRL-Token' = $Token }
Invoke-RestMethod http://127.0.0.1:8787/agents -Headers $Headers
```

## Operations

```powershell
# Status
.\scripts\windows\Get-RuntimeStatus.ps1

# Verify package and live API
.\scripts\windows\Verify-WindowsServer.ps1

# Stop runtime
.\scripts\windows\Stop-Runtime.ps1

# Start registered startup task
Start-ScheduledTask -TaskName MRLiou-800AI-Runtime

# Remove startup task
.\scripts\windows\Unregister-StartupTask.ps1

# Backup mutable state
.\scripts\windows\Backup-Runtime.ps1
```

## GitHub deployment

```powershell
gh auth login
.\scripts\windows\Deploy-GitHub.ps1 `
  -RepoName MRLiou-800AI-Integrated-WindowsServer `
  -Visibility private
```

The deployment script runs verification before committing and rejects tracked files under `secrets/`.

## Offline Python installation

Prepare a wheel directory on an Internet-connected machine, copy it to the server, then run:

```powershell
.\scripts\windows\Install-WindowsServer.ps1 -Wheelhouse D:\wheelhouse -InstallStartupTask
```

The wheelhouse must include all required packages and Python build dependencies for the server's Python version and architecture.
