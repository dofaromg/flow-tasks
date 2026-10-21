#requires -Version 5.1
# origin_signature: MrLiouWord
# Registration ACL and recovery helpers preserve the main/#681 validation boundary.
Set-StrictMode -Version 2.0
$ErrorActionPreference = 'Stop'

function Get-BridgeAclItems([string]$Directory, [switch]$Directories, [string]$ExcludePath = '') {
    foreach ($item in Get-ChildItem -LiteralPath $Directory -Force) {
        if ($ExcludePath -and $item.FullName -eq $ExcludePath) { continue }
        if ($item.Attributes -band [IO.FileAttributes]::ReparsePoint) { throw "Reparse point in protected code/state tree: $($item.FullName)" }
        if ($item.PSIsContainer) {
            if ($Directories) { $item.FullName }
            Get-BridgeAclItems -Directory $item.FullName -Directories:$Directories -ExcludePath $ExcludePath
        } elseif (-not $Directories) {
            $item.FullName
        }
    }
}

function Get-BridgeNormalizedDependencyPath([string]$Value) {
    Resolve-BridgeDependencyPath $Value
}

function Assert-BridgeRecoveryTrigger($repeat) {
        $start = [DateTimeOffset]::MinValue
        if (-not [DateTimeOffset]::TryParse([string]$repeat.StartBoundary,
                [Globalization.CultureInfo]::InvariantCulture,
                [Globalization.DateTimeStyles]::AllowWhiteSpaces, [ref]$start) -or
            $start -gt [DateTimeOffset]::Now.AddMinutes(2) -or
            -not [string]::IsNullOrEmpty([string]$repeat.EndBoundary) -or
            -not [string]::IsNullOrEmpty([string]$repeat.Repetition.Duration)) {
            throw ('Task recovery active window changed; refusing mutation: start={0}; end={1}; bootEnd={2}; duration={3}; stopAtEnd={4}' -f $repeat.StartBoundary, $repeat.EndBoundary, '', $repeat.Repetition.Duration, $repeat.Repetition.StopAtDurationEnd)
        }
}

function Assert-BridgeRegistrationAcl([string]$Root, [string]$Backend, [string]$Node, [string]$Python, [string[]]$DependencyDirs) {
    $writeRights = 0x500D0156
    $entry = Join-Path $Backend 'server.js'
# Discover Python's library roots from protected metadata, never by executing Python.
$pythonRoot = Split-Path $python
$venvConfig = Join-Path (Split-Path $pythonRoot) 'pyvenv.cfg'
$pythonRoots = @($pythonRoot)
if (Test-Path -LiteralPath $venvConfig -PathType Leaf) {
    $pythonRoots = @((Split-Path $pythonRoot))
    $homeLines = @(Get-Content -LiteralPath $venvConfig | Where-Object { $_ -match '^\s*home\s*=' })
    if ($homeLines.Count -ne 1) { throw 'Python venv must declare exactly one base interpreter home' }
    $pythonHome = ($homeLines[0] -split '=', 2)[1].Trim()
    if ($pythonHome -notmatch '^[A-Za-z]:[\\/]') { throw 'Python venv home must be an absolute local path' }
    $pythonRoots += (Resolve-Path -LiteralPath $pythonHome).Path
}
$state = Join-Path $root '.bridge'
$storagePath = Join-Path $backend 'storage'
# Use the .NET full-path spelling shared by FileSystemInfo.FullName (8.3 aliases).
if (Test-Path -LiteralPath $storagePath) { $storagePath = [IO.Path]::GetFullPath((Resolve-Path -LiteralPath $storagePath).Path) }
$recursiveRoots = @((Join-Path $root 'scripts')) + $dependencyDirs + $pythonRoots
if (Test-Path -LiteralPath $state) { $recursiveRoots += $state }
Write-Verbose ('ACL recursive roots: ' + ($recursiveRoots -join ';'))
Write-Verbose ('ACL backend data exclusion: ' + $storagePath)
$protectedDirectories = @($root, $backend, (Split-Path $node)) + $recursiveRoots
$protectedDirectories += @(Get-BridgeAclItems -Directory $backend -Directories -ExcludePath $storagePath)
foreach ($dir in @($recursiveRoots | Sort-Object -Unique)) {
    if (-not (Test-Path -LiteralPath $dir -PathType Container)) { throw "Protected path must be a directory: $dir" }
    $protectedDirectories += @(Get-BridgeAclItems -Directory $dir -Directories)
}
foreach ($dir in @($protectedDirectories | Sort-Object -Unique)) {
    if ((Get-Item -LiteralPath $dir -Force).Attributes -band [IO.FileAttributes]::ReparsePoint) { throw "Reparse point in protected code/state tree: $dir" }
    foreach ($ace in (Get-Acl -LiteralPath $dir).Access) {
        $sid = $ace.IdentityReference.Translate([Security.Principal.SecurityIdentifier]).Value
        if ($sid -in @('S-1-1-0','S-1-5-11','S-1-5-32-545') -and $ace.AccessControlType -eq 'Allow' -and ([int]$ace.FileSystemRights -band $writeRights)) { throw "Broad write access on $dir; protect deployment ACL before SYSTEM registration" }
    }
}
$protectedFiles = @($node, $python, $entry, (Join-Path $backend 'python\mrl3d_job_runner.py'))
$protectedFiles += @(Get-BridgeAclItems -Directory $backend -ExcludePath $storagePath)
foreach ($dir in @($recursiveRoots | Sort-Object -Unique)) {
    $protectedFiles += @(Get-BridgeAclItems -Directory $dir)
}
foreach ($file in @($protectedFiles | Sort-Object -Unique)) {
    if ((Get-Item -LiteralPath $file -Force).Attributes -band [IO.FileAttributes]::ReparsePoint) { throw "Reparse point in protected code/state tree: $file" }
    foreach ($ace in (Get-Acl -LiteralPath $file).Access) {
        $sid = $ace.IdentityReference.Translate([Security.Principal.SecurityIdentifier]).Value
        if ($sid -in @('S-1-1-0','S-1-5-11','S-1-5-32-545') -and $ace.AccessControlType -eq 'Allow' -and ([int]$ace.FileSystemRights -band $writeRights)) { throw "Broad write access on executable or loaded file $file; protect deployment ACL before SYSTEM registration" }
    }
}
}
