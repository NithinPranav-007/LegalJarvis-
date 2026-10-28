# LegalJarvis Deployment Smoke Test (PowerShell)
param (
    [string]$BaseUrl = "http://localhost:8000",
    [string]$FrontendUrl = "http://localhost:5173"
)

$ErrorActionPreference = "Continue"

Write-Host "================================================="
Write-Host "LegalJarvis Deployment Smoke Test (PRD T-21)"
Write-Host "================================================="

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$repoRoot = Split-Path -Parent (Split-Path -Parent $scriptDir)

python "$scriptDir\smoke_harness.py" --base-url $BaseUrl --frontend-url $FrontendUrl
$exitCode = $LASTEXITCODE

if ($exitCode -eq 0) {
    Write-Host "`n[SUCCESS] Deployment smoke verification completed." -ForegroundColor Green
    exit 0
} else {
    Write-Host "`n[FAILURE] Deployment smoke test failed with code $exitCode." -ForegroundColor Red
    exit $exitCode
}
