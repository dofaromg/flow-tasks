# GitHub Deployment from Windows Server

## Prerequisites

- Git for Windows
- GitHub CLI (`gh`)
- Authenticated GitHub CLI session

```powershell
gh auth login
```

## Verified private repository deployment

```powershell
Set-ExecutionPolicy -Scope Process Bypass -Force
cd C:\MRLiou\MRLiou_800AI
.\scripts\windows\Deploy-GitHub.ps1 `
  -RepoName MRLiou-800AI-Integrated-WindowsServer `
  -Visibility private
```

The script performs these gates:

1. Runs Windows package verification.
2. Initializes Git when required.
3. Configures repository-local Git identity when missing.
4. Stages source files.
5. Rejects tracked files under `secrets/`.
6. Commits only when changes exist.
7. Creates a private repository or updates an existing one.
8. Pushes the `main` branch.

Never place an access token in files or command history. Use `gh auth login` and the Windows credential manager.
