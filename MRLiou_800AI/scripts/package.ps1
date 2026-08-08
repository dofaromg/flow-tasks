$ErrorActionPreference = 'Stop'
Set-Location (Join-Path $PSScriptRoot '..')
& .\scripts\windows\Verify-WindowsServer.ps1 -SkipLiveApi
$Out = Join-Path (Split-Path (Get-Location)) 'MRLiou_800AI_Integrated_WindowsServer_GitHub_Deploy_v1_1_0.zip'
Remove-Item $Out -Force -ErrorAction SilentlyContinue
$items = Get-ChildItem -Force | Where-Object { $_.Name -notin @('.venv', '.git') }
Compress-Archive -Path $items.FullName -DestinationPath $Out -CompressionLevel Optimal
Write-Host $Out
