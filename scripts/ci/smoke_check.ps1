param(
    [ValidateSet("local", "ci")]
    [string]$Mode = "local"
)

$ErrorActionPreference = "Stop"

function Assert-Exists {
    param(
        [string]$Path
    )
    if (-not (Test-Path -LiteralPath $Path)) {
        throw "Missing required path: $Path"
    }
}

function Resolve-Single {
    param(
        [string]$Pattern
    )
    $items = @(Get-ChildItem -Path $Pattern -File -ErrorAction SilentlyContinue)
    if ($items.Count -eq 0) {
        throw "No file matched pattern: $Pattern"
    }
    if ($items.Count -gt 1) {
        throw "Multiple files matched pattern: $Pattern"
    }
    return $items[0].FullName
}

$requiredPatterns = @(
    "execution/00_*.md",
    "execution/01_*.md",
    "execution/02_*.md",
    "execution/03_M1*.csv",
    "execution/logs/worklog.csv",
    "execution/logs/testlog.csv",
    "execution/logs/releaselog.csv",
    "execution/m1/G1-1*_v1.0.md",
    "execution/m1/G1-2*_v1.0.md",
    "execution/m1/G1-3*_v1.0.md",
    "execution/m1/G1-4*_v1.0.md"
)

foreach ($pattern in $requiredPatterns) {
    [void](Resolve-Single -Pattern $pattern)
}

$boardPath = Resolve-Single -Pattern "execution/03_M1*.csv"
$board = Import-Csv $boardPath
if (-not $board) {
    throw "M1 board has no records."
}

$logHeaders = @(
    @{ Path = "execution/logs/worklog.csv"; Header = "log_id" },
    @{ Path = "execution/logs/testlog.csv"; Header = "test_id" },
    @{ Path = "execution/logs/releaselog.csv"; Header = "release_id" }
)

foreach ($item in $logHeaders) {
    $row = Import-Csv $item.Path | Select-Object -First 1
    if (-not $row) {
        throw "Log file has no data rows: $($item.Path)"
    }
    $props = $row.PSObject.Properties.Name
    if ($props -notcontains $item.Header) {
        throw "Missing required header '$($item.Header)' in $($item.Path)"
    }
}

$doneCount = ($board | Where-Object { $_.status -eq "Done" }).Count
$result = [PSCustomObject]@{
    mode = $Mode
    checked_at = (Get-Date).ToString("yyyy-MM-dd HH:mm:ss")
    required_patterns = $requiredPatterns.Count
    m1_tasks_total = $board.Count
    m1_tasks_done = $doneCount
    status = "PASS"
}

New-Item -ItemType Directory -Path "ops/artifacts" -Force | Out-Null
$result | ConvertTo-Json | Set-Content -Path "ops/artifacts/ci_smoke_result.json" -Encoding UTF8

Write-Output "Smoke check passed. M1 done: $doneCount/$($board.Count)"
