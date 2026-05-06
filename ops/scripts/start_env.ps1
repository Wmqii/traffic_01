param(
  [ValidateSet('dev', 'test', 'prod')]
  [string]$EnvName = 'dev',
  [switch]$NoInstall
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

. (Join-Path $PSScriptRoot 'common.ps1')

$root = Get-ProjectRoot
$envFile = Resolve-EnvFile -EnvName $EnvName
$envMap = Import-EnvFile -EnvFile $envFile

if (-not $NoInstall) {
  python -m pip install fastapi uvicorn pydantic pyjwt | Out-Null
}

$logDir = Join-Path $root $envMap['LOG_DIR']
if (-not (Test-Path -LiteralPath $logDir)) {
  New-Item -ItemType Directory -Path $logDir -Force | Out-Null
}

$backendOut = Join-Path $logDir 'backend.out.log'
$backendErr = Join-Path $logDir 'backend.err.log'
$frontendOut = Join-Path $logDir 'frontend.out.log'
$frontendErr = Join-Path $logDir 'frontend.err.log'

$apiHost = $envMap['API_HOST']
$apiPort = $envMap['API_PORT']
$frontendPort = $envMap['FRONTEND_PORT']

$backendArgs = @('-m', 'uvicorn', 'backend.app:app', '--host', $apiHost, '--port', $apiPort)
$frontendArgs = @('-m', 'http.server', $frontendPort, '--directory', 'frontend')

$backend = Start-Process -FilePath 'python' -ArgumentList $backendArgs -WorkingDirectory $root -PassThru -WindowStyle Hidden -RedirectStandardOutput $backendOut -RedirectStandardError $backendErr
$frontend = Start-Process -FilePath 'python' -ArgumentList $frontendArgs -WorkingDirectory $root -PassThru -WindowStyle Hidden -RedirectStandardOutput $frontendOut -RedirectStandardError $frontendErr

$runtimeFile = Get-RuntimeFile -EnvName $EnvName
Write-JsonFile -Path $runtimeFile -Value @{
  env = $EnvName
  started_at = (Get-Date).ToString('s')
  backend_pid = $backend.Id
  frontend_pid = $frontend.Id
  api_url = "http://$apiHost`:$apiPort"
  frontend_url = "http://127.0.0.1:$frontendPort"
  log_dir = $logDir
}

Start-Sleep -Seconds 2
Write-Output "Started $EnvName"
Write-Output "API: http://$apiHost`:$apiPort"
Write-Output "Frontend: http://127.0.0.1:$frontendPort"
Write-Output "Runtime: $runtimeFile"
