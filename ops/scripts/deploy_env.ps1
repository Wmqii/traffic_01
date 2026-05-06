param(
  [ValidateSet('dev', 'test', 'prod')]
  [string]$EnvName = 'dev',
  [switch]$NoInstall,
  [switch]$SkipSmoke
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$startScript = Join-Path $PSScriptRoot 'start_env.ps1'
$stopScript = Join-Path $PSScriptRoot 'stop_env.ps1'
$smokeScript = Join-Path $PSScriptRoot 'smoke_api.ps1'

if (Test-Path -LiteralPath $stopScript) {
  & $stopScript -EnvName $EnvName | Out-Null
}

if ($NoInstall) {
  & $startScript -EnvName $EnvName -NoInstall
} else {
  & $startScript -EnvName $EnvName
}

if (-not $SkipSmoke) {
  & $smokeScript -EnvName $EnvName
}

Write-Output "Deploy completed for $EnvName"

