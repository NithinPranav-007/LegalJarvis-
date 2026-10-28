param (
    [Parameter(Position=0)]
    [string]$Target = "help",
    [Parameter(ValueFromRemainingArguments=$true)]
    [string[]]$Args
)

$ErrorActionPreference = "Stop"

function Show-Help {
    Write-Host "LegalJarvis PowerShell Task Runner" -ForegroundColor Cyan
    Write-Host "Usage: .\make.ps1 <target> [args]"
    Write-Host ""
    Write-Host "Targets:"
    Write-Host "  setup         - Install backend and frontend dependencies"
    Write-Host "  lint          - Run linters (ruff, mypy)"
    Write-Host "  test          - Run test suites (pytest)"
    Write-Host "  eval          - Run evaluation runner"
    Write-Host "  smoke         - Run deployment smoke test"
    Write-Host "  ingest        - Run ingestion CLI"
    Write-Host "  run-backend   - Start FastAPI backend"
    Write-Host "  run-frontend  - Start Vite dev server"
    Write-Host "  backup        - Run database backup script"
    Write-Host "  restore       - Run database restore script"
    Write-Host "  data-probe    - Probe data sources"
    Write-Host "  security      - Run security scans"
}

switch ($Target.ToLower()) {
    "setup" {
        python -m pip install --upgrade pip
        python -m pip install -e "backend[dev]"
        Push-Location frontend
        npm install
        Pop-Location
    }
    "lint" {
        ruff check backend/
        mypy backend/app
    }
    "test" {
        pytest backend/tests -v
    }
    "eval" {
        python -m backend.app.eval.runner --config configs/experiment.yaml
    }
    "smoke" {
        & "scripts\ops\smoke.ps1"
    }
    "ingest" {
        python -m backend.app.ingest.cli ingest $Args
    }
    "run-backend" {
        uvicorn app.main:app --app-dir backend --host 0.0.0.0 --port 8000 --reload
    }
    "run-frontend" {
        Push-Location frontend
        npm run dev
        Pop-Location
    }
    "backup" {
        & "scripts\ops\backup.ps1"
    }
    "restore" {
        & "scripts\ops\restore.ps1"
    }
    "data-probe" {
        & "scripts\data\probe_sources.ps1"
    }
    "security" {
        bandit -r backend/app -ll
        ruff check backend/
    }
    Default {
        Show-Help
    }
}
