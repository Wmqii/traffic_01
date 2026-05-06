param(
  [ValidateSet('dev', 'test', 'prod')]
  [string]$EnvName = 'dev'
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

. (Join-Path $PSScriptRoot 'common.ps1')

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

  try {
    if ($Method -eq 'POST') {
      $jsonBody = $Body | ConvertTo-Json -Depth 8
      $resp = Invoke-RestMethod -Method Post -Uri $Uri -Headers $headers -Body $jsonBody -ContentType 'application/json'
    } else {
      $resp = Invoke-RestMethod -Method Get -Uri $Uri -Headers $headers
    }
    return @{
      ok = $true
      status = 200
      body = $resp
    }
  } catch {
    $statusCode = -1
    $respBody = $null
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
      body = $respBody
    }
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

$checks = @()

$health = Invoke-JsonHttp -Method GET -Uri "$apiBase/health"
$checks += @{
  name = 'health'
  status = $health.status
  ok = ($health.status -eq 200)
}

$viewerLogin = Invoke-JsonHttp -Method POST -Uri "$apiBase/api/v1/auth/login" -Body @{
  username = 'viewer'
  password = 'viewer123'
}
$viewerToken = $null
if ($viewerLogin.status -eq 200 -and $viewerLogin.body.access_token) {
  $viewerToken = [string]$viewerLogin.body.access_token
}
$checks += @{
  name = 'login_viewer'
  status = $viewerLogin.status
  ok = ($viewerLogin.status -eq 200 -and $viewerToken)
}

$heat = Invoke-JsonHttp -Method GET -Uri "$apiBase/api/v1/map/layers/heat" -Token $viewerToken
$checks += @{
  name = 'heat_with_viewer'
  status = $heat.status
  ok = ($heat.status -eq 200)
}

$auditByViewer = Invoke-JsonHttp -Method GET -Uri "$apiBase/api/v1/admin/audit" -Token $viewerToken
$checks += @{
  name = 'admin_audit_forbidden_viewer'
  status = $auditByViewer.status
  ok = ($auditByViewer.status -eq 403)
}

$adminLogin = Invoke-JsonHttp -Method POST -Uri "$apiBase/api/v1/auth/login" -Body @{
  username = 'admin'
  password = 'admin123'
}
$adminToken = $null
if ($adminLogin.status -eq 200 -and $adminLogin.body.access_token) {
  $adminToken = [string]$adminLogin.body.access_token
}
$checks += @{
  name = 'login_admin'
  status = $adminLogin.status
  ok = ($adminLogin.status -eq 200 -and $adminToken)
}

$auditByAdmin = Invoke-JsonHttp -Method GET -Uri "$apiBase/api/v1/admin/audit" -Token $adminToken
$checks += @{
  name = 'admin_audit_with_admin'
  status = $auditByAdmin.status
  ok = ($auditByAdmin.status -eq 200)
}

$failedChecks = @($checks | Where-Object { -not $_.ok })
$passedChecks = @($checks | Where-Object { $_.ok })
$allPass = $failedChecks.Count -eq 0

$output = @{
  env = $EnvName
  api_base = $apiBase
  generated_at = (Get-Date).ToString('s')
  checks = $checks
  summary = @{
    pass = $allPass
    total = $checks.Count
    passed = $passedChecks.Count
  }
}

$artifact = Join-Path $root "ops/artifacts/o1_2_smoke_$EnvName.json"
Write-JsonFile -Path $artifact -Value $output
Write-Output "Smoke artifact: $artifact"
Write-Output ("Smoke summary: {0}/{1} pass" -f $output.summary.passed, $output.summary.total)

if (-not $allPass) {
  exit 1
}
