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
    $venvRoot=Join-Path $root '.venv'
    $baseHome=Join-Path $temp 'base-python'
    $packageStorage=Join-Path $backend 'node_modules\@google-cloud\storage'
    $scanStorage=Join-Path $backend 'storage\uploads'
    $sitePackages=Join-Path $venvRoot 'Lib\site-packages'
    foreach($dir in @((Join-Path $root 'scripts'),(Join-Path $backend 'python'),(Join-Path $backend 'node_modules\nested'),(Join-Path $DependencyPath 'nested'),$packageStorage,$scanStorage,(Join-Path $venvRoot 'Scripts'),$sitePackages,(Join-Path $baseHome 'Lib'))) {
        $null=New-Item -ItemType Directory $dir -Force
    }
    $baseHome=(Resolve-Path -LiteralPath $baseHome).Path
    $node=Join-Path $DependencyPath 'node.exe'
    $python=Join-Path $venvRoot 'Scripts\python.exe'
    $entry=Join-Path $backend 'server.js'
    $nested=Join-Path $DependencyPath 'nested\library.dll'
    $packageFile=Join-Path $packageStorage 'index.js'
    $scanFile=Join-Path $scanStorage 'scan.bin'
    $plugin=Join-Path $sitePackages 'plugin.py'
    $baseModule=Join-Path $baseHome 'Lib\encodings.py'
    @"
home = $baseHome
include-system-site-packages = false
version = 3.12.0
"@ | Set-Content -LiteralPath (Join-Path $venvRoot 'pyvenv.cfg')
    $state=Join-Path $root '.bridge'
    $null=New-Item -ItemType Directory $state -Force
    $configFile=Join-Path $state 'config.json'
    foreach($file in @($node,$python,$entry,$nested,$packageFile,$scanFile,$plugin,$baseModule,$configFile,(Join-Path $backend 'python\mrl3d_job_runner.py'))) {
        'isolated ACL fixture; never executed' | Set-Content -LiteralPath $file
    }
    function Invoke-AclPreflight { Assert-BridgeRegistrationAcl -Root $root -Backend $backend -Node $node -Python $python -DependencyDirs @($DependencyPath) }
    Invoke-AclPreflight
    function Assert-WritableOutcome([string]$target,[bool]$mustReject,[string]$label) {
        $original=Get-Acl -LiteralPath $target
        $unsafe=Get-Acl -LiteralPath $target
        $users=New-Object Security.Principal.SecurityIdentifier('S-1-5-32-545')
        $unsafe.AddAccessRule((New-Object Security.AccessControl.FileSystemAccessRule($users,'Write','Allow')))
        Set-Acl -LiteralPath $target -AclObject $unsafe
        $rejected=$false
        try { Invoke-AclPreflight } catch {
            if($_.Exception.Message -notlike 'Broad write access*') { throw }
            $rejected=$true
        } finally { Set-Acl -LiteralPath $target -AclObject $original }
        if($mustReject) { Assert $rejected ('writable path accepted: ' + $label) }
        else { Assert (-not $rejected) ('backend storage write rejected: ' + $label) }
    }
    foreach($target in @($nested,(Join-Path $backend 'node_modules\nested'))) {
        Assert-WritableOutcome $target $true $target
    }
    Assert-WritableOutcome $packageFile $true 'nested package named storage'
    Assert-WritableOutcome $plugin $true 'venv site-packages module'
    Assert-WritableOutcome $baseModule $true 'base interpreter library'
    Assert-WritableOutcome $configFile $true 'writable .bridge config'
    Assert-WritableOutcome $scanFile $false 'backend scan storage file'
    'PASS: native ACL rejects writable nested file/directory, package storage, Python trees and .bridge config; backend storage remains writable'

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
