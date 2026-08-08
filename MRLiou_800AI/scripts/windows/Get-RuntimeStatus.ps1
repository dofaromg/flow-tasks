[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot 'Common.ps1')

$config = Get-MRLRuntimeConfig
$task = Get-ScheduledTask -TaskName ([string]$config.task_name) -ErrorAction SilentlyContinue
$health = $null
$agents = $null
$errorText = $null
try {
    $health = Invoke-RestMethod -Method Get -Uri (Get-MRLLocalHealthUri) -TimeoutSec 5
    $token = Get-MRLApiToken
    if ($token) {
        $headers = @{ 'X-MRL-Token' = $token }
        $agents = Invoke-RestMethod -Method Get -Uri "http://127.0.0.1:$($config.port)/agents" -Headers $headers -TimeoutSec 5
    }
} catch {
    $errorText = $_.Exception.Message
}

[ordered]@{
    task_name = [string]$config.task_name
    task_state = if ($task) { [string]$task.State } else { 'NotInstalled' }
    listen_address = [string]$config.listen_address
    port = [int]$config.port
    health = $health
    agent_count = if ($agents) { @($agents.agents).Count } else { $null }
    error = $errorText
} | ConvertTo-Json -Depth 8
