param(
  [ValidateSet('dev', 'test', 'prod')]
  [string]$EnvName = 'dev',
  [switch]$FailOnWarning
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

. (Join-Path $PSScriptRoot 'common.ps1')

function Add-Alert {
  param(
    [ref]$Alerts,
    [ValidateSet('warning', 'critical')]
    [string]$Severity,
    [string]$Code,
    [string]$Message,
    [string]$Source
  )
  $Alerts.Value += [pscustomobject]@{
    severity = $Severity
    code = $Code
    message = $Message
    source = $Source
  }
}

function Add-Check {
  param(
    [ref]$Checks,
    [string]$Name,
    [bool]$Ok,
    [object]$Value,
    [object]$Threshold = $null
  )
  $Checks.Value += [pscustomobject]@{
    name = $Name
    ok = $Ok
    value = $Value
    threshold = $Threshold
  }
}

function Invoke-JsonHttp {
  param(
    [Parameter(Mandatory = $true)]
    [ValidateSet('GET', 'POST')]
    [string]$Method,
    [Parameter(Mandatory = $true)]
    [string]$Uri,
    [object]$Body,
    [string]$Token
  )

  $headers = @{}
  if ($Token) {
    $headers['Authorization'] = "Bearer $Token"
  }

  $sw = [System.Diagnostics.Stopwatch]::StartNew()
  try {
    if ($Method -eq 'POST') {
      $jsonBody = $Body | ConvertTo-Json -Depth 8
      $resp = Invoke-RestMethod -Method Post -Uri $Uri -Headers $headers -Body $jsonBody -ContentType 'application/json'
    } else {
      $resp = Invoke-RestMethod -Method Get -Uri $Uri -Headers $headers
    }
    $sw.Stop()
    return @{
      ok = $true
      status = 200
      body = $resp
      latency_ms = [Math]::Round($sw.Elapsed.TotalMilliseconds, 2)
    }
  } catch {
    $sw.Stop()
    $statusCode = -1
    if ($_.Exception.Response) {
      try {
        $statusCode = [int]$_.Exception.Response.StatusCode
      } catch {
        $statusCode = -1
      }
    }
    return @{
      ok = $false
      status = $statusCode
      body = $null
      latency_ms = [Math]::Round($sw.Elapsed.TotalMilliseconds, 2)
    }
  }
}

$root = Get-ProjectRoot
$envFile = Resolve-EnvFile -EnvName $EnvName
$envMap = Import-EnvFile -EnvFile $envFile
$rulesPath = Join-Path $root 'ops/monitoring/alert_rules.json'
$rules = Get-Content -LiteralPath $rulesPath -Encoding UTF8 | ConvertFrom-Json

$checks = @()
$alerts = @()

$runtimeFile = Get-RuntimeFile -EnvName $EnvName
$runtimeExists = Test-Path -LiteralPath $runtimeFile
Add-Check -Checks ([ref]$checks) -Name 'runtime_file_exists' -Ok $runtimeExists -Value $runtimeExists
if (-not $runtimeExists) {
  Add-Alert -Alerts ([ref]$alerts) -Severity warning -Code 'runtime.missing' -Message "Runtime file missing: $runtimeFile" -Source 'system'
}

$apiHost = $envMap['API_HOST']
if ($apiHost -eq '0.0.0.0') {
  $apiHost = '127.0.0.1'
}
$apiPort = $envMap['API_PORT']
$apiBase = "http://$apiHost`:$apiPort"

if ($runtimeExists) {
  $runtime = Get-Content -LiteralPath $runtimeFile -Encoding UTF8 | ConvertFrom-Json
  foreach ($procInfo in @(
      @{ name = 'backend_process_alive'; pid = $runtime.backend_pid },
      @{ name = 'frontend_process_alive'; pid = $runtime.frontend_pid }
    )) {
    $alive = $false
    try {
      $p = Get-Process -Id ([int]$procInfo.pid) -ErrorAction Stop
      $alive = $null -ne $p
    } catch {
      $alive = $false
    }
    Add-Check -Checks ([ref]$checks) -Name $procInfo.name -Ok $alive -Value $procInfo.pid
    if (-not $alive) {
      Add-Alert -Alerts ([ref]$alerts) -Severity critical -Code 'process.down' -Message "$($procInfo.name) pid=$($procInfo.pid) not alive" -Source 'system'
    }
  }
}

# Application checks
$health = Invoke-JsonHttp -Method GET -Uri "$apiBase/health"
$healthOk = ($health.status -eq 200)
Add-Check -Checks ([ref]$checks) -Name 'health_200' -Ok $healthOk -Value $health.status
if (-not $healthOk) {
  Add-Alert -Alerts ([ref]$alerts) -Severity critical -Code 'app.health.unavailable' -Message "Health endpoint status=$($health.status)" -Source 'application'
}

Add-Check -Checks ([ref]$checks) -Name 'health_latency_ms' -Ok $true -Value $health.latency_ms -Threshold $rules.health_response_ms_warn
if ($health.latency_ms -ge $rules.health_response_ms_critical) {
  Add-Alert -Alerts ([ref]$alerts) -Severity critical -Code 'app.health.latency.critical' -Message "Health latency $($health.latency_ms)ms >= $($rules.health_response_ms_critical)ms" -Source 'application'
} elseif ($health.latency_ms -ge $rules.health_response_ms_warn) {
  Add-Alert -Alerts ([ref]$alerts) -Severity warning -Code 'app.health.latency.warn' -Message "Health latency $($health.latency_ms)ms >= $($rules.health_response_ms_warn)ms" -Source 'application'
}

$viewerLogin = Invoke-JsonHttp -Method POST -Uri "$apiBase/api/v1/auth/login" -Body @{
  username = 'viewer'
  password = 'viewer123'
}
$viewerToken = $null
if ($viewerLogin.status -eq 200 -and $viewerLogin.body.access_token) {
  $viewerToken = [string]$viewerLogin.body.access_token
}
Add-Check -Checks ([ref]$checks) -Name 'login_viewer_200' -Ok ($viewerLogin.status -eq 200) -Value $viewerLogin.status
if (-not $viewerToken) {
  Add-Alert -Alerts ([ref]$alerts) -Severity critical -Code 'app.auth.login_failed' -Message 'viewer login failed' -Source 'application'
}

$heat = Invoke-JsonHttp -Method GET -Uri "$apiBase/api/v1/map/layers/heat" -Token $viewerToken
Add-Check -Checks ([ref]$checks) -Name 'map_heat_200' -Ok ($heat.status -eq 200) -Value $heat.status
if ($heat.status -ne 200) {
  Add-Alert -Alerts ([ref]$alerts) -Severity critical -Code 'app.map.heat_failed' -Message "map heat status=$($heat.status)" -Source 'application'
}

# Model checks
$metricsPath = Join-Path $root 'model/deep/output/metrics.json'
$metricsExists = Test-Path -LiteralPath $metricsPath
Add-Check -Checks ([ref]$checks) -Name 'model_metrics_exists' -Ok $metricsExists -Value $metricsPath
if (-not $metricsExists) {
  Add-Alert -Alerts ([ref]$alerts) -Severity critical -Code 'model.metrics.missing' -Message 'model/deep/output/metrics.json missing' -Source 'model'
}

if ($metricsExists) {
  $metrics = Get-Content -LiteralPath $metricsPath -Encoding UTF8 | ConvertFrom-Json
  $gruMape = [double]$metrics.models.gru.metrics.mape
  $lstmMape = [double]$metrics.models.lstm.metrics.mape
  $bestMape = [Math]::Min($gruMape, $lstmMape)

  Add-Check -Checks ([ref]$checks) -Name 'model_best_mape' -Ok $true -Value ([Math]::Round($bestMape, 4)) -Threshold $rules.model_mape_warn
  if ($bestMape -ge $rules.model_mape_critical) {
    Add-Alert -Alerts ([ref]$alerts) -Severity critical -Code 'model.mape.critical' -Message "best_mape=$bestMape >= $($rules.model_mape_critical)" -Source 'model'
  } elseif ($bestMape -ge $rules.model_mape_warn) {
    Add-Alert -Alerts ([ref]$alerts) -Severity warning -Code 'model.mape.warn' -Message "best_mape=$bestMape >= $($rules.model_mape_warn)" -Source 'model'
  }

  $lastWrite = (Get-Item -LiteralPath $metricsPath).LastWriteTimeUtc
  $ageHours = [Math]::Round(((Get-Date).ToUniversalTime() - $lastWrite).TotalHours, 2)
  Add-Check -Checks ([ref]$checks) -Name 'model_metrics_age_hours' -Ok ($ageHours -le $rules.model_metrics_max_age_hours) -Value $ageHours -Threshold $rules.model_metrics_max_age_hours
  if ($ageHours -gt $rules.model_metrics_max_age_hours) {
    Add-Alert -Alerts ([ref]$alerts) -Severity warning -Code 'model.metrics.stale' -Message "metrics age $ageHours h > $($rules.model_metrics_max_age_hours) h" -Source 'model'
  }
}

# Log checks
$logDir = Join-Path $root $envMap['LOG_DIR']
$backendErr = Join-Path $logDir 'backend.err.log'
$errLineCount = 0
if (Test-Path -LiteralPath $backendErr) {
  $errLineCount = (Get-Content -LiteralPath $backendErr -Encoding UTF8 | Measure-Object -Line).Lines
}
Add-Check -Checks ([ref]$checks) -Name 'backend_err_log_lines' -Ok $true -Value $errLineCount -Threshold $rules.backend_err_log_warn_lines
if ($errLineCount -ge $rules.backend_err_log_critical_lines) {
  Add-Alert -Alerts ([ref]$alerts) -Severity critical -Code 'logs.backend_err.critical' -Message "backend.err.log lines=$errLineCount >= $($rules.backend_err_log_critical_lines)" -Source 'system'
} elseif ($errLineCount -ge $rules.backend_err_log_warn_lines) {
  Add-Alert -Alerts ([ref]$alerts) -Severity warning -Code 'logs.backend_err.warn' -Message "backend.err.log lines=$errLineCount >= $($rules.backend_err_log_warn_lines)" -Source 'system'
}

$criticalCount = @($alerts | Where-Object { $_.severity -eq 'critical' }).Count
$warningCount = @($alerts | Where-Object { $_.severity -eq 'warning' }).Count
$pass = $criticalCount -eq 0
if ($FailOnWarning) {
  $pass = $pass -and ($warningCount -eq 0)
}

$output = [pscustomobject]@{
  env = $EnvName
  generated_at = (Get-Date).ToString('s')
  api_base = $apiBase
  checks = $checks
  alerts = $alerts
  summary = [pscustomobject]@{
    pass = $pass
    total_checks = $checks.Count
    critical_alerts = $criticalCount
    warning_alerts = $warningCount
  }
}

$artifact = Join-Path $root "ops/artifacts/o1_3_monitor_$EnvName.json"
Write-JsonFile -Path $artifact -Value $output

$dashboard = [pscustomobject]@{
  title = [pscustomobject]@{ text = "O1-3 Monitor ($EnvName)" }
  tooltip = [pscustomobject]@{ trigger = 'item' }
  legend = [pscustomobject]@{ top = 24 }
  xAxis = [pscustomobject]@{
    type = 'category'
    data = @('critical_alerts', 'warning_alerts', 'total_checks')
  }
  yAxis = [pscustomobject]@{ type = 'value' }
  series = @(
    [pscustomobject]@{
      name = 'count'
      type = 'bar'
      data = @($criticalCount, $warningCount, $checks.Count)
      itemStyle = [pscustomobject]@{
        color = '#1f78b4'
      }
    }
  )
}
$dashboardPath = Join-Path $root "ops/artifacts/o1_3_monitor_dashboard_$EnvName.json"
Write-JsonFile -Path $dashboardPath -Value $dashboard

Write-Output "Monitor artifact: $artifact"
Write-Output "Dashboard config: $dashboardPath"
Write-Output ("Monitor summary: pass={0}, critical={1}, warning={2}, checks={3}" -f $pass, $criticalCount, $warningCount, $checks.Count)

if (-not $pass) {
  exit 1
}

