#requires -Version 5.1
. "$PSScriptRoot\MRL_bridge_common.ps1"
$root=Get-BridgeRoot
$task=Get-BridgeTask
$processes = @(Get-CimInstance Win32_Process | Where-Object { $_.Name -match '^(node|python|powershell).*' } | Select-Object ProcessId,ParentProcessId,Name,ExecutablePath,CommandLine,CreationDate)
$services = @(Get-CimInstance Win32_Service | Where-Object { $_.PathName -like '*MRL*' -or $_.Name -like '*MRL*' } | Select-Object Name,State,StartMode,PathName)
$otherTasks = @(Get-ScheduledTask | Where-Object { $_.TaskName -like '*MRL*' -or ($_.Actions | Out-String) -like '*MRL*' } | Select-Object TaskName,TaskPath,State,Actions)
try { $events=@(Get-WinEvent -FilterHashtable @{LogName='Microsoft-Windows-TaskScheduler/Operational';StartTime=(Get-CimInstance Win32_OperatingSystem).LastBootUpTime} -MaxEvents 1000 -ErrorAction Stop | Where-Object { $_.ToXml().Contains($script:TaskPath + $script:TaskName) } | Select-Object TimeCreated,Id,Message); $eventError=$null } catch { $events=@(); $eventError=$_.Exception.Message }
Write-BridgeReceipt 'status' @{processes=$processes; services=$services; relatedTasks=$otherTasks; taskEvents=$events; taskEventError=$eventError}
if ($task) { Assert-TaskOwner $task $root }
