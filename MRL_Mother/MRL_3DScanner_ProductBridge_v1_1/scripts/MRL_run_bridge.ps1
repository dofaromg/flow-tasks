#requires -Version 5.1
. "$PSScriptRoot\MRL_bridge_common.ps1"
$c = Get-BridgeConfig
$state = Join-Path $c.root '.bridge'
$logs = Join-Path $state 'logs'; New-Item -ItemType Directory $logs -Force | Out-Null
$mutex = [Threading.Mutex]::new($false, 'Global\MRL_ProductBridge_3050')
$locked = $false
try { $locked = $mutex.WaitOne(0) } catch [Threading.AbandonedMutexException] { $locked = $true }
if (-not $locked) { $mutex.Dispose(); exit 0 }
$stop = Join-Path $state 'stop.request'
function Log($text) { "[$((Get-Date).ToUniversalTime().ToString('o'))] $text" | Add-Content (Join-Path $logs ('supervisor_' + (Get-Date -Format 'yyyyMMdd') + '.log')) -Encoding UTF8 }
try {
    $env:MRL_3D_BRIDGE_PORT = '3050'; $env:MRL_BRIDGE_INSTANCE = $c.instance; $env:MRL_BRIDGE_PYTHON = $c.python
    $env:MRL_BRIDGE_BIND = $script:BindAddresses -join ','
    $tailnet = @($script:BindAddresses | Where-Object { $_ -ne '127.0.0.1' }); $waiting = $false
    $env:PATH = (Split-Path $c.python) + ';' + $c.dependencyPath + ';' + $env:PATH
    # Only recover a surviving child recorded by this installation.
    Stop-OwnedNode $c
    while (-not (Test-Path $stop)) {
        # At boot Tailscale may come up after this task; wait for its address instead of restarting Node in a loop.
        if (@($tailnet | Where-Object { -not (Get-NetIPAddress -IPAddress $_ -ErrorAction SilentlyContinue) }).Count) {
            if (-not $waiting) { Log "WAIT_BIND_ADDRESS $($tailnet -join ',')"; $waiting = $true }
            Start-Sleep -Seconds 10; continue
        }
        if ($waiting) { Log "BIND_ADDRESS_READY $($tailnet -join ',')"; $waiting = $false }
        if (@(Get-BridgeListeners).Count) { Log 'PORT_CONFLICT: refusing to start or terminate foreign listener'; exit 2 }
        $stamp = (Get-Date -Format 'yyyyMMdd_HHmmss_fff') + '_' + [guid]::NewGuid().ToString('N')
        $child = Start-Process -FilePath $c.node -ArgumentList ('"' + $c.entry + '"') -WorkingDirectory (Split-Path $c.entry) -RedirectStandardOutput (Join-Path $logs "$stamp.stdout.log") -RedirectStandardError (Join-Path $logs "$stamp.stderr.log") -WindowStyle Hidden -PassThru
        $p = Get-CimInstance Win32_Process -Filter "ProcessId=$($child.Id)"
        if (-not $p) { throw 'Node exited before process identity was captured' }
        Write-BridgeJson (Join-Path $state 'node.json') @{pid=$child.Id; created=$p.CreationDate.ToUniversalTime().ToString('o')}
        Log "NODE_START pid=$($child.Id)"
        $failures = 0; $seenHealthy = $false; $started = Get-Date
        while (-not $child.HasExited -and -not (Test-Path $stop)) {
            Start-Sleep -Seconds 5
            try {
                $null = Get-BridgeHealth $c; $failures = 0
                if (-not $seenHealthy) { Write-BridgeReceipt 'healthy-start' @{pid=$child.Id} | Out-Null; Log "HEALTHY pid=$($child.Id)"; $seenHealthy=$true }
            } catch {
                if (((Get-Date) - $started).TotalSeconds -gt 60) { $failures++; Log "HEALTH_FAIL $($_.Exception.Message)" }
                if ($failures -ge 3) { Stop-OwnedNode $c; break }
            }
            $child.Refresh()
        }
        Stop-OwnedNode $c
        Log "NODE_STOP pid=$($child.Id) stopRequested=$(Test-Path $stop)"
        if (-not (Test-Path $stop)) { Start-Sleep -Seconds 10 }
    }
    Log 'SUPERVISOR_STOP'
} catch { Log "SUPERVISOR_ERROR $($_.Exception.Message)"; exit 1 }
finally { Stop-OwnedNode $c; $mutex.ReleaseMutex(); $mutex.Dispose() }
