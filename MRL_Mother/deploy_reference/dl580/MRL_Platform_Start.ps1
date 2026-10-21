# MRL_Platform_Start.ps1 — DL580(Windows) 啟動 mrliouword.com 四功能平台
# origin_signature=MrLiouWord
# 啟動零依賴 Python 平台 MRL_Platform_Server.py（母體控制台/監控/API/對話），預設埠 8790。
# 與 MRL_cloudflared_deploy.ps1 -Hostname mrliouword.com 搭配對外上線。
# 網域可設：環境變數 MRL_PLATFORM_DOMAIN（預設 mrliouword.com；.ai 域不穩，先避開）。
$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$MrlHome = if ($env:MRL_HOME) { $env:MRL_HOME } else { (Resolve-Path (Join-Path $ScriptDir "..\..")).Path }
$MrlPort = if ($env:MRL_PORT) { $env:MRL_PORT } else { "8790" }
$env:MRL_PORT = $MrlPort
$MrlDomain = if ($env:MRL_PLATFORM_DOMAIN) { $env:MRL_PLATFORM_DOMAIN } else { "mrliouword.com" }
$env:MRL_PLATFORM_DOMAIN = $MrlDomain

Set-Location $MrlHome
Write-Host "MRL_PLATFORM_START | origin_signature=MrLiouWord"
Write-Host "node_role=DL580 母體自運行節點 | platform=$MrlDomain | MRL_HOME=$MrlHome | MRL_PORT=$MrlPort"

# C: 容量不足 → 一律導向 D:\。所有暫存/落盤(含 DL580 PersistentLoop)改寫到 D:\MRL_runtime。
$MrlDataRoot = if ($env:MRL_DATA_ROOT) { $env:MRL_DATA_ROOT } else { "D:\MRL_runtime" }
$MrlTmp = Join-Path $MrlDataRoot "tmp"
New-Item -ItemType Directory -Force -Path $MrlTmp | Out-Null
$env:MRL_DATA_ROOT = $MrlDataRoot
$env:TEMP = $MrlTmp        # Python tempfile.mkdtemp / DL580 runtime_dir 落 D:
$env:TMP  = $MrlTmp
Write-Host "資料/暫存導向 D:： MRL_DATA_ROOT=$MrlDataRoot ; TEMP=$MrlTmp (C: 不寫入)"

# 找 python（python / python3 / py）
$py = $null
foreach ($c in @("python", "python3", "py")) {
  if (Get-Command $c -ErrorAction SilentlyContinue) { $py = $c; break }
}
if (-not $py) { throw "找不到 Python。請安裝 Python 3.10+（平台為零依賴，無需 pip install）。" }

Write-Host "啟動四功能平台：$py MRL_Platform_Server.py (port $MrlPort)"
Write-Host "本地驗證： curl.exe http://localhost:$MrlPort/health"
& $py "MRL_Platform_Server.py"
