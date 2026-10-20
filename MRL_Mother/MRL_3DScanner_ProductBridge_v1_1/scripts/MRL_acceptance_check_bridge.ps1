#requires -Version 5.1
[CmdletBinding()]
param([ValidateSet('Mesh','Images')][string]$Mode='Mesh', [string]$ImagesDirectory, [ValidateRange(10,7200)][int]$TimeoutSeconds=600, [string]$BeforeRebootReceipt)
. "$PSScriptRoot\MRL_bridge_common.ps1"
$c=Get-BridgeConfig
$result=[ordered]@{health='NOT_RUN'; upload='NOT_RUN'; reconstruction='NOT_RUN'; recovery='NOT_RUN'; mode=$Mode; scanId=$null; jobId=$null; reason=$null}
function Add-Line($s) { Write-Host $s }
function New-CubeObj($path) {
@"
v -0.5 -0.5 -0.5
v 0.5 -0.5 -0.5
v 0.5 0.5 -0.5
v -0.5 0.5 -0.5
v -0.5 -0.5 0.5
v 0.5 -0.5 0.5
v 0.5 0.5 0.5
v -0.5 0.5 0.5
f 1 2 3
f 1 3 4
f 5 8 7
f 5 7 6
f 1 5 6
f 1 6 2
f 2 6 7
f 2 7 3
f 3 7 8
f 3 8 4
f 4 8 5
f 4 5 1
"@ | Out-File $path -Encoding ascii
}

function Invoke-MRLUpload($uri, $filePath, $scanId, $scanName) {
  Add-Type -AssemblyName System.Net.Http
  $client = New-Object System.Net.Http.HttpClient
  $client.DefaultRequestHeaders.Add("X-MRL-Scan-ID", $scanId)
  $client.DefaultRequestHeaders.Add("X-MRL-Scan-Name", $scanName)
  $content = New-Object System.Net.Http.MultipartFormDataContent
  $bytes = [System.IO.File]::ReadAllBytes($filePath)
  $fileContent = [System.Net.Http.ByteArrayContent]::new($bytes)
  $fileContent.Headers.ContentType = [System.Net.Http.Headers.MediaTypeHeaderValue]::Parse("text/plain")
  $content.Add($fileContent, "files", [System.IO.Path]::GetFileName($filePath))
  $response = $client.PostAsync($uri, $content).Result
  $text = $response.Content.ReadAsStringAsync().Result
  $content.Dispose()
  $client.Dispose()
  if (-not $response.IsSuccessStatusCode) { throw "upload HTTP $([int]$response.StatusCode): $text" }
  return $text | ConvertFrom-Json
}


$work = Join-Path $env:TEMP ('mrl_acceptance_' + [guid]::NewGuid().ToString('N'))
New-Item -ItemType Directory $work | Out-Null
try {
    $null=Get-BridgeHealth $c; $result.health='PASS'
    if ($BeforeRebootReceipt) {
        $before=Get-Content $BeforeRebootReceipt -Raw | ConvertFrom-Json
        $boot=(Get-CimInstance Win32_OperatingSystem).LastBootUpTime.ToUniversalTime().ToString('o')
        $task=Get-BridgeTask; Assert-TaskOwner $task $c.root
        if (-not $task -or $task.State -ne 'Running' -or $before.host -ne $env:COMPUTERNAME -or $before.root -ne $c.root -or -not $before.health -or $before.bootTime -eq $boot) { throw 'Recovery evidence invalid: need a healthy receipt from this host/root before a different boot' }
        $result.recovery='PASS'; $result.beforeReceipt=$BeforeRebootReceipt
    }
    $id='acceptance_' + [guid]::NewGuid().ToString('N'); $result.scanId=$id
    if ($Mode -eq 'Mesh') {
        $file=Join-Path $work 'cube.obj'; New-CubeObj $file
        $files=@(Get-Item $file)
    } else {
        if (-not $ImagesDirectory) { throw 'ImagesDirectory required for real image reconstruction acceptance' }
        $files=@(Get-ChildItem $ImagesDirectory -File | Where-Object { $_.Extension -match '^\.(jpg|jpeg|png|heic)$' })
        if ($files.Count -lt 3) { throw 'Use at least three real overlapping photos' }
    }
    Add-Type -AssemblyName System.Net.Http
    $client=[System.Net.Http.HttpClient]::new(); $client.Timeout=[TimeSpan]::FromSeconds(120)
    $content=[System.Net.Http.MultipartFormDataContent]::new()
    try {
        $client.DefaultRequestHeaders.Add('X-MRL-Scan-ID',$id)
        foreach ($f in $files) { $part=[System.Net.Http.ByteArrayContent]::new([IO.File]::ReadAllBytes($f.FullName)); $content.Add($part,'files',$f.Name) }
        $response=$client.PostAsync('http://127.0.0.1:3050/api/scans/upload',$content).GetAwaiter().GetResult()
        $text=$response.Content.ReadAsStringAsync().GetAwaiter().GetResult()
        if (-not $response.IsSuccessStatusCode) { throw "Upload HTTP $([int]$response.StatusCode): $text" }
        $u=$text | ConvertFrom-Json
        Assert-BridgeUploadResponse $u $id $files.Count
        $scanDir=Join-Path (Join-Path $c.root 'backend\MRL_3D_Reconstruction_Server\storage\uploads') $id
        $saved=Get-Content (Join-Path $scanDir 'manifest.json') -Raw | ConvertFrom-Json
        if ($saved.uploaded -ne $files.Count) { throw 'Stored manifest mismatch' }
        foreach ($f in $files) {
            $target=Join-Path $scanDir ($f.Name -replace '[^a-zA-Z0-9._-]','_')
            if ((Get-FileHash $target).Hash -ne (Get-FileHash $f.FullName).Hash) { throw 'Stored upload hash mismatch' }
        }
        $result.upload='PASS'
    } finally { $content.Dispose(); $client.Dispose() }
    $body=@{scanId=$id; mode='auto'} | ConvertTo-Json
    $j=Invoke-RestMethod 'http://127.0.0.1:3050/api/reconstruction/jobs' -Method Post -Body $body -ContentType 'application/json' -TimeoutSec 10
    $result.jobId=$j.jobId
    $deadline=(Get-Date).AddSeconds($TimeoutSeconds)
    do {
        Start-Sleep 2
        $job=Invoke-RestMethod ("http://127.0.0.1:3050/api/reconstruction/jobs/" + $j.jobId) -TimeoutSec 10
    } while ($job.status -notin @('completed','failed') -and (Get-Date) -lt $deadline)
    $result.reason=$job.message; $result.job=$job
    if ($job.status -eq 'completed' -and $job.report.status -eq 'completed') {
        $result.reconstruction='PASS'
        $result.reconstructionScope=$(if($Mode -eq 'Mesh'){'mesh adapter smoke test; not photo reconstruction'}else{'COLMAP sparse reconstruction + MRL analysis; not dense mesh/OpenMVS'})
    } elseif ($job.status -eq 'failed' -and $job.message -like '*COLMAP_NOT_FOUND*') { $result.reconstruction='FAIL_COLMAP_MISSING' }
    elseif ($job.status -eq 'failed') { $result.reconstruction='FAIL' }
    else { $result.reconstruction='TIMEOUT' }
} catch {
    $result.reason=$_.Exception.Message
    if ($result.health -ne 'PASS') {$result.health='FAIL'}
    elseif ($result.upload -ne 'PASS') {$result.upload='FAIL'}
    else {$result.reconstruction='FAIL'}
} finally {
    Write-BridgeReceipt 'acceptance' $result
    # Only delete this run's temporary fixture. Uploaded scan/job/output evidence remains.
    Remove-Item $work -Recurse -Force
}
$result | ConvertTo-Json -Depth 12
if ($result.health -eq 'PASS' -and $result.upload -eq 'PASS' -and $result.reconstruction -eq 'PASS') { exit 0 }
exit 1
