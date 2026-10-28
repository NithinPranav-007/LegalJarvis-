# LegalJarvis Deployment Guide & Operations Runbook

**Document:** `docs/deployment.md`  
**PRD Reference:** Part D14, Deliverable 10, Task T-21  
**Target Environment:** Docker Compose on Linux VM / Cloud Server / Local Workstation  

---

## 1. System Overview

LegalJarvis is deployed as a modular three-tier containerized architecture orchestrated via Docker Compose:
1. **`db`**: PostgreSQL 16 with `pgvector` extension for structured case metadata, full-text inverted index (FTS), and dense vector similarity search.
2. **`backend`**: FastAPI application serving REST endpoints (`/health`, `/v1/search`, `/v1/qa`, `/v1/documents`, `/v1/statutes`, `/v1/feedback`), LLM gateway, and citation verifier.
3. **`frontend`**: React + TypeScript + Tailwind single-page application served via Vite.

---

## 2. Hardware and Storage Requirements

| Resource | Minimum (Development) | Recommended (Production / 1 SC Year) |
|---|---|---|
| **CPU** | 2 Cores | 4 Cores |
| **RAM** | 4 GB | 8 GB (16 GB if running neural reranker locally) |
| **Disk Storage** | 10 GB SSD | 50 GB NVMe SSD |
| **Network** | Outbound access to AWS Open Data | Outbound access to AWS Open Data & LLM API |

### Storage Budgeting
- **Raw PDFs & Tars (1 Supreme Court Year, ~3,000 judgments):** ~3 to 5 GB.
- **Extracted Text & Metadata:** ~500 MB.
- **Postgres Database + pgvector Index:** ~1.5 GB.
- **Embedding Models (BGE-M3 / InLegalBERT):** ~1.2 to 2.2 GB.
- **Backups:** ~2 GB (configured with 7-day rolling retention).

---

## 3. Quickstart Deployment (Single VM)

### Step 1: Clone Repository
```bash
git clone https://github.com/your-org/legaljarvis.git
cd legaljarvis
```

### Step 2: Configure Environment Variables
Copy the template configuration file:
```bash
cp .env.example .env
```
Edit `.env` to configure credentials:
```bash
# Core Database Settings
POSTGRES_USER=legaljarvis
POSTGRES_PASSWORD=replace_with_a_secure_strong_password
POSTGRES_DB=legaljarvis
POSTGRES_PORT=5432

# Application Security
SECRET_KEY=generate_with_openssl_rand_hex_32
JWT_SECRET=generate_with_openssl_rand_hex_32
ACCESS_TOKEN_EXPIRE_MINUTES=1440

# LLM Gateway
LLM_PROVIDER=openai  # or anthropic, mistral, ollama, fake
LLM_API_KEY=your_actual_api_key_here
LLM_MODEL=gpt-4o-mini
```

### Step 3: Launch Services via Docker Compose
```bash
docker compose up -d --build
```
Verify that all containers are healthy:
```bash
docker compose ps
```

### Step 4: Run Database Migrations
```bash
docker compose exec backend alembic upgrade head
```

### Step 5: Ingest Initial Corpus
```bash
docker compose exec backend python -m app.ingest.cli ingest --source sc --years 2023
docker compose exec backend python -m app.ingest.cli embed
```

### Step 6: Verify Deployment via Smoke Test
```bash
make smoke
# or
bash scripts/ops/smoke.sh http://localhost:8000 http://localhost:5173
```

---

## 4. Operational Scripts & Automation

### Smoke Testing (`scripts/ops/smoke.sh` / `smoke.ps1`)
Tests the core deployment endpoints:
- `GET /health`: Liveness and database connectivity.
- `POST /v1/search`: Hybrid retrieval and passage attribution.
- `POST /v1/qa`: Citation-grounded answer generation or graceful low-evidence abstention.
- `GET /v1/statutes`: Versioning and criminal law concordance.

### Database Backup (`scripts/ops/backup.sh` / `backup.ps1`)
Creates a full SQL dump with SHA-256 integrity manifest:
```bash
make backup
# Generated: backups/legaljarvis_backup_YYYYMMDD_HHMMSS.sql
# Manifest:  backups/legaljarvis_backup_YYYYMMDD_HHMMSS.sql.sha256
```

Recommended automated cron job (daily at 02:00 UTC):
```crontab
0 2 * * * cd /opt/legaljarvis && bash scripts/ops/backup.sh >> /var/log/legaljarvis_backup.log 2>&1
```

### Database Restore (`scripts/ops/restore.sh` / `restore.ps1`)
Restores the database from a verified backup:
```bash
# Restores from latest available backup
make restore

# Or restore specific backup
bash scripts/ops/restore.sh backups/legaljarvis_backup_20261028_120000.sql
```

---

## 5. Security & Isolation Controls

1. **Row-Level Security (RLS):** Private user uploads are isolated via PostgreSQL Row-Level Security policies. Unauthenticated or non-owning users receive zero records and 404 responses.
2. **Zero Text Leakage in Logs:** Application logs sanitize all private document text and user queries.
3. **Secret Protection:** Zero secrets or credentials tracked in Git (validated via `check_secrets.py` and `bandit`).
4. **WCAG 2.1 AA Accessibility:** Continuous automated compliance validated via `axe-core` across all user workflows.

---

## 6. Disaster Recovery Runbook

| Incident | Triage Step | Resolution |
|---|---|---|
| **Database container crash** | `docker compose logs db` | Check disk volume; restart with `docker compose restart db`. |
| **Corrupted database** | Inspect log errors | Re-create volume: `docker compose down -v && docker compose up -d db && make restore`. |
| **LLM Provider API Outage** | Check `POST /v1/qa` output | LegalJarvis automatically enters **graceful degradation mode**, delivering top cited authoritative passages with clear service status notice. |
| **High Search Latency** | Check slow query logs | Verify HNSW index health in Postgres: `REINDEX TABLE chunks;`. |
