param(
    [string]$RepoName = 'MRLiou-800AI-Integrated-WindowsServer',
    [ValidateSet('private', 'public', 'internal')][string]$Visibility = 'private',
    [string]$CommitMessage = 'feat: MRLiou 800 AI Windows Server runtime v1.1.0'
)
$ErrorActionPreference = 'Stop'
& (Join-Path $PSScriptRoot 'windows\Deploy-GitHub.ps1') @PSBoundParameters
