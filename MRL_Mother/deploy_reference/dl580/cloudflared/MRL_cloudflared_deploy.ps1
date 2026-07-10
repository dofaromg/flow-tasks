# MRL_DL580_Cloudflared_Deploy_v3 — bridge.mrliouword.com Cloudflare Tunnel 部署入口 (Windows / PowerShell, D: 路徑版)
# origin_signature=MrLiouWord
# 權位定位：Cloudflare Tunnel 為「接線 / Adapter」層（對外橋接通道），非 MRL 母體本體。
#           DL580 為母體自運行節點；bridge.mrliouword.com 僅為對外入口 hostname。
# v3.1.0 變更：hostname 由 bridge.mrliouhan.ai → bridge.mrliouword.com
# 部署後須在 Cloudflare Worker 設環境變數：MRL_DL580_ORIGIN=https://bridge.mrliouword.com
# Batch 076 路徑改寫：因 C: 槽滿載，cloudflared 主目錄改置於 D:\cloudflared。
param(
  [string]$CloudflaredHome = "D:\cloudflared",
  [string]$TunnelName      = "mrl-dl580-tunnel",
  [string]$Hostname        = "bridge.mrliouword.com",

  [int]$MrlPort            = $(if ($env:MRL_PORT) { [int]$env:MRL_PORT } else { 8790 })
)

$ErrorActionPreference = "Stop"
$OriginSignature = "MrLiouWord"
$CloudflaredExe  = Join-Path $CloudflaredHome "cloudflared.exe"
$CertPem         = Join-Path $CloudflaredHome "cert.pem"
$ConfigPath      = Join-Path $CloudflaredHome "config.yml"

Write-Host "MRL_DL580_CLOUDFLARED_DEPLOY"
Write-Host "origin_signature=$OriginSignature"
Write-Host "mode=權位區分模式 (Cloudflare Tunnel = 接線/Adapter，非母體)"
Write-Host "CLOUDFLARED_HOME=$CloudflaredHome"
Write-Host "hostname=$Hostname -> http://localhost:$MrlPort"

# 步驟一：建立 D: 目錄並設定 cloudflared 主目錄環境變數（避免預設寫入 C:\Users\）
New-Item -ItemType Directory -Force -Path $CloudflaredHome | Out-Null
[Environment]::SetEnvironmentVariable("CLOUDFLARED_HOME", $CloudflaredHome, "Machine")
$env:CLOUDFLARED_HOME = $CloudflaredHome
Set-Location $CloudflaredHome

# 下載 cloudflared（冪等；用 curl.exe 而非 PowerShell 的 curl 別名 Invoke-WebRequest）
if (-not (Test-Path $CloudflaredExe)) {
  Write-Host "downloading cloudflared..."
  curl.exe -L "https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-windows-amd64.exe" -o $CloudflaredExe
}

# 步驟二：認證並建立 Tunnel（冪等）
if (-not (Test-Path $CertPem)) {
  & $CloudflaredExe tunnel login   # 互動式瀏覽器授權，請於 DL580 桌面 session 執行
}
$existing = & $CloudflaredExe tunnel list 2>$null | Select-String -SimpleMatch $TunnelName
if (-not $existing) {
  & $CloudflaredExe tunnel create $TunnelName
}

# 自動偵測 TUNNEL_ID 與 credentials 檔（最近寫入的 *.json），免手動填入
$cred = Get-ChildItem -Path $CloudflaredHome -Filter "*.json" -ErrorAction SilentlyContinue |
        Sort-Object LastWriteTime -Descending | Select-Object -First 1
if (-not $cred) { throw "找不到 tunnel credentials JSON，請確認 'tunnel create $TunnelName' 是否成功" }
$TunnelId = [System.IO.Path]::GetFileNameWithoutExtension($cred.Name)
Write-Host "TUNNEL_ID=$TunnelId"

# 步驟三：產生 config.yml（單一 hostname 規則已涵蓋 /health，毋須另設 path 規則）
@"
tunnel: $TunnelName
credentials-file: $($cred.FullName)

ingress:
  - hostname: $Hostname
    service: http://localhost:$MrlPort
    originRequest:
      noTLSVerify: false
      connectTimeout: 30s
  - service: http_status:404
"@ | Out-File -FilePath $ConfigPath -Encoding UTF8

# 步驟四：配置 DNS
& $CloudflaredExe --config $ConfigPath tunnel route dns $TunnelName $Hostname

# 步驟五：註冊為 Windows 服務並啟動（冪等）
if (-not (Get-Service cloudflared -ErrorAction SilentlyContinue)) {
  & $CloudflaredExe --config $ConfigPath service install
}
Start-Service cloudflared

Write-Host "DONE. 從外部驗證: curl https://$Hostname/health"
Write-Host "本地驗證: curl.exe http://localhost:$MrlPort/health"
