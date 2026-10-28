<#
.SYNOPSIS
    One-click PowerShell launcher for LegalJarvis (Backend + Frontend).
#>

$repoRoot = Split-Path -Parent $MyInvocation.MyCommand.Path

Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host "                  Starting LegalJarvis Project                        " -ForegroundColor Cyan
Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "[1/2] Launching FastAPI Backend on http://localhost:8000 ..." -ForegroundColor White
Start-Process powershell -ArgumentList "-NoExit", "-Command", "Set-Location '$repoRoot'; Write-Host 'LegalJarvis Backend Running...' -ForegroundColor Green; uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8000"

Start-Sleep -Seconds 3

Write-Host "[2/2] Launching React Frontend on http://localhost:5173 ..." -ForegroundColor White
Start-Process powershell -ArgumentList "-NoExit", "-Command", "Set-Location '$repoRoot\frontend'; Write-Host 'LegalJarvis Frontend Running...' -ForegroundColor Green; npm run dev -- --host 127.0.0.1 --port 5173"

Write-Host ""
Write-Host "======================================================================" -ForegroundColor Green
Write-Host "   LegalJarvis Services Successfully Launched!                        " -ForegroundColor Green
Write-Host ""
Write-Host "   Frontend Application:   http://localhost:5173" -ForegroundColor Yellow
Write-Host "   Backend Swagger Docs:   http://localhost:8000/docs" -ForegroundColor Yellow
Write-Host "   Health Endpoint:        http://localhost:8000/health" -ForegroundColor Yellow
Write-Host "======================================================================" -ForegroundColor Green
Write-Host ""

Start-Process "http://localhost:5173"
