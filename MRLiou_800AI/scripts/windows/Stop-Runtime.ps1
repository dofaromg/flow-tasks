[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'
. (Join-Path $PSScriptRoot 'Common.ps1')
Assert-MRLAdministrator

$config = Get-MRLRuntimeConfig
$taskName = [string]$config.task_name
$task = Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue
if ($task) {
    Stop-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue
}

$processes = Get-CimInstance Win32_Process | Where-Object {
    $_.CommandLine -and $_.CommandLine -match 'mrliou_800ai\.cli\s+serve'
}
foreach ($process in $processes) {
    Invoke-CimMethod -InputObject $process -MethodName Terminate | Out-Null
}
Write-Host "Runtime stop request completed. Processes terminated: $($processes.Count)"
