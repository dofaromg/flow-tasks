# MRL_DL580 自運行部署檢查 (Windows / PowerShell)
# origin_signature=MrLiouWord
# DL580 為 MRL 內部母體自運行主節點；GitHub/Cloud Code 為鏡像與建構器；APFS/Batch072 為部署/備份鏈，非母體本體。

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$MrlHome = if ($env:MRL_HOME) { $env:MRL_HOME } else { (Resolve-Path (Join-Path $ScriptDir "..")).Path }
$MrlPort = if ($env:MRL_PORT) { $env:MRL_PORT } else { "8790" }
$OriginSignature = "MrLiouWord"

Set-Location $MrlHome

Write-Host "MRL_DL580_DEPLOY_CHECK"
Write-Host "origin_signature=$OriginSignature"
Write-Host "MRL_HOME=$MrlHome"
Write-Host "target_port=$MrlPort"

$script:Fail = 0
function Pass($m) { Write-Host "PASS: $m" }
function Fail($m) { Write-Host "FAIL: $m"; $script:Fail = 1 }

# 1. Node version
$node = Get-Command node -ErrorAction SilentlyContinue
if ($node) { Pass "node runtime present ($(node --version))" } else { Fail "node runtime not found on DL580 node" }

# 2. package.json
if (Test-Path "package.json") { Pass "package.json present" } else { Fail "package.json missing" }

# 3. MRL_RuntimeServer.js
if (Test-Path "MRL_RuntimeServer.js") { Pass "MRL_RuntimeServer.js present" } else { Fail "MRL_RuntimeServer.js missing" }

# 4. required docs
$RequiredDocs = @(
  "docs/MRL_完整態主權宣示_v1.md",
  "docs/MRL_中文正名與英文Adapter對照表_v1.md",
  "docs/MRL_四層同步映射表_v1.md",
  "docs/MRL_CloudCode工程建構規格_v1.md",
  "docs/MRL_DL580自運行部署規格_v1.md"
)
foreach ($d in $RequiredDocs) {
  if (Test-Path $d) { Pass "doc present: $d" } else { Fail "doc missing: $d" }
}

# 5. deploy/dl580 scripts
$RequiredDeploy = @(
  "deploy/dl580/README.md",
  "deploy/dl580/MRL_dl580_start.sh",
  "deploy/dl580/MRL_dl580_start.ps1",
  "deploy/dl580/MRL_systemd_service.template",
  "deploy/dl580/MRL_selfhosted_runner_notes.md"
)
foreach ($f in $RequiredDeploy) {
  if (Test-Path $f) { Pass "deploy file present: $f" } else { Fail "deploy file missing: $f" }
}

# 6. (optional) Health
try {
  Invoke-WebRequest -UseBasicParsing -Uri "http://127.0.0.1:$MrlPort/health" -TimeoutSec 3 | Out-Null
  Write-Host "INFO: health=reachable"
} catch {
  Write-Host "INFO: health=not running (start with: pwsh deploy/dl580/MRL_dl580_start.ps1)"
}

if ($script:Fail -eq 0) {
  Write-Host "MRL_DL580_DEPLOY_CHECK_PASS"
  exit 0
} else {
  Write-Host "MRL_DL580_DEPLOY_CHECK_FAIL"
  exit 1
}
