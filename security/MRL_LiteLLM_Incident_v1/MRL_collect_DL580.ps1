<# Read-only local evidence collection. NO Python/pip/container start/pull/exec.
   Run in PowerShell on DL580. Output contains local paths: keep it private.
   Supply explicit roots for installations, caches, deployments and archived SBOMs.
#>
[CmdletBinding()]
param(
  [Parameter(Mandatory=$true)][string[]]$Roots,
  [Parameter(Mandatory=$true)][string]$OutputDirectory
)
$ErrorActionPreference = 'Stop'
$policy = Get-Content -LiteralPath (Join-Path $PSScriptRoot 'policy.json') -Raw | ConvertFrom-Json
if (Test-Path -LiteralPath $OutputDirectory) { throw 'Evidence directory must be new; preserve prior evidence.' }
$outputFull = [IO.Path]::GetFullPath($OutputDirectory).TrimEnd('\')
foreach ($root in $Roots) {
  $rootFull = [IO.Path]::GetFullPath($root).TrimEnd('\')
  if ($outputFull.Equals($rootFull, [StringComparison]::OrdinalIgnoreCase) -or
      $outputFull.StartsWith($rootFull + '\', [StringComparison]::OrdinalIgnoreCase)) {
    throw 'Output directory must be outside all scan roots.'
  }
}
New-Item -ItemType Directory -Path $OutputDirectory | Out-Null
$records = [Collections.Generic.List[object]]::new()
$gaps = [Collections.Generic.List[object]]::new()
function Walk-Static([string]$Directory) {
  try { $children = @(Get-ChildItem -LiteralPath $Directory -Force -ErrorAction Stop) }
  catch { $gaps.Add(@{path=$Directory;reason='unreadable_directory'}); return }
  foreach ($item in $children) {
    if ($item.Attributes -band [IO.FileAttributes]::ReparsePoint) {
      $gaps.Add(@{path=$item.FullName;reason='reparse_point_not_followed'}); continue
    }
    if ($item.PSIsContainer) {
      if ($item.Name -eq 'litellm-1.107.0.dist-info') {
        $records.Add(@{path=$item.FullName;state='HIT';rule='affected_installed_metadata_directory'})
      }
      Walk-Static $item.FullName
    } else {
      # Hash selected metadata, wheels and startup hooks; never print their contents.
      if ($item.Name -match '(?i)litellm|\.whl$|\.tar\.gz$|^\.pc_once_|^remote_code_loader\.lock$|^cook\.(pth|py)$|^sitecustomize\.py$|^(cook|sitecustomize).*\.pyc$|^METADATA$|requirements|lock$|Dockerfile|compose|sbom|deploy') {
        try {
          $hash = (Get-FileHash -LiteralPath $item.FullName -Algorithm SHA256).Hash.ToLowerInvariant()
          $state = if ($item.Name -match '(?i)litellm[-_]1\.107\.0([.-]|$)') {'HIT'} else {'UNKNOWN'}
          if ($policy.bad_file_sha256 -contains $hash) { $state = 'HIT' }
          if ($item.Name -eq 'METADATA') {
            $metadata = Get-Content -LiteralPath $item.FullName -Raw
            if ($metadata -match '(?im)^Name:\s*litellm\s*$' -and $metadata -match '(?im)^Version:\s*1\.107\.0\s*$') { $state = 'HIT' }
          }
          $records.Add(@{path=$item.FullName;size=$item.Length;sha256=$hash;state=$state;rule='static_file_inventory';last_write_utc=$item.LastWriteTimeUtc.ToString('o')})
        } catch { $gaps.Add(@{path=$item.FullName;reason='hash_failed'}) }
      }
    }
  }
}
foreach ($root in $Roots) {
  if ((Test-Path -LiteralPath $root -PathType Container) -and -not ((Get-Item -LiteralPath $root -Force).Attributes -band [IO.FileAttributes]::ReparsePoint)) { Walk-Static $root }
  else { $gaps.Add(@{path=$root;reason='root_unavailable'}) }
}
$docker = @()
if (Get-Command docker -ErrorAction SilentlyContinue) {
  # Select only image identity. NEVER dump inspect Env, mounts, labels or credentials.
  $docker = @(& docker image ls --no-trunc --digests --format '{{json .}}' 2>$null)
  if ($LASTEXITCODE -ne 0) { $gaps.Add(@{reason='docker_inventory_failed'}) }
  $containers = @(& docker ps -aq 2>$null)
  if ($LASTEXITCODE -ne 0) { $gaps.Add(@{reason='container_listing_failed'}) }
  foreach ($container in $containers) {
    $docker += @(& docker container inspect --format '{{.Id}} {{.Image}} {{.Config.Image}} {{.Created}}' $container 2>$null)
    if ($LASTEXITCODE -ne 0) { $gaps.Add(@{reason='container_identity_failed'}) }
  }
} else { $gaps.Add(@{reason='docker_not_available'}) }
$overall = 'UNKNOWN'
if (@($records.ToArray() | Where-Object {$_.state -eq 'HIT'}).Count -gt 0) { $overall = 'HIT' }
foreach ($line in $docker) {
  foreach ($prefix in $policy.bad_digest_prefixes) {
    if ($line -match ('(?i)sha256:' + [regex]::Escape($prefix))) { $overall = 'HIT' }
  }
}
$report = @{schema='MRL_DL580_LiteLLM_Static_Inventory/v1.0.0';origin_signature='MrLiouWord';created_utc=[DateTime]::UtcNow.ToString('o');roots=$Roots;files=$records.ToArray();gaps=$gaps.ToArray();runtime_execution_verified=$false;state=$overall}
$report | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath (Join-Path $OutputDirectory 'MRL_inventory.json') -Encoding UTF8
$docker | Set-Content -LiteralPath (Join-Path $OutputDirectory 'MRL_docker_identity.txt') -Encoding UTF8
Get-ChildItem -LiteralPath $OutputDirectory -File | Get-FileHash -Algorithm SHA256 |
  Select-Object Path,Hash | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $OutputDirectory 'MRL_evidence_hashes.json') -Encoding UTF8
Write-Output ('Static inventory saved locally. State=' + $overall + '; execution history still unverified.')
