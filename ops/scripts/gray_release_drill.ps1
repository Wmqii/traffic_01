param(
  [ValidateSet('dev', 'test', 'prod')]
  [string]$EnvName = 'dev',
  [switch]$NoInstall
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

. (Join-Path $PSScriptRoot 'common.ps1')

function Get-Percentile {
  param(
    [double[]]$Values,
    [double]$P
  )
  if (-not $Values -or $Values.Count -eq 0) {
    return 0.0
  }
  $sorted = $Values | Sort-Object
  if ($sorted.Count -eq 1) {
    return [double]$sorted[0]
  }
  $rank = ($sorted.Count - 1) * ($P / 100.0)
  $low = [int][Math]::Floor($rank)
  $high = [Math]::Min($low + 1, $sorted.Count - 1)
  $weight = $rank - $low
  return (($sorted[$low] * (1.0 - $weight)) + ($sorted[$high] * $weight))
}

function Invoke-HealthProbe {
  param(
    [string]$ApiBase,
    [int]$Count = 30
  )
  $latencies = @()
  $ok = 0
  for ($i = 0; $i -lt $Count; $i++) {
    $sw = [System.Diagnostics.Stopwatch]::StartNew()
    $status = -1
    try {
      $resp = Invoke-RestMethod -Method Get -Uri "$ApiBase/health"
      if ($resp.status -eq 'ok') {
        $status = 200
      }
    } catch {
      $status = -1
    } finally {
      $sw.Stop()
      $ms = [Math]::Round($sw.Elapsed.TotalMilliseconds, 2)
      $latencies += $ms
    }
    if ($status -eq 200) {
      $ok += 1
    }
    Start-Sleep -Milliseconds 100
  }
  $successRate = if ($Count -gt 0) { [Math]::Round($ok / $Count, 4) } else { 0.0 }
  return [pscustomobject]@{
    count = $Count
    success = $ok
    success_rate = $successRate
    p95_ms = [Math]::Round((Get-Percentile -Values $latencies -P 95), 2)
    avg_ms = [Math]::Round((($latencies | Measure-Object -Average).Average), 2)
    max_ms = [Math]::Round((($latencies | Measure-Object -Maximum).Maximum), 2)
  }
}

function Invoke-BusinessProbe {
  param(
    [string]$ApiBase,
    [int]$Count = 20
  )
  $loginBody = @{ username = 'viewer'; password = 'viewer123' } | ConvertTo-Json
  $token = $null
  try {
    $loginResp = Invoke-RestMethod -Method Post -Uri "$ApiBase/api/v1/auth/login" -Body $loginBody -ContentType 'application/json'
    $token = [string]$loginResp.access_token
  } catch {
    return [pscustomobject]@{
      count = $Count
      success = 0
      success_rate = 0.0
      p95_ms = 0.0
      avg_ms = 0.0
      max_ms = 0.0
      login_ok = $false
    }
  }

  $latencies = @()
  $ok = 0
  $headers = @{ Authorization = "Bearer $token" }
  for ($i = 0; $i -lt $Count; $i++) {
    $sw = [System.Diagnostics.Stopwatch]::StartNew()
    $status = -1
    try {
      $resp = Invoke-RestMethod -Method Get -Uri "$ApiBase/api/v1/map/layers/heat" -Headers $headers
      if ($resp.layer_id) {
        $status = 200
      }
    } catch {
      $status = -1
    } finally {
      $sw.Stop()
      $ms = [Math]::Round($sw.Elapsed.TotalMilliseconds, 2)
      $latencies += $ms
    }
    if ($status -eq 200) {
      $ok += 1
    }
    Start-Sleep -Milliseconds 100
  }
  $successRate = if ($Count -gt 0) { [Math]::Round($ok / $Count, 4) } else { 0.0 }
  return [pscustomobject]@{
    count = $Count
    success = $ok
    success_rate = $successRate
    p95_ms = [Math]::Round((Get-Percentile -Values $latencies -P 95), 2)
    avg_ms = [Math]::Round((($latencies | Measure-Object -Average).Average), 2)
    max_ms = [Math]::Round((($latencies | Measure-Object -Maximum).Maximum), 2)
    login_ok = $true
  }
}

$root = Get-ProjectRoot
$envFile = Resolve-EnvFile -EnvName $EnvName
$envMap = Import-EnvFile -EnvFile $envFile

$apiHost = $envMap['API_HOST']
if ($apiHost -eq '0.0.0.0') {
  $apiHost = '127.0.0.1'
}
$apiPort = $envMap['API_PORT']
$apiBase = "http://$apiHost`:$apiPort"

$deployScript = Join-Path $PSScriptRoot 'deploy_env.ps1'
$startScript = Join-Path $PSScriptRoot 'start_env.ps1'
$stopScript = Join-Path $PSScriptRoot 'stop_env.ps1'
$smokeScript = Join-Path $PSScriptRoot 'smoke_api.ps1'
$monitorScript = Join-Path $PSScriptRoot 'monitoring_check.ps1'

$steps = @()
$drillPassed = $true

function Add-Step {
  param(
    [string]$Name,
    [bool]$Ok,
    [string]$Detail,
    [object]$Data = $null
  )
  $script:steps += [pscustomobject]@{
    name = $Name
    ok = $Ok
    detail = $Detail
    data = $Data
  }
  if (-not $Ok) {
    $script:drillPassed = $false
  }
}

try {
  # Step 1: baseline deploy (candidate rollout)
  if ($NoInstall) {
    & $deployScript -EnvName $EnvName -NoInstall | Out-Null
  } else {
    & $deployScript -EnvName $EnvName | Out-Null
  }
  if (-not $?) {
    throw "deploy_env failed"
  }
  Add-Step -Name 'candidate_deploy' -Ok $true -Detail "deploy_env completed for $EnvName"

  # Step 2: monitoring check after candidate rollout
  & $monitorScript -EnvName $EnvName | Out-Null
  if (-not $?) {
    throw "monitoring_check failed after candidate deploy"
  }
  Add-Step -Name 'candidate_monitoring_check' -Ok $true -Detail 'monitoring baseline pass'

  # Step 3: canary probe (simulate canary window)
  $healthProbe = Invoke-HealthProbe -ApiBase $apiBase -Count 30
  $bizProbe = Invoke-BusinessProbe -ApiBase $apiBase -Count 20
  $canaryOk = ($healthProbe.success_rate -ge 0.99) -and ($healthProbe.p95_ms -lt 1000) -and ($bizProbe.success_rate -ge 0.99) -and ($bizProbe.p95_ms -lt 1000)
  Add-Step -Name 'canary_probe' -Ok $canaryOk -Detail "health_p95=$($healthProbe.p95_ms), biz_p95=$($bizProbe.p95_ms)" -Data @{
    health = $healthProbe
    business = $bizProbe
    thresholds = @{
      success_rate_ge = 0.99
      p95_ms_lt = 1000
    }
  }

  # Step 4: rollback drill (stop + restore + smoke + monitor)
  & $stopScript -EnvName $EnvName | Out-Null
  if ($NoInstall) {
    & $startScript -EnvName $EnvName -NoInstall | Out-Null
  } else {
    & $startScript -EnvName $EnvName | Out-Null
  }
  & $smokeScript -EnvName $EnvName | Out-Null
  & $monitorScript -EnvName $EnvName | Out-Null
  $rollbackOk = $?
  Add-Step -Name 'rollback_restore_validation' -Ok $rollbackOk -Detail 'stop/start + smoke + monitoring completed'
} catch {
  Add-Step -Name 'drill_exception' -Ok $false -Detail $_.Exception.Message
} finally {
  # Keep environment clean after drill
  try {
    & $stopScript -EnvName $EnvName | Out-Null
  } catch {
    # ignore cleanup errors
  }
}

$summary = [pscustomobject]@{
  pass = $drillPassed
  total_steps = $steps.Count
  passed_steps = @($steps | Where-Object { $_.ok }).Count
  failed_steps = @($steps | Where-Object { -not $_.ok }).Count
}

$output = [pscustomobject]@{
  env = $EnvName
  generated_at = (Get-Date).ToString('s')
  api_base = $apiBase
  release_plan = @{
    strategy = 'canary_simulation'
    phases = @('candidate_deploy', 'monitor', 'canary_probe', 'rollback_restore_validation')
    rollback_trigger = 'canary success_rate<99% or p95>=1000ms or monitoring critical alert'
  }
  steps = $steps
  summary = $summary
}

$artifact = Join-Path $root "ops/artifacts/o1_4_gray_release_drill_$EnvName.json"
Write-JsonFile -Path $artifact -Value $output
Write-Output "Gray drill artifact: $artifact"
Write-Output ("Gray drill summary: pass={0}, passed_steps={1}/{2}" -f $summary.pass, $summary.passed_steps, $summary.total_steps)

if (-not $summary.pass) {
  exit 1
}

