# MRLiou 800 AI Integrated Engineering System — Windows Server v1.1.0

**Origin Signature:** `MrLiouWord`  
**Canonical deployment:** Windows Server  
**Package purpose:** Integrate the MRLiou 800-AI enterprise organization, engineering wake protocol, reversible FlowCore principles, engineering-agent routing, and CFD/physics-law audit capability into one GitHub-ready Windows Server deployment package.

## Included capabilities

- Exact eight-role allocation totaling 800 logical AI workers.
- Engineering gate: `collect → compare → plan → execute → verify`.
- Architect, Engineer, Reviewer, Optimizer, Debugger, Refactorer, UI Builder, and Physics Auditor routing.
- Reversible datastore with pre-write snapshots and SHA-256 trace-chain evidence.
- 2D/3D regular-grid mass-conservation audit.
- CLI and local HTTP API.
- API-token protection for every endpoint except `/health`.
- Native Windows Server installation through PowerShell.
- Automatic startup through Windows Task Scheduler under `SYSTEM`.
- Domain/Private Windows Firewall helper restricted to `LocalSubnet` by default.
- GitHub private-repository deployment script with pre-push verification and secret-file rejection.
- Tests, CI, Docker/Linux compatibility assets, evidence sources, manifests, and package hashes.

## Windows Server quick start

Extract the package to a stable local path, for example:

```text
C:\MRLiou\MRLiou_800AI
```

Open **PowerShell as Administrator**:

```powershell
Set-ExecutionPolicy -Scope Process Bypass -Force
cd C:\MRLiou\MRLiou_800AI

# Local-only API, automatic startup
.\scripts\windows\Install-WindowsServer.ps1 -InstallStartupTask

# Check status
.\scripts\windows\Get-RuntimeStatus.ps1

# Full verification, including the live API
.\scripts\windows\Verify-WindowsServer.ps1
```

### Allow access from the local network

```powershell
.\scripts\windows\Install-WindowsServer.ps1 `
  -ListenAddress 0.0.0.0 `
  -Port 8787 `
  -InstallStartupTask `
  -OpenFirewall `
  -RemoteAddress LocalSubnet
```

Do not publish port 8787 directly to the public Internet. Use a VPN, IIS reverse proxy, or another trusted access layer.

## Authentication

Installation generates `secrets\api_token.txt`. It is excluded from Git and protected with Windows ACLs.

```powershell
$Token = (Get-Content .\secrets\api_token.txt -Raw).Trim()
$Headers = @{ 'X-MRL-Token' = $Token }
Invoke-RestMethod http://127.0.0.1:8787/agents -Headers $Headers
```

`GET /health` does not require a token. All other endpoints do when the token exists.

## GitHub deployment from Windows Server

Install Git for Windows and GitHub CLI, then authenticate:

```powershell
gh auth login
```

Create or update a private repository:

```powershell
.\scripts\windows\Deploy-GitHub.ps1 `
  -RepoName MRLiou-800AI-Integrated-WindowsServer `
  -Visibility private
```

The script runs the verification gate before commit and push.

## Main API

| Method | Endpoint | Authentication | Function |
|---|---|---:|---|
| GET | `/health` | No | Runtime and trace-chain health |
| GET | `/organization` | Yes | 800-AI organization map |
| GET | `/agents` | Yes | Agent registry |
| POST | `/tasks/dispatch` | Yes | Dispatch through the engineering gate |
| POST | `/vault/write` | Yes | Additive and reversible text write |
| POST | `/physics/mass-audit` | Yes | 2D/3D mass-conservation audit |

## CLI

```powershell
.\.venv\Scripts\python.exe -m mrliou_800ai.cli health
.\.venv\Scripts\python.exe -m mrliou_800ai.cli agents
.\.venv\Scripts\python.exe -m mrliou_800ai.cli dispatch --task "audit the runtime API"
.\.venv\Scripts\python.exe -m mrliou_800ai.cli mass-audit --data examples\cfd_mass_sample.npz --out runs\cfd-audit
```

## Windows operation scripts

| Script | Purpose |
|---|---|
| `Install-WindowsServer.ps1` | Create virtual environment, install package, generate token, write runtime config |
| `Register-StartupTask.ps1` | Register and start boot-time runtime task |
| `Get-RuntimeStatus.ps1` | Report task state, API health, and role count |
| `Verify-WindowsServer.ps1` | Unit tests, CLI health, CFD audit, config/token checks, optional live API |
| `Open-Firewall.ps1` | Add restricted Domain/Private inbound rule |
| `Close-Firewall.ps1` | Remove the runtime firewall rule |
| `Backup-Runtime.ps1` | Back up mutable runtime state |
| `Deploy-GitHub.ps1` | Verify, commit, create/update repository, push |

See `docs/WINDOWS_SERVER_DEPLOYMENT.md`, `docs/WINDOWS_SERVER_OPERATIONS.md`, `ROADMAP.md`, and `manifest/AUDIT_REPORT.md`.
