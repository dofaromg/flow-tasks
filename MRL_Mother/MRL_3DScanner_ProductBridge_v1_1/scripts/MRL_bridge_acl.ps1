#requires -Version 5.1
# Registration ACL and path helpers. Loaded by MRL_bridge_common.ps1.
# Tests call this module directly; they must not parse MRL_register_bridge.ps1.
Set-StrictMode -Version 2.0
$ErrorActionPreference = 'Stop'
$script:BridgeWriteRights = 0x500D0156
$script:BridgeBroadSids = @('S-1-1-0','S-1-5-11','S-1-5-32-545')
$script:BridgeIndefiniteDuration = @('', 'P10675199DT2H48M5.4775807S')

function Test-BridgeSamePath([string]$Left, [string]$Right) {
    if (-not $Right) { return $false }
    return [IO.Path]::GetFullPath($Left).TrimEnd('\') -eq [IO.Path]::GetFullPath($Right).TrimEnd('\')
}

function Get-BridgeAclItems([string]$Directory, [switch]$Directories, [string]$ExcludePath = '') {
    foreach ($item in Get-ChildItem -LiteralPath $Directory -Force) {
        if ($item.PSIsContainer) {
            if (Test-BridgeSamePath $item.FullName $ExcludePath) { continue }
            if ($Directories) { $item.FullName }
            Get-BridgeAclItems -Directory $item.FullName -Directories:$Directories -ExcludePath $ExcludePath
        } elseif (-not $Directories) {
            $item.FullName
        }
    }
}

function Get-BridgeNormalizedDependencyPath([string]$Value) {
    return (@($Value -split ';' | Where-Object { $_.Trim() } | ForEach-Object {
        $p = $_.Trim()
        $resolved = Resolve-Path -LiteralPath $p -ErrorAction SilentlyContinue
        if ($resolved) { $resolved.Path } else { $p.TrimEnd('\') }
    }) -join ';')
}

function Get-BridgePythonLibraryTrees([string]$PythonPath) {
    $trees = @((Split-Path $PythonPath))
    $venvRoot = Split-Path (Split-Path $PythonPath)
    $venvCfg = Join-Path $venvRoot 'pyvenv.cfg'
    if (Test-Path -LiteralPath $venvCfg -PathType Leaf) {
        if (-not (Test-Path -LiteralPath $venvRoot -PathType Container)) { throw "Python venv root missing: $venvRoot" }
        $trees += (Resolve-Path -LiteralPath $venvRoot).Path
        $interpreterHome = $null
        foreach ($line in Get-Content -LiteralPath $venvCfg) {
            if ($line -match '^\s*home\s*=\s*(.+?)\s*$') {
                $interpreterHome = $Matches[1].Trim().Trim('"').Trim("'")
                break
            }
        }
        if (-not $interpreterHome) { throw 'pyvenv.cfg home is required before SYSTEM registration' }
        if (-not (Test-Path -LiteralPath $interpreterHome -PathType Container)) { throw "Python home missing: $interpreterHome" }
        $trees += (Resolve-Path -LiteralPath $interpreterHome).Path
    }
    return @($trees | Sort-Object -Unique)
}

function Assert-BridgeNoBroadWrite([string]$Path, [string]$Kind) {
    foreach ($ace in (Get-Acl -LiteralPath $Path).Access) {
        $sid = $ace.IdentityReference.Translate([Security.Principal.SecurityIdentifier]).Value
        if ($sid -in $script:BridgeBroadSids -and $ace.AccessControlType -eq 'Allow' -and ([int]$ace.FileSystemRights -band $script:BridgeWriteRights)) {
            if ($Kind -eq 'file') { throw "Broad write access on executable or loaded file $Path; protect deployment ACL before SYSTEM registration" }
            throw "Broad write access on $Path; protect deployment ACL before SYSTEM registration"
        }
    }
}

function Assert-BridgeRecoveryTrigger($repeat) {
    $startText = $null
    if ($repeat.PSObject.Properties.Name -contains 'StartBoundary') { $startText = [string]$repeat.StartBoundary }
    if (-not $startText) { throw 'Task recovery start is missing; refusing mutation' }
    try { $start = [datetime]$startText } catch { throw 'Task recovery start is invalid; refusing mutation' }
    if ($start -gt (Get-Date).AddMinutes(5)) { throw 'Task recovery start is in the future; refusing mutation' }
    $duration = ''
    if ($repeat.Repetition.PSObject.Properties.Name -contains 'Duration') { $duration = [string]$repeat.Repetition.Duration }
    if ($duration -and $duration -notin $script:BridgeIndefiniteDuration) { throw 'Task recovery repetition is not indefinite; refusing mutation' }
}

function Assert-BridgeRegistrationAcl([string]$Root, [string]$Backend, [string]$Node, [string]$Python, [string[]]$DependencyDirs) {
    $backendStorage = Join-Path $Backend 'storage'
    $pythonTrees = @(Get-BridgePythonLibraryTrees $Python)
    $state = Join-Path $Root '.bridge'
    $dependencyDirs = @($DependencyDirs | Where-Object { $_ })
    $protectedDirectories = @($Root, (Join-Path $Root 'scripts'), $Backend, (Split-Path $Node), (Split-Path $Python)) + $dependencyDirs + $pythonTrees
    if (Test-Path -LiteralPath $state -PathType Container) { $protectedDirectories += $state }
    $protectedDirectories += @(Get-BridgeAclItems -Directory (Join-Path $Root 'scripts') -Directories)
    $protectedDirectories += @(Get-BridgeAclItems -Directory $Backend -Directories -ExcludePath $backendStorage)
    foreach ($dir in $dependencyDirs) {
        $protectedDirectories += @(Get-BridgeAclItems -Directory $dir -Directories)
    }
    foreach ($dir in $pythonTrees) {
        $protectedDirectories += @(Get-BridgeAclItems -Directory $dir -Directories)
    }
    if (Test-Path -LiteralPath $state -PathType Container) {
        $protectedDirectories += @(Get-BridgeAclItems -Directory $state -Directories)
    }
    foreach ($dir in @($protectedDirectories | Sort-Object -Unique)) {
        Assert-BridgeNoBroadWrite $dir 'directory'
    }
    $protectedFiles = @($Node, $Python, (Join-Path $Backend 'server.js'), (Join-Path $Backend 'python\mrl3d_job_runner.py'))
    $protectedFiles += @(Get-BridgeAclItems -Directory (Join-Path $Root 'scripts'))
    $protectedFiles += @(Get-BridgeAclItems -Directory $Backend -ExcludePath $backendStorage)
    foreach ($dir in $dependencyDirs) {
        $protectedFiles += @(Get-BridgeAclItems -Directory $dir)
    }
    foreach ($dir in $pythonTrees) {
        $protectedFiles += @(Get-BridgeAclItems -Directory $dir)
    }
    if (Test-Path -LiteralPath $state -PathType Container) {
        $protectedFiles += @(Get-BridgeAclItems -Directory $state)
    }
    foreach ($file in @($protectedFiles | Sort-Object -Unique)) {
        Assert-BridgeNoBroadWrite $file 'file'
    }
}
