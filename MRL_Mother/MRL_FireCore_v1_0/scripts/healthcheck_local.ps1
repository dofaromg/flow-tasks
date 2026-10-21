param(
  [string]$Root = (Get-Location).Path
)

$ErrorActionPreference = "Stop"
$modules = Get-ChildItem -Path (Join-Path $Root "modules") -Directory | Sort-Object Name
foreach ($m in $modules) {
  $worker = Join-Path $m.FullName "src/index.ts"
  $schema = Get-ChildItem -Path (Join-Path $m.FullName "migrations") -Filter "*.sql" | Select-Object -First 1
  [pscustomobject]@{
    module = $m.Name
    worker_exists = Test-Path $worker
    schema_exists = [bool]$schema
    origin_signature_in_worker = if (Test-Path $worker) { Select-String -Path $worker -Pattern "MrLiouWord" -Quiet } else { $false }
    origin_signature_in_schema = if ($schema) { Select-String -Path $schema.FullName -Pattern "origin_signature" -Quiet } else { $false }
  }
}
