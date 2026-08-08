$ErrorActionPreference = "Stop"
$root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$reportDir = Join-Path $root "acceptance_reports"
New-Item -ItemType Directory -Force -Path $reportDir | Out-Null
$report = Join-Path $reportDir ("MRL_acceptance_bridge_" + (Get-Date -Format "yyyyMMdd_HHmmss") + ".md")

function Add-Line($s) { $s | Out-File $report -Append -Encoding utf8; Write-Host $s }

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
  $client.Dispose()
  if (-not $response.IsSuccessStatusCode) { throw "upload HTTP $([int]$response.StatusCode): $text" }
  return $text | ConvertFrom-Json
}

Add-Line "# MRL 3DScanner Bridge Acceptance"
Add-Line "time: $(Get-Date -Format o)"
Add-Line ""

try {
  $h = Invoke-RestMethod -Uri "http://localhost:3050/api/health"
  if ($h.ok -ne $true) { throw "health ok flag false" }
  Add-Line "health: PASS"
} catch { Add-Line "health: FAIL $($_.Exception.Message)"; exit 1 }

$tmp = Join-Path $env:TEMP "mrl_bridge_cube.obj"
New-CubeObj $tmp

try {
  $r = Invoke-MRLUpload -Uri "http://localhost:3050/api/scans/upload" -FilePath $tmp -ScanId "acceptance_mesh" -ScanName "acceptance_mesh"
  Add-Line "upload: PASS uploaded=$($r.uploaded)"
} catch { Add-Line "upload: FAIL $($_.Exception.Message)"; exit 1 }

try {
  $body = @{ scanId="acceptance_mesh"; mode="auto" } | ConvertTo-Json
  $j = Invoke-RestMethod -Uri "http://localhost:3050/api/reconstruction/jobs" -Method POST -Body $body -ContentType "application/json"
  Add-Line "job_create: PASS jobId=$($j.jobId)"
} catch { Add-Line "job_create: FAIL $($_.Exception.Message)"; exit 1 }

$status = $null
for ($i = 0; $i -lt 30; $i++) {
  Start-Sleep -Seconds 2
  $status = Invoke-RestMethod -Uri "http://localhost:3050/api/reconstruction/jobs/$($j.jobId)"
  if ($status.status -eq "completed" -or $status.status -eq "failed") { break }
}

if ($status.status -eq "completed") {
  Add-Line "runner: PASS"
  Add-Line "reason: $($status.message)"
  Add-Line "created files: $($status.outputFiles -join ', ')"
  Add-Line "ACCEPTANCE PASS"
  exit 0
} else {
  Add-Line "runner: FAIL status=$($status.status)"
  Add-Line "failed reason: $($status.message)"
  Add-Line "created files: $($status.outputFiles -join ', ')"
  exit 1
}
