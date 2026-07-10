[CmdletBinding()]
param(
    [string]$RepoName = 'MRLiou-800AI-Integrated-WindowsServer',
    [ValidateSet('private', 'public', 'internal')][string]$Visibility = 'private',
    [string]$CommitMessage = 'feat: MRLiou 800 AI Windows Server runtime v1.1.0'
)

$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot 'Common.ps1')

$root = Get-MRLProjectRoot
Set-Location $root

if (-not (Get-Command git.exe -ErrorAction SilentlyContinue)) { throw 'Git for Windows is required.' }
if (-not (Get-Command gh.exe -ErrorAction SilentlyContinue)) { throw 'GitHub CLI is required.' }
& gh auth status 2>$null
if ($LASTEXITCODE -ne 0) { throw 'GitHub CLI is not authenticated. Run: gh auth login' }

& (Join-Path $PSScriptRoot 'Verify-WindowsServer.ps1') -SkipLiveApi

$login = (& gh api user --jq .login).Trim()
if (-not $login) { throw 'Unable to determine the authenticated GitHub login.' }

if (-not (Test-Path '.git')) { & git init | Out-Null }
$gitName = (& git config --get user.name 2>$null)
$gitEmail = (& git config --get user.email 2>$null)
if (-not $gitName) { & git config user.name $login }
if (-not $gitEmail) { & git config user.email "$login@users.noreply.github.com" }

& git add .
$trackedSecrets = (& git ls-files 'secrets/*')
if ($trackedSecrets) { throw 'Secret files are tracked by Git. Stop and correct .gitignore before push.' }

$status = (& git status --porcelain)
if ($status) {
    & git commit -m $CommitMessage
    if ($LASTEXITCODE -ne 0) { throw 'Git commit failed.' }
}
& git branch -M main

$fullName = "$login/$RepoName"
& gh repo view $fullName 1>$null 2>$null
if ($LASTEXITCODE -eq 0) {
    $remote = (& git remote get-url origin 2>$null)
    $target = "https://github.com/$fullName.git"
    if ($remote) { & git remote set-url origin $target } else { & git remote add origin $target }
    & git push -u origin main
} else {
    $visibilityArg = "--$Visibility"
    & gh repo create $RepoName $visibilityArg --source . --remote origin --push
}
if ($LASTEXITCODE -ne 0) { throw 'GitHub deployment failed.' }

Write-Host "GitHub deployment completed: https://github.com/$fullName"
