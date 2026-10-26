#requires -Version 5.1
$ErrorActionPreference='Stop'
if ($env:OS -ne 'Windows_NT') { throw 'Native Windows test required' }
. "$PSScriptRoot/../scripts/MRL_bridge_common.ps1"
function Assert($condition,$message) { if(-not $condition) { throw $message } }
$temp=Join-Path $env:TEMP ('MRL_bridge_regression_' + [guid]::NewGuid().ToString('N'))
$null=New-Item -ItemType Directory $temp
$job=$null; $parent=$null; $descendant=$null
try {
    # Test the registration script's real ACL preflight against an isolated protected tree.
    # No scheduled task, service, existing deployment or host ACL is changed.
    $acl=New-Object Security.AccessControl.DirectorySecurity
    $acl.SetAccessRuleProtection($true,$false)
    foreach($sid in @([Security.Principal.WindowsIdentity]::GetCurrent().User.Value,'S-1-5-18','S-1-5-32-544')) {
        $identity=New-Object Security.Principal.SecurityIdentifier($sid)
        $rule=New-Object Security.AccessControl.FileSystemAccessRule($identity,'FullControl','ContainerInherit,ObjectInherit','None','Allow')
        $acl.AddAccessRule($rule)
    }
    Set-Acl -LiteralPath $temp -AclObject $acl
    $root=Join-Path $temp 'bridge'
    $backend=Join-Path $root 'backend\MRL_3D_Reconstruction_Server'
    $DependencyPath=Join-Path $temp 'deps'
    $venv=Join-Path $root '.venv'
    $basePython=Join-Path $temp 'basePython'
    $state=Join-Path $root '.bridge'
    $storage=Join-Path $backend 'storage'
    $packageStorage=Join-Path $backend 'node_modules\@fixture\storage'
    foreach($dir in @((Join-Path $root 'scripts'),(Join-Path $backend 'python'),(Join-Path $backend 'node_modules\nested'),(Join-Path $DependencyPath 'nested'),(Join-Path $venv 'Scripts'),(Join-Path $venv 'Lib\site-packages'),(Join-Path $basePython 'Lib'),(Join-Path $basePython 'DLLs'),(Join-Path $state 'receipts'),$storage,$packageStorage)) {
        $null=New-Item -ItemType Directory $dir -Force
    }
    $node=Join-Path $DependencyPath 'node.exe'; $python=Join-Path $venv 'Scripts\python.exe'
    $entry=Join-Path $backend 'server.js'
    $nested=Join-Path $DependencyPath 'nested\library.dll'
    $venvModule=Join-Path $venv 'Lib\site-packages\module.py'
    $baseModule=Join-Path $basePython 'Lib\module.py'
    $baseDll=Join-Path $basePython 'DLLs\module.pyd'
    $configFile=Join-Path $state 'config.json'
    $packageModule=Join-Path $packageStorage 'index.js'
    foreach($file in @($node,$python,$entry,$nested,$venvModule,$baseModule,$baseDll,$configFile,$packageModule,(Join-Path $backend 'python\mrl3d_job_runner.py'))) {
        'isolated ACL fixture; never executed' | Set-Content $file
    }
    $venvConfig=Join-Path $venv 'pyvenv.cfg'
    ('home = ' + $basePython) | Set-Content $venvConfig
    $source=Get-Content "$PSScriptRoot/../scripts/MRL_register_bridge.ps1" -Raw
    $start=$source.IndexOf('$dependencyDirs =')
    $end=$source.IndexOf('$task = Get-BridgeTask')
    Assert ($start -ge 0 -and $end -gt $start) 'registration ACL section not found'
    $preflight=[scriptblock]::Create($source.Substring($start,$end-$start))
    & $preflight
    foreach($target in @($nested,(Join-Path $backend 'node_modules\nested'),$state,$configFile,(Join-Path $state 'receipts'),$venvModule,$baseModule,$baseDll,$venvConfig,$packageStorage,$packageModule)) {
        $original=Get-Acl -LiteralPath $target
        $unsafe=Get-Acl -LiteralPath $target
        $users=New-Object Security.Principal.SecurityIdentifier('S-1-5-32-545')
        $unsafe.AddAccessRule((New-Object Security.AccessControl.FileSystemAccessRule($users,'Write','Allow')))
        Set-Acl -LiteralPath $target -AclObject $unsafe
        $rejected=$false
        try { & $preflight } catch {
            if($_.Exception.Message -notlike 'Broad write access*') { throw }
            $rejected=$true
        } finally { Set-Acl -LiteralPath $target -AclObject $original }
        Assert $rejected ('nested writable dependency accepted: ' + $target)
    }
    # Only the top-level data tree is excluded; package folders named storage are code.
    $original=Get-Acl -LiteralPath $storage
    $unsafe=Get-Acl -LiteralPath $storage
    $unsafe.AddAccessRule((New-Object Security.AccessControl.FileSystemAccessRule($users,'Write','Allow')))
    try { Set-Acl -LiteralPath $storage -AclObject $unsafe; & $preflight }
    finally { Set-Acl -LiteralPath $storage -AclObject $original }
    'PASS: native ACL rejects 11 writable code/state/Python targets; only backend storage excluded'

    $canonical=Resolve-BridgeDependencyPath $DependencyPath
    foreach($legacy in @(($DependencyPath + '\'),(' ; ' + $DependencyPath.Replace('\','/') + '/ ; '),$DependencyPath.ToUpperInvariant())) {
        Assert ((Resolve-BridgeDependencyPath $legacy) -eq $canonical) 'legacy equivalent dependency path rejected'
    }
    Assert ((Resolve-BridgeDependencyPath $null) -eq (Resolve-BridgeDependencyPath ' ; ')) 'null/empty dependency paths differ'
    Assert ((Resolve-BridgeDependencyPath $basePython) -ne $canonical) 'changed dependency directory accepted'
    $rejected=$false
    try { Resolve-BridgeDependencyPath (Join-Path $temp 'missing') | Out-Null } catch { $rejected=$true }
    Assert $rejected 'missing dependency directory accepted'
    'PASS: legacy dependency paths normalize; changed/missing directories remain distinct or rejected'

    # Exercise actual ScheduledTasks CIM defaults without registering or starting any task.
    $action=New-ScheduledTaskAction -Execute (Join-Path $env:SystemRoot 'System32\WindowsPowerShell\v1.0\powershell.exe') -Argument ('-NoProfile -NonInteractive -ExecutionPolicy Bypass -File "' + (Join-Path $root 'scripts\MRL_run_bridge.ps1') + '"') -WorkingDirectory $backend
    $boot=New-ScheduledTaskTrigger -AtStartup; $boot.Delay='PT30S'
    $watch=New-ScheduledTaskTrigger -Once -At (Get-Date).AddMinutes(1) -RepetitionInterval (New-TimeSpan -Minutes 1)
    $settings=New-ScheduledTaskSettingsSet -MultipleInstances IgnoreNew -ExecutionTimeLimit ([TimeSpan]::Zero) -StartWhenAvailable -RestartCount 3 -RestartInterval (New-TimeSpan -Minutes 1) -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries
    $principal=New-ScheduledTaskPrincipal -UserId 'SYSTEM' -LogonType ServiceAccount -RunLevel Highest
    $task=New-ScheduledTask -Action $action -Trigger @($boot,$watch) -Settings $settings -Principal $principal -Description "$script:OwnerTag|$root"
    Assert-TaskOwner $task $root
    $task.Triggers[1].Repetition.Duration='PT1H'
    $rejected=$false
    try { Assert-TaskOwner $task $root } catch { $rejected=$true }
    Assert $rejected 'finite native trigger accepted'
    'PASS: native ScheduledTasks CIM active window accepted; finite repetition rejected; no task registered'

    # Assign before the fixture starts its child, then simulate a dead supervisor's Node.
    $parentFile=Join-Path $temp 'parent.ps1'
    @'
param([string]$FixtureRoot)
while(-not (Test-Path (Join-Path $FixtureRoot 'go'))) { Start-Sleep -Milliseconds 50 }
$p=Start-Process (Join-Path $PSHOME 'powershell.exe') -ArgumentList '-NoProfile -NonInteractive -Command "Start-Sleep -Seconds 120"' -PassThru
$p.Id | Set-Content (Join-Path $FixtureRoot 'descendant.pid')
Start-Sleep -Seconds 120
'@ | Set-Content $parentFile
    $job=New-BridgeProcessJob
    $parent=Start-Process (Join-Path $PSHOME 'powershell.exe') -ArgumentList ('-NoProfile -NonInteractive -ExecutionPolicy Bypass -File "' + $parentFile + '" "' + $temp + '"') -PassThru
    Add-BridgeProcessToJob $job $parent.Id
    $null=New-Item -ItemType File (Join-Path $temp 'go')
    $pidFile=Join-Path $temp 'descendant.pid'
    $deadline=(Get-Date).AddSeconds(20)
    while(-not (Test-Path $pidFile) -and (Get-Date) -lt $deadline) { Start-Sleep -Milliseconds 100 }
    Assert (Test-Path $pidFile) 'descendant was not created'
    $descendant=Get-Process -Id ([int](Get-Content $pidFile))
    $parent.Kill(); Assert ($parent.WaitForExit(5000)) 'fixture parent did not exit'
    Assert (-not $descendant.HasExited) 'descendant must survive parent to exercise orphan cleanup'
    Close-BridgeProcessJob $job; $job=$null
    Assert ($descendant.WaitForExit(5000)) 'kill-on-close failed to terminate orphan descendant'
    'PASS: native Windows Job Object kills surviving descendant after parent exits'
} finally {
    if($job) { Close-BridgeProcessJob $job }
    foreach($process in @($parent,$descendant)) {
        if($process) { try { if(-not $process.HasExited) { $process.Kill(); $null=$process.WaitForExit(5000) } } catch {} }
    }
    Remove-Item -LiteralPath $temp -Recurse -Force
}
