# MRL_tailnet_bridge_receipt_v1.ps1
# origin_signature: MrLiouWord
# parent: MRL_Mother/deploy_reference/tailscale
# Read-only collection; never calls tailscale up/down/set/serve/funnel.
[CmdletBinding()]
param(
  [string]$OutDir = "$env:ProgramData\MRL\receipts",
  [string]$ExpectedHost = "WIN-PBVUI7VK2A6",
  [switch]$ProbeLoopback
)
$ErrorActionPreference = 'Stop'
function Test-Endpoint([string]$HostAddress, [int]$Port) {
  $result = [ordered]@{port=$Port;address=$HostAddress;tcp='UNKNOWN';http_status=$null}
  try {
    $client = [Net.Sockets.TcpClient]::new()
    try {
      $async = $client.BeginConnect($HostAddress,$Port,$null,$null)
      if (-not $async.AsyncWaitHandle.WaitOne(2000)) { $result.tcp='TIMEOUT' }
      else { $client.EndConnect($async); $result.tcp='PASS' }
    } finally { $client.Dispose() }
  } catch { $result.tcp='FAIL' }
  if ($result.tcp -eq 'PASS') {
    try {
      $resp = Invoke-WebRequest -Uri "http://${HostAddress}:${Port}/health" -UseBasicParsing -TimeoutSec 3 -ErrorAction Stop
      $result.http_status = [int]$resp.StatusCode
    } catch {
      if ($_.Exception.Response) { $result.http_status = [int]$_.Exception.Response.StatusCode }
    }
  }
  return $result
}
$receipt = [ordered]@{
 schema='MRL_Tailnet_Bridge_Receipt_v1'
 origin_signature='MrLiouWord'
 observed_at_utc=[DateTime]::UtcNow.ToString('o')
 host=$env:COMPUTERNAME
 expected_host=$ExpectedHost
 host_match=($env:COMPUTERNAME -ieq $ExpectedHost)
 tailscale=[ordered]@{present=$false;backend_state='UNKNOWN';self_online=$null;self_ips=@();peer_count=$null}
 services=@()
 ports=@()
 checks=[ordered]@{local_receipt='PENDING';tailnet='UNKNOWN';bridge='UNRUN';runtime='UNRUN';scanner='UNRUN';remote_roundtrip='UNRUN'}
}
$bin = Get-Command tailscale.exe -ErrorAction SilentlyContinue
if (-not $bin) {
  $candidate = Join-Path $env:ProgramFiles 'Tailscale\tailscale.exe'
  if (Test-Path -LiteralPath $candidate) { $bin = [pscustomobject]@{Source=$candidate} }
}
if ($bin) {
  $receipt.tailscale.present=$true
  try {
    $raw = & $bin.Source status --json 2>$null
    if ($LASTEXITCODE -eq 0 -and $raw) {
      $s = ($raw -join "`n") | ConvertFrom-Json
      $receipt.tailscale.backend_state=[string]$s.BackendState
      if ($s.Self) {
        $receipt.tailscale.self_online=[bool]$s.Self.Online
        $receipt.tailscale.self_ips=@($s.Self.TailscaleIPs)
      }
      if ($null -ne $s.Peer) { $receipt.tailscale.peer_count=@($s.Peer.PSObject.Properties).Count }
      $receipt.checks.tailnet=if ($s.BackendState -eq 'Running' -and $receipt.tailscale.self_online) {'PASS'} else {'FAIL'}
    } else { $receipt.checks.tailnet='UNKNOWN' }
  } catch { $receipt.checks.tailnet='UNKNOWN' }
}
foreach ($name in @('MRL_Bridge','MRL_RuntimeOS','MRL_Inference','MRL_Inference_v5','MRL_FlowAgent_API','MRL_Tunnel','MRL_Tailscale','Tailscale')) {
  $sv=Get-Service -Name $name -ErrorAction SilentlyContinue
  $receipt.services+= [ordered]@{name=$name;status=if($sv){[string]$sv.Status}else{'NOT_FOUND'}}
}
$expected=@(
  [ordered]@{name='MRL_Bridge';port=7800},
  [ordered]@{name='MRL_RuntimeOS';port=8790},
  [ordered]@{name='MRL_3DScanner_ProductBridge';port=3050},
  [ordered]@{name='MRL_Inference';port=7500},
  [ordered]@{name='MRL_FlowAgent_API';port=7900}
)
foreach ($item in $expected) {
  $listeners=@(Get-NetTCPConnection -State Listen -LocalPort $item.port -ErrorAction SilentlyContinue)
  $receipt.ports+= [ordered]@{
    name=$item.name;port=$item.port;listening=($listeners.Count -gt 0)
    binds=@($listeners|ForEach-Object {$_.LocalAddress}|Sort-Object -Unique)
    owning_pids=@($listeners|ForEach-Object {$_.OwningProcess}|Sort-Object -Unique)
  }
}
if ($ProbeLoopback) {
  $b=Test-Endpoint '127.0.0.1' 7800
  $r=Test-Endpoint '127.0.0.1' 8790
  $s=Test-Endpoint '127.0.0.1' 3050
  $receipt.local_probes=@($b,$r,$s)
  $receipt.checks.bridge=if($b.tcp -eq 'PASS' -and $b.http_status -eq 200){'PASS'}else{'FAIL'}
  $receipt.checks.runtime=if($r.tcp -eq 'PASS' -and $r.http_status -eq 200){'PASS'}else{'FAIL'}
  $receipt.checks.scanner=if($s.tcp -eq 'PASS' -and $s.http_status -eq 200){'PASS'}else{'FAIL'}
}
# The receipt contains no peer names, credentials, auth output or HTTP response body.
New-Item -ItemType Directory -Force -Path $OutDir | Out-Null
$receipt.checks.local_receipt='PASS'
$serialized=$receipt|ConvertTo-Json -Depth 9
$stamp=[DateTime]::UtcNow.ToString('yyyyMMddTHHmmssfffZ')
$path=Join-Path $OutDir "MRL_Tailnet_Bridge_Receipt_$stamp.json"
$tmp="$path.tmp"
[IO.File]::WriteAllText($tmp,$serialized,[Text.UTF8Encoding]::new($false))
Move-Item -LiteralPath $tmp -Destination $path -ErrorAction Stop
$hash=(Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash.ToLowerInvariant()
[pscustomobject]@{receipt=$path;sha256=$hash;tailnet=$receipt.checks.tailnet;remote_roundtrip='UNRUN'}|ConvertTo-Json -Compress
