# Existing DL580 deployment/acceptance adapter. origin_signature: MrLiouWord
[CmdletBinding()]
param(
    [Parameter(Mandatory=$true)][string]$RuntimeRoot,
    [Parameter(Mandatory=$true)][string]$PythonPath,
    [Parameter(Mandatory=$true)][string]$PythonLedgerDirectory,
    [string]$SourceRoot = (Split-Path $PSScriptRoot -Parent),
    [string]$BridgeDirectory = 'D:\mrl\bridge',
    [string]$NodePath = 'D:\MrlToolchain\node\node.exe',
    [string]$NodeLedgerDirectory = 'D:\mrl\bridge\logs',
    [string]$EvidenceDirectory = 'D:\MRL_Mother\EvidenceChain\MRL_Bridge_Translation_Center',
    [string]$BridgeServiceName = 'MRL_Bridge',
    [string]$PythonServiceName,
    [ValidateRange(1,65535)][int]$BridgePort = 7800,
    [switch]$Install,
    [switch]$ReloadPython,
    [string]$DeploymentSession
)
$ErrorActionPreference = 'Stop'
if ($env:COMPUTERNAME -ne 'WIN-PBVUI7VK2A6') { throw 'DL580 host identity mismatch' }
foreach ($location in @($RuntimeRoot,$SourceRoot,$BridgeDirectory,$NodePath,$PythonPath,$NodeLedgerDirectory,$PythonLedgerDirectory,$EvidenceDirectory)) {
    if ([IO.Path]::GetPathRoot([IO.Path]::GetFullPath($location)) -ne 'D:\') { throw 'All paths must remain on D:' }
}
if ($ReloadPython -and -not $PythonServiceName) { throw 'Reload requires the existing Python service name' }
if ($ReloadPython -and -not $Install) { throw 'Reload only during the explicit installation session' }
foreach ($location in @($RuntimeRoot,$SourceRoot,$BridgeDirectory,$NodePath,$PythonPath)) {
    if (-not (Test-Path -LiteralPath $location)) { throw 'Required existing deployment path missing' }
}
if ($env:TEMP -notlike 'D:\*' -or $env:TMP -notlike 'D:\*') {
    New-Item -ItemType Directory -Force -Path (Join-Path $EvidenceDirectory 'temp') | Out-Null
    $env:TEMP = Join-Path $EvidenceDirectory 'temp'; $env:TMP = $env:TEMP
}
$commit = (& git -C $SourceRoot rev-parse HEAD).Trim()
if ($LASTEXITCODE -ne 0 -or $commit -notmatch '^[0-9a-f]{40}$') { throw 'Source must be an existing versioned checkout' }
& git -C $SourceRoot diff --quiet HEAD -- MRL_Bridge connectors MRL_Mother/09_workflow scripts docs/MRL_Bridge_Translation_Center_v1.audit.json
if ($LASTEXITCODE -ne 0) { throw 'Uncommitted deployment source changes' }

function Get-MRLProcess([int]$Id) {
    Get-CimInstance Win32_Process -Filter "ProcessId=$Id" -ErrorAction Stop
}
function Test-MRLServiceAncestor($Process, [uint32]$ServicePid) {
    $seen = @{}
    while ($Process -and -not $seen.ContainsKey([string]$Process.ProcessId)) {
        if ($Process.ProcessId -eq $ServicePid) { return $true }
        $seen[[string]$Process.ProcessId] = $true
        $Process = Get-MRLProcess ([int]$Process.ParentProcessId)
    }
    return $false
}
function Get-MRLNodeIdentity {
    $service = Get-CimInstance Win32_Service -Filter "Name='$BridgeServiceName'"
    if (-not $service -or $service.State -ne 'Running') { throw 'Existing Bridge service is not running' }
    $owners = @(Get-NetTCPConnection -State Listen -LocalPort $BridgePort | Select-Object -ExpandProperty OwningProcess -Unique)
    if ($owners.Count -ne 1) { throw 'Bridge listener identity is ambiguous' }
    $process = Get-MRLProcess ([int]$owners[0])
    if ([IO.Path]::GetFullPath($process.ExecutablePath) -ne [IO.Path]::GetFullPath($NodePath)) { throw 'Bridge listener uses another executable' }
    $entry = Join-Path $BridgeDirectory 'server.js'
    if ($process.CommandLine -notmatch ('(?:^|[\s"])' + [regex]::Escape($entry) + '(?:$|[\s"])')) { throw 'Bridge listener entrypoint differs from install target' }
    if (-not (Test-MRLServiceAncestor $process $service.ProcessId)) { throw 'Bridge listener is not owned by the selected existing service' }
    [ordered]@{ pid=[int]$process.ProcessId; created_at=$process.CreationDate.ToUniversalTime().ToString('o'); executable=$process.ExecutablePath; service_owned=$true; service=$BridgeServiceName }
}
# Validate ownership before the existing installer can stop anything.
$null = Get-MRLNodeIdentity
if ($ReloadPython) {
    $pyService = Get-CimInstance Win32_Service -Filter "Name='$PythonServiceName'"
    if (-not $pyService -or $pyService.State -ne 'Running') { throw 'Selected Python service is not running' }
    $owned = @(Get-CimInstance Win32_Process | Where-Object {
        $_.ExecutablePath -eq $PythonPath -and (Test-MRLServiceAncestor $_ $pyService.ProcessId)
    })
    if (-not $owned.Count) { throw 'Selected service has no process using the supplied Python executable' }
    # Do not overwrite service environment or infer its launcher configuration.
    # Existing launcher must already persist PYTHONPATH and MRL_TRANSLATION_LEDGER_DIR.
}
New-Item -ItemType Directory -Force -Path $EvidenceDirectory | Out-Null
if ($Install) {
    if ($DeploymentSession) { throw 'Do not reuse an old session for a new installation' }
    $session = [ordered]@{ origin_signature='MrLiouWord'; source_commit=$commit; deployment_started_at=(Get-Date).ToUniversalTime().ToString('o'); runtime_root=$RuntimeRoot; bridge_directory=$BridgeDirectory }
    $DeploymentSession = Join-Path $EvidenceDirectory ('deployment_session_' + [guid]::NewGuid().ToString('N') + '.json')
    $session | ConvertTo-Json | Set-Content -LiteralPath $DeploymentSession -Encoding UTF8
    & (Join-Path $SourceRoot 'scripts/MRL_install_bridge_translation_center.ps1') -RuntimeRoot $RuntimeRoot -SourceRoot $SourceRoot -ServiceName $BridgeServiceName -BridgePort $BridgePort -NodePath $NodePath -BridgeDirectory $BridgeDirectory
    if ($ReloadPython) {
        Restart-Service -Name $PythonServiceName
        (Get-Service -Name $PythonServiceName).WaitForStatus('Running',[TimeSpan]::FromSeconds(30))
    }
} else {
    if (-not $DeploymentSession -or [IO.Path]::GetPathRoot([IO.Path]::GetFullPath($DeploymentSession)) -ne 'D:\') { throw 'Observation requires the original D: deployment session' }
    $session = Get-Content -LiteralPath $DeploymentSession -Raw | ConvertFrom-Json
    if ($session.source_commit -ne $commit -or $session.runtime_root -ne $RuntimeRoot -or $session.bridge_directory -ne $BridgeDirectory) { throw 'Deployment session source or target mismatch' }
}
$pythonProcesses = @()
if ($PythonServiceName) {
    $pyService = Get-CimInstance Win32_Service -Filter "Name='$PythonServiceName'"
    if ($pyService -and $pyService.State -eq 'Running') {
        foreach ($process in (Get-CimInstance Win32_Process | Where-Object { $_.ExecutablePath -eq $PythonPath })) {
            if (Test-MRLServiceAncestor $process $pyService.ProcessId) {
                $pythonProcesses += [ordered]@{ pid=[int]$process.ProcessId; created_at=$process.CreationDate.ToUniversalTime().ToString('o'); executable=$process.ExecutablePath; service_owned=$true; service=$PythonServiceName }
            }
        }
    }
}
$inventory = [ordered]@{ computer=$env:COMPUTERNAME; captured_at=(Get-Date).ToUniversalTime().ToString('o'); origin_signature='MrLiouWord'; source_commit=$commit; deployment_started_at=$session.deployment_started_at; node=(Get-MRLNodeIdentity); python_processes=@($pythonProcesses) }
$token = [guid]::NewGuid().ToString('N')
$inventoryFile = Join-Path $EvidenceDirectory ("inventory_$token.json")
$outputFile = Join-Path $EvidenceDirectory ("acceptance_$token.json")
$inventory | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath $inventoryFile -Encoding UTF8
# Inherit the existing secret from this authorized process, never log it.
& $PythonPath (Join-Path $SourceRoot 'scripts/MRL_accept_bridge_translation_center.py') --inventory $inventoryFile --output $outputFile --runtime-root $RuntimeRoot --bridge-directory $BridgeDirectory --source-root $SourceRoot --node-ledger-dir $NodeLedgerDirectory --python-ledger-dir $PythonLedgerDirectory --port $BridgePort
if ($LASTEXITCODE -ne 0) { throw "Live acceptance incomplete. Preserve session: $DeploymentSession ; receipt: $outputFile" }
