# Starts the disposable test Postgres, runs pytest with the given arguments, then tears it down.
# Usage: .\scripts\run_tests.ps1 [pytest args]      e.g. .\scripts\run_tests.ps1 -m integration -q
$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
Set-Location $root

$compose = @("compose", "-f", "docker-compose.test.yml")
$python = Join-Path $root "venv\Scripts\python.exe"
if (-not (Test-Path $python)) { $python = "python" }

if (-not $env:TEST_DATABASE_URL) {
    $env:TEST_DATABASE_URL = "postgresql+psycopg2://postgres:postgres@localhost:55432/jobmatch_test"
}

$exitCode = 1
try {
    & docker @compose up -d --wait postgres-test
    if ($LASTEXITCODE -ne 0) { throw "Could not start postgres-test" }
    & $python -m pytest @args
    $exitCode = $LASTEXITCODE
}
finally {
    & docker @compose down -v
}
exit $exitCode
