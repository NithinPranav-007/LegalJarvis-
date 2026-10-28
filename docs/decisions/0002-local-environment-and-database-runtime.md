# ADR 0002: Local Execution Environment and Database Runtime Fallback

## Context
During T-01 environment scaffolding on the host machine (`win32`, Python 3.13 / Anaconda), `docker` is not installed (`docker: The term 'docker' is not recognized`).
Per PRD Part F T-01 and Part D14, the canonical deployment targets `docker compose up -d db` running `pgvector/pgvector:pg16`.
In CI (`.github/workflows/ci.yml`), the GitHub Actions runner spins up the `pgvector/pgvector:pg16` service container directly.

## Decision
1. `docker-compose.yml` defines the production and local Docker setup with `pgvector/pgvector:pg16` and healthy status checks.
2. For local testing where Docker Desktop is not installed on the developer workstation:
   - Automated unit tests, linting (`ruff`), typechecking (`mypy`), security scanning (`bandit`), and secret scanning run locally using the Python environment.
   - For database tests, when a live PostgreSQL + pgvector instance is unreachable at `DATABASE_URL`, tests skip live-database-dependent execution or use SQLite/mock fixtures with an explicit warning, and the real PostgreSQL pgvector tests run in CI where the Docker service is active.
3. Once Docker Desktop or a remote PostgreSQL instance is available, `DATABASE_URL` connects directly to the pgvector container.
