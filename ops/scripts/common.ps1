Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function Get-ProjectRoot {
  $scriptDir = Split-Path -Parent $PSScriptRoot
  return Split-Path -Parent $scriptDir
}

function Resolve-EnvFile {
  param(
    [Parameter(Mandatory = $true)]
    [ValidateSet('dev', 'test', 'prod')]
    [string]$EnvName
  )

  $root = Get-ProjectRoot
  $envFile = Join-Path $root "ops/environments/$EnvName.env"
  if (-not (Test-Path -LiteralPath $envFile)) {
    throw "Env file not found: $envFile"
  }
  return $envFile
}

function Import-EnvFile {
  param(
    [Parameter(Mandatory = $true)]
    [string]$EnvFile
  )

  $map = @{}
  $lines = Get-Content -LiteralPath $EnvFile -Encoding UTF8
  foreach ($line in $lines) {
    $trim = $line.Trim()
    if (-not $trim -or $trim.StartsWith('#')) {
      continue
    }
    $parts = $trim -split '=', 2
    if ($parts.Count -ne 2) {
      continue
    }
    $key = $parts[0].Trim()
    $value = $parts[1].Trim()
    $map[$key] = $value
    [Environment]::SetEnvironmentVariable($key, $value, 'Process')
  }
  return $map
}

function Get-RuntimeFile {
  param([string]$EnvName)
  $root = Get-ProjectRoot
  return Join-Path $root "ops/runtime/$EnvName.pids.json"
}

function Write-JsonFile {
  param(
    [Parameter(Mandatory = $true)]
    [string]$Path,
    [Parameter(Mandatory = $true)]
    [object]$Value
  )
  $dir = Split-Path -Parent $Path
  if ($dir -and -not (Test-Path -LiteralPath $dir)) {
    New-Item -ItemType Directory -Path $dir -Force | Out-Null
  }
  $Value | ConvertTo-Json -Depth 8 | Set-Content -LiteralPath $Path -Encoding UTF8
}
