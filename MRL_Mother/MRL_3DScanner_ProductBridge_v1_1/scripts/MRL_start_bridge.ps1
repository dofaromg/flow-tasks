$root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$backend = Join-Path $root "backend\MRL_3D_Reconstruction_Server"
$log = Join-Path $root "start.log"
"[MRL] start $(Get-Date -Format o)" | Out-File $log -Encoding utf8
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$backend'; `$env:MRL_3D_BRIDGE_PORT='3050'; node server.js" -WindowStyle Normal
Start-Sleep -Seconds 2
try { Invoke-WebRequest -Uri "http://localhost:3050/api/health" -UseBasicParsing | Tee-Object -FilePath $log -Append } catch { $_ | Out-File $log -Append; throw }
"START PASS" | Tee-Object -FilePath $log -Append
