param(
  [ValidateSet('dev', 'test', 'prod')]
  [string]$EnvName = 'dev',
  [switch]$NoInstall
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

. (Join-Path $PSScriptRoot 'common.ps1')

function Add-Step {
  param(
    [ref]$Steps,
    [string]$Name,
    [bool]$Ok,
    [string]$Detail,
    [object]$Data = $null
  )
  $Steps.Value += [pscustomobject]@{
    name = $Name
    ok = $Ok
    detail = $Detail
    data = $Data
  }
}

function Test-HealthUnavailable {
  param(
    [string]$ApiBase
  )
  try {
    $null = Invoke-RestMethod -Method Get -Uri "$ApiBase/health"
    return $false
  } catch {
    return $true
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
$grayScript = Join-Path $PSScriptRoot 'gray_release_drill.ps1'

$steps = @()
$drillPass = $true
$incidentStart = $null
$incidentRecoveredAt = $null
$mttrSeconds = $null

try {
  if ($NoInstall) {
    & $deployScript -EnvName $EnvName -NoInstall -SkipSmoke | Out-Null
  } else {
    & $deployScript -EnvName $EnvName -SkipSmoke | Out-Null
  }
  Add-Step -Steps ([ref]$steps) -Name 'baseline_deploy' -Ok $true -Detail "deploy_env finished for $EnvName"

  & $smokeScript -EnvName $EnvName | Out-Null
  Add-Step -Steps ([ref]$steps) -Name 'baseline_smoke' -Ok $true -Detail 'smoke check passed'

  & $monitorScript -EnvName $EnvName | Out-Null
  Add-Step -Steps ([ref]$steps) -Name 'baseline_monitoring' -Ok $true -Detail 'monitoring check passed'

  if ($NoInstall) {
    & $grayScript -EnvName $EnvName -NoInstall | Out-Null
  } else {
    & $grayScript -EnvName $EnvName | Out-Null
  }
  $grayArtifact = Join-Path $root "ops/artifacts/o1_4_gray_release_drill_$EnvName.json"
  $grayPass = $false
  if (Test-Path -LiteralPath $grayArtifact) {
    $grayResult = Get-Content -LiteralPath $grayArtifact -Encoding UTF8 | ConvertFrom-Json
    $grayPass = [bool]$grayResult.summary.pass
  }
  Add-Step -Steps ([ref]$steps) -Name 'gray_release_drill' -Ok $grayPass -Detail "gray drill summary pass=$grayPass" -Data @{
    artifact = $grayArtifact
  }

  $incidentStart = Get-Date
  & $stopScript -EnvName $EnvName | Out-Null
  $detected = Test-HealthUnavailable -ApiBase $apiBase
  Add-Step -Steps ([ref]$steps) -Name 'incident_detection' -Ok $detected -Detail "health unavailable detected=$detected"

  if ($NoInstall) {
    & $startScript -EnvName $EnvName -NoInstall | Out-Null
  } else {
    & $startScript -EnvName $EnvName | Out-Null
  }
  & $smokeScript -EnvName $EnvName | Out-Null
  & $monitorScript -EnvName $EnvName | Out-Null
  $incidentRecoveredAt = Get-Date
  $mttrSeconds = [Math]::Round(($incidentRecoveredAt - $incidentStart).TotalSeconds, 2)
  Add-Step -Steps ([ref]$steps) -Name 'incident_recovery' -Ok $true -Detail "start+smoke+monitor finished, mttr=${mttrSeconds}s" -Data @{
    mttr_seconds = $mttrSeconds
  }

  $slo = 300.0
  $mttrOk = $mttrSeconds -le $slo
  Add-Step -Steps ([ref]$steps) -Name 'incident_mttr_slo' -Ok $mttrOk -Detail "mttr=${mttrSeconds}s, slo<=${slo}s"
} catch {
  Add-Step -Steps ([ref]$steps) -Name 'runbook_exception' -Ok $false -Detail $_.Exception.Message
} finally {
  try {
    & $stopScript -EnvName $EnvName | Out-Null
  } catch {
    # ignore cleanup errors
  }
}

$failedCount = @($steps | Where-Object { -not $_.ok }).Count
$drillPass = $failedCount -eq 0

$summary = [pscustomobject]@{
  pass = $drillPass
  total_steps = $steps.Count
  passed_steps = @($steps | Where-Object { $_.ok }).Count
  failed_steps = $failedCount
}

$output = [pscustomobject]@{
  env = $EnvName
  generated_at = (Get-Date).ToString('s')
  api_base = $apiBase
  runbook = @{
    docs = @(
      'ops/runbooks/o1_5_runbook_v1.0.md',
      'ops/runbooks/o1_5_incident_plan_v1.0.md'
    )
    mttr_slo_seconds = 300
  }
  incident = @{
    started_at = if ($incidentStart) { $incidentStart.ToString('s') } else { $null }
    recovered_at = if ($incidentRecoveredAt) { $incidentRecoveredAt.ToString('s') } else { $null }
    mttr_seconds = $mttrSeconds
  }
  steps = $steps
  summary = $summary
}

$artifact = Join-Path $root "ops/artifacts/o1_5_runbook_drill_$EnvName.json"
Write-JsonFile -Path $artifact -Value $output
Write-Output "Runbook drill artifact: $artifact"
Write-Output ("Runbook drill summary: pass={0}, passed_steps={1}/{2}" -f $summary.pass, $summary.passed_steps, $summary.total_steps)

if (-not $summary.pass) {
  exit 1
}

