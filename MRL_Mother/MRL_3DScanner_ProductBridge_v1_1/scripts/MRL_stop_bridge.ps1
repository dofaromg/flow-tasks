Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -like "*MRL_3D_Reconstruction_Server*" -and $_.Name -like "node*" } | ForEach-Object { Stop-Process -Id $_.ProcessId -Force }
"STOP PASS"
