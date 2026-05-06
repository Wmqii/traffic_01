param(
  [ValidateSet('dev', 'test', 'prod')]
  [string]$EnvName = 'dev'
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

. (Join-Path $PSScriptRoot 'common.ps1')

$runtimeFile = Get-RuntimeFile -EnvName $EnvName
if (-not (Test-Path -LiteralPath $runtimeFile)) {
  Write-Output "Runtime file not found: $runtimeFile"
  exit 0
}

$runtime = Get-Content -LiteralPath $runtimeFile -Encoding UTF8 | ConvertFrom-Json
$pids = @($runtime.backend_pid, $runtime.frontend_pid) | Where-Object { $_ }

foreach ($procId in $pids) {
  try {
    Stop-Process -Id ([int]$procId) -Force -ErrorAction Stop
    Write-Output "Stopped PID $procId"
  } catch {
    Write-Output "PID $procId already stopped"
  }
}

Remove-Item -LiteralPath $runtimeFile -Force
Write-Output "Stopped env $EnvName"
