Set-StrictMode -Version 2.0
$ErrorActionPreference = 'Stop'
$script:TaskName = 'MRL_3DScanner_ProductBridge'
$script:TaskPath = '\MRL\'
$script:OwnerTag = 'MRL-Bridge-Startup-v1'
# ROOT: enter and leave only through DL580's Tailscale address; loopback is for on-host health checks.
$script:BindAddresses = @('100.78.70.78','127.0.0.1')
if (-not ('MRLBridgeProcessJob' -as [type])) {
    Add-Type -TypeDefinition @'
using System;
using System.ComponentModel;
using System.Diagnostics;
using System.Runtime.InteropServices;

public static class MRLBridgeProcessJob
{
    [StructLayout(LayoutKind.Sequential)]
    private struct BasicLimitInformation
    {
        public long PerProcessUserTimeLimit;
        public long PerJobUserTimeLimit;
        public uint LimitFlags;
        public UIntPtr MinimumWorkingSetSize;
        public UIntPtr MaximumWorkingSetSize;
        public uint ActiveProcessLimit;
        public UIntPtr Affinity;
        public uint PriorityClass;
        public uint SchedulingClass;
    }

    [StructLayout(LayoutKind.Sequential)]
    private struct IoCounters
    {
        public ulong ReadOperationCount;
        public ulong WriteOperationCount;
        public ulong OtherOperationCount;
        public ulong ReadTransferCount;
        public ulong WriteTransferCount;
        public ulong OtherTransferCount;
    }

    [StructLayout(LayoutKind.Sequential)]
    private struct ExtendedLimitInformation
    {
        public BasicLimitInformation BasicLimitInformation;
        public IoCounters IoInfo;
        public UIntPtr ProcessMemoryLimit;
        public UIntPtr JobMemoryLimit;
        public UIntPtr PeakProcessMemoryUsed;
        public UIntPtr PeakJobMemoryUsed;
    }

    [DllImport("kernel32.dll", CharSet = CharSet.Unicode, SetLastError = true)]
    private static extern IntPtr CreateJobObject(IntPtr attributes, string name);
    [DllImport("kernel32.dll", SetLastError = true)]
    private static extern bool SetInformationJobObject(IntPtr job, int infoClass, ref ExtendedLimitInformation info, uint length);
    [DllImport("kernel32.dll", SetLastError = true)]
    private static extern IntPtr OpenProcess(uint access, bool inheritHandle, uint processId);
    [DllImport("kernel32.dll", SetLastError = true)]
    private static extern bool AssignProcessToJobObject(IntPtr job, IntPtr process);
    [DllImport("kernel32.dll", SetLastError = true)]
    private static extern bool CloseHandle(IntPtr handle);

    public static IntPtr Create()
    {
        IntPtr job = CreateJobObject(IntPtr.Zero, null);
        if (job == IntPtr.Zero) throw new Win32Exception(Marshal.GetLastWin32Error());
        ExtendedLimitInformation info = new ExtendedLimitInformation();
        info.BasicLimitInformation.LimitFlags = 0x2000;
        if (!SetInformationJobObject(job, 9, ref info, (uint)Marshal.SizeOf(typeof(ExtendedLimitInformation))))
        {
            int error = Marshal.GetLastWin32Error();
            CloseHandle(job);
            throw new Win32Exception(error);
        }
        return job;
    }

    public static void Assign(IntPtr job, int processId)
    {
        IntPtr process = OpenProcess(0x0100 | 0x0001, false, (uint)processId);
        if (process == IntPtr.Zero) throw new Win32Exception(Marshal.GetLastWin32Error());
        try
        {
            if (!AssignProcessToJobObject(job, process))
                throw new Win32Exception(Marshal.GetLastWin32Error());
        }
        finally { CloseHandle(process); }
    }

    public static void Close(IntPtr job)
    {
        if (job != IntPtr.Zero && !CloseHandle(job))
            throw new Win32Exception(Marshal.GetLastWin32Error());
    }
}
'@
}
function Get-BridgeRoot { (Resolve-Path (Join-Path $PSScriptRoot '..')).Path }
function Resolve-BridgeDependencyPath([string]$value) {
    $paths = @($value -split ';' | Where-Object { $_.Trim() } | ForEach-Object {
        $resolved = Resolve-Path -LiteralPath $_.Trim()
        if ($resolved.Provider.Name -ne 'FileSystem' -or -not (Test-Path -LiteralPath $resolved.Path -PathType Container)) {
            throw "Dependency path must be a filesystem directory: $_"
        }
        $path = [IO.Path]::GetFullPath($resolved.Path)
        if ($path.Length -gt [IO.Path]::GetPathRoot($path).Length) { $path = $path.TrimEnd([char[]]'\/') }
        $path
    })
    return ($paths -join ';')
}
function Get-BridgeConfig {
    $c = Get-Content (Join-Path (Get-BridgeRoot) '.bridge\config.json') -Raw | ConvertFrom-Json
    if ($c.root -ne (Get-BridgeRoot) -or $c.port -ne 3050) { throw 'Config root/port mismatch' }
    return $c
}
function Assert-Administrator {
    $i = [Security.Principal.WindowsIdentity]::GetCurrent()
    if (-not ([Security.Principal.WindowsPrincipal]::new($i)).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) { throw 'Run elevated Windows PowerShell 5.1' }
}
function Get-BridgeTask { Get-ScheduledTask -TaskPath $script:TaskPath -TaskName $script:TaskName -ErrorAction SilentlyContinue }
function Assert-TaskOwner($task, $root) {
    if ($task -and $task.Description -ne "$script:OwnerTag|$root") { throw 'Task belongs to another install; refusing mutation' }
    if ($task) {
        $expected = '-NoProfile -NonInteractive -ExecutionPolicy Bypass -File "' + (Join-Path $root 'scripts\MRL_run_bridge.ps1') + '"'
        if (@($task.Actions).Count -ne 1 -or
            $task.Actions[0].Arguments -ne $expected -or
            $task.Actions[0].Execute -ne (Join-Path $env:SystemRoot 'System32\WindowsPowerShell\v1.0\powershell.exe') -or
            $task.Actions[0].WorkingDirectory -ne (Join-Path $root 'backend\MRL_3D_Reconstruction_Server')) {
            throw 'Task action changed; refusing mutation'
        }
        $boot = @($task.Triggers | Where-Object { $_.CimClass.CimClassName -eq 'MSFT_TaskBootTrigger' })
        $repeat = @($task.Triggers | Where-Object { $_.CimClass.CimClassName -eq 'MSFT_TaskTimeTrigger' })
        $settings = $task.Settings
        $principal = $task.Principal
        if (@($task.Triggers).Count -ne 2 -or $boot.Count -ne 1 -or $repeat.Count -ne 1 -or
            -not $boot[0].Enabled -or $boot[0].Delay -ne 'PT30S' -or
            -not $repeat[0].Enabled -or $repeat[0].Repetition.Interval -ne 'PT1M' -or
            $principal.UserId -notin @('SYSTEM','NT AUTHORITY\SYSTEM','S-1-5-18') -or
            $principal.LogonType -ne 'ServiceAccount' -or $principal.RunLevel -ne 'Highest' -or
            $settings.MultipleInstances -ne 'IgnoreNew' -or
            $settings.ExecutionTimeLimit -ne 'PT0S' -or
            -not $settings.StartWhenAvailable -or
            $settings.RestartCount -ne 3 -or $settings.RestartInterval -ne 'PT1M' -or
            $settings.DisallowStartIfOnBatteries -or $settings.StopIfGoingOnBatteries) {
            throw 'Task recovery definition changed; refusing mutation'
        }
        # Registration starts the watch one minute ahead. Allow that initial window,
        # but reject delayed, expired or finite recovery definitions thereafter.
        $start = [DateTimeOffset]::MinValue
        if (-not [DateTimeOffset]::TryParse([string]$repeat[0].StartBoundary,
                [Globalization.CultureInfo]::InvariantCulture,
                [Globalization.DateTimeStyles]::AllowWhiteSpaces, [ref]$start) -or
            $start -gt [DateTimeOffset]::Now.AddMinutes(2) -or
            -not [string]::IsNullOrEmpty([string]$repeat[0].EndBoundary) -or
            -not [string]::IsNullOrEmpty([string]$boot[0].EndBoundary) -or
            -not [string]::IsNullOrEmpty([string]$repeat[0].Repetition.Duration)) {
            throw ('Task recovery active window changed; refusing mutation: start={0}; end={1}; bootEnd={2}; duration={3}; stopAtEnd={4}' -f $repeat[0].StartBoundary, $repeat[0].EndBoundary, $boot[0].EndBoundary, $repeat[0].Repetition.Duration, $repeat[0].Repetition.StopAtDurationEnd)
        }
        # Native PS5.1 sets StopAtDurationEnd even for an indefinite trigger.
        # With no duration/end boundary it cannot terminate the recovery window.
    }
}
function New-BridgeProcessJob { [MRLBridgeProcessJob]::Create() }
function Add-BridgeProcessToJob($job, $processId) { [MRLBridgeProcessJob]::Assign($job, $processId) }
function Close-BridgeProcessJob($job) { if ($job -and $job -ne [IntPtr]::Zero) { [MRLBridgeProcessJob]::Close($job) } }
function Get-BridgeListeners { @(Get-NetTCPConnection -LocalPort 3050 -State Listen -ErrorAction SilentlyContinue | Select-Object -ExpandProperty OwningProcess -Unique) }
function Test-BridgeProcess($record, $c) {
    if (-not $record) { return $false }
    $p = Get-CimInstance Win32_Process -Filter "ProcessId=$($record.pid)" -ErrorAction SilentlyContinue
    return ($p -and $p.ExecutablePath -eq $c.node -and $p.CreationDate.ToUniversalTime().ToString('o') -eq $record.created -and $p.CommandLine.Contains('"' + $c.entry + '"'))
}
function Get-BridgeRecord($c) {
    $file = Join-Path $c.root '.bridge\node.json'
    if (Test-Path $file) { return (Get-Content $file -Raw | ConvertFrom-Json) }
    return $null
}
function Get-BridgeHealth($c) {
    $h = Invoke-RestMethod 'http://127.0.0.1:3050/api/health' -TimeoutSec 5
    $record = Get-BridgeRecord $c
    $listeners = @(Get-BridgeListeners)
    if ($h.ok -ne $true -or $h.service -ne 'MRL_3D_Reconstruction_Server' -or $h.version -ne '1.0.0' -or $h.port -ne 3050 -or $h.instance -ne $c.instance -or $h.pid -ne $record.pid -or -not (Test-BridgeProcess $record $c) -or $listeners.Count -ne 1 -or $listeners[0] -ne $h.pid) { throw 'Health/process/port identity mismatch' }
    return $h
}
function Assert-BridgeUploadResponse($response, [string]$scanId, [int]$count) {
    $keys = @($response.PSObject.Properties.Name | Sort-Object)
    if (($keys -join ',') -ne 'ok,scanId,uploaded' -or
        $response.ok -ne $true -or $response.scanId -cne $scanId -or $response.uploaded -ne $count) {
        throw 'Upload API contract/count/ID mismatch (server-local paths are forbidden)'
    }
}
function Write-BridgeJson($file, $data) {
    $temp = "$file.$PID.tmp"
    $data | ConvertTo-Json -Depth 12 | Set-Content $temp -Encoding UTF8
    Move-Item $temp $file -Force
}
function Write-BridgeReceipt($operation, $extra) {
    $root = Get-BridgeRoot
    $dir = Join-Path $root '.bridge\receipts'
    New-Item -ItemType Directory $dir -Force | Out-Null
    $task = Get-BridgeTask
    $info = if ($task) { Get-ScheduledTaskInfo -TaskPath $script:TaskPath -TaskName $script:TaskName } else { $null }
    $health = $null; $healthError = $null
    try { $health = Get-BridgeHealth (Get-BridgeConfig) } catch { $healthError = $_.Exception.Message }
    $receipt = [ordered]@{ operation=$operation; time=(Get-Date).ToUniversalTime().ToString('o'); host=$env:COMPUTERNAME; root=$root; bootTime=(Get-CimInstance Win32_OperatingSystem).LastBootUpTime.ToUniversalTime().ToString('o'); taskState=$(if($task){[string]$task.State}else{'Absent'}); lastTaskResult=$(if($info){$info.LastTaskResult}else{$null}); lastTaskRunTime=$(if($info){$info.LastRunTime.ToUniversalTime().ToString('o')}else{$null}); listeners=@(Get-BridgeListeners); listenAddresses=@(Get-NetTCPConnection -LocalPort 3050 -State Listen -ErrorAction SilentlyContinue | ForEach-Object { [string]$_.LocalAddress }); health=$health; healthError=$healthError; extra=$extra; hashes=@(Get-ChildItem (Join-Path $root 'scripts') -Filter '*.ps1' | Get-FileHash -Algorithm SHA256 | Select-Object Path,Hash) }
    $name = (Get-Date -Format 'yyyyMMdd_HHmmss_fff') + '_' + $operation + '_' + [guid]::NewGuid().ToString('N') + '.json'
    $file = Join-Path $dir $name
    Write-BridgeJson $file $receipt
    if ($task) { Export-ScheduledTask -TaskPath $script:TaskPath -TaskName $script:TaskName | Set-Content "$file.task.xml" -Encoding UTF8 }
    Write-Output $file
}
function Stop-OwnedNode($c) {
    $r = Get-BridgeRecord $c
    if (Test-BridgeProcess $r $c) {
        & "$env:SystemRoot\System32\taskkill.exe" /PID $r.pid /T /F | Out-Null
        if ($LASTEXITCODE -ne 0 -and (Test-BridgeProcess $r $c)) { throw 'Could not stop owned Node process tree' }
    }
}
