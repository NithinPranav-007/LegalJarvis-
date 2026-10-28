.PHONY: help setup lint test eval eval-retrieval llm-ping smoke ingest embed run-backend run-frontend backup restore data-probe security clean

PYTHON ?= python
PIP ?= pip
SOURCE ?= sc
YEARS ?= 2023

help:
	@echo "LegalJarvis Management Commands:"
	@echo "  make setup         - Set up environment, virtualenv, and install dependencies"
	@echo "  make lint          - Run linters and typecheckers (ruff, mypy, eslint)"
	@echo "  make test          - Run test suites (pytest, vitest)"
	@echo "  make eval          - Run evaluation harness and benchmarks"
	@echo "  make smoke         - Run system deployment smoke test"
	@echo "  make ingest        - Run corpus ingestion (e.g. make ingest SOURCE=sc YEARS=2023)"
	@echo "  make run-backend   - Start the FastAPI backend"
	@echo "  make run-frontend  - Start the React frontend development server"
	@echo "  make backup        - Create database backup dump"
	@echo "  make restore       - Restore database from latest backup"
	@echo "  make data-probe    - Probe data sources and verify accessibility"
	@echo "  make security      - Run security audits (bandit, gitleaks)"

setup:
	$(PYTHON) -m venv .venv || true
	$(PIP) install --upgrade pip
	$(PIP) install -e "./backend[dev]"
	cd frontend && npm install

lint:
	ruff check backend/
	mypy backend/app
	cd frontend && npm run lint || true

test:
	pytest backend/tests -v

eval:
	$(PYTHON) -m app.eval.runner --config configs/experiment.yaml

eval-retrieval:
	$(PYTHON) -m app.eval.runner --config configs/experiment.yaml

eval-qa:
	$(PYTHON) -m app.eval.qa_runner --runs 3 --config configs/experiment.yaml

llm-ping:
	$(PYTHON) -m app.llm.gateway

smoke:
	bash scripts/ops/smoke.sh || powershell -File scripts/ops/smoke.ps1

ingest:
	$(PYTHON) -m app.ingest.cli ingest --source $(SOURCE) --years $(YEARS)

embed:
	$(PYTHON) -m app.ingest.cli embed

run-backend:
	uvicorn app.main:app --app-dir backend --host 0.0.0.0 --port 8000 --reload

run-frontend:
	cd frontend && npm run dev

backup:
	bash scripts/ops/backup.sh || powershell -File scripts/ops/backup.ps1

restore:
	bash scripts/ops/restore.sh || powershell -File scripts/ops/restore.ps1

data-probe:
	bash scripts/data/probe_sources.sh || powershell -File scripts/data/probe_sources.ps1

security:
	bandit -r backend/app -ll
	ruff check backend/

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
