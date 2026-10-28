# LegalJarvis

> **Citation-Verified Legal Research and Q&A for Indian Law**

LegalJarvis is an automated legal intelligence and research system for Indian law (Supreme Court of India, High Courts, and Central Statutes). Every generated answer is grounded in retrieved passages, verified against real paragraph citations, and engineered to abstain when evidence is insufficient or when asked for case-specific legal advice.

---

## Architecture & Technology Stack

- **Backend**: Python 3.11+, FastAPI, SQLAlchemy 2, Alembic, Pydantic v2
- **Vector & Full-Text Search**: PostgreSQL 16 + pgvector (`vector` extension) + PostgreSQL FTS
- **Frontend**: React 18, Vite, TypeScript, Tailwind CSS, Lucide icons
- **Models**:
  - Dense Retriever: `BAAI/bge-m3` (1024-dim embeddings)
  - Cross-Encoder Reranker: `BAAI/bge-reranker-base`
  - Generator: Configurable LLM gateway (Hosted OpenAI/Anthropic or local server; graceful fallback)
  - Rhetorical Role Segmenter: `law-ai/InLegalBERT`
- **Testing & Quality Assurance**: pytest, pytest-asyncio, ruff, mypy, bandit, pip-audit, npm audit, axe-core, Playwright, Locust

---

## Getting Started

### 1. Prerequisites
- Python 3.11+
- Node.js 20+
- Docker and Docker Compose (or a local PostgreSQL 16 instance with `pgvector`)
- Git

### 2. Quick Setup

```bash
# Clone and enter directory
git clone https://github.com/your-org/legaljarvis.git
cd legaljarvis

# Configure environment variables
cp .env.example .env

# Start database container
docker compose up -d db

# Install dependencies and set up environment
make setup
```

### 3. Running Verification and Tests

```bash
# Run linters and typecheckers (ruff, mypy, eslint)
make lint

# Run automated backend test suite (81 tests)
make test

# Run Playwright E2E and WCAG 2.1 AA accessibility audit
make a11y

# Run full security suite (bandit, pip-audit, npm audit, secret scanner)
make security

# Run concurrent performance load test (20 concurrent users, D4 targets)
make perf
```

### 4. Corpus Ingestion & Data Probing

```bash
# Probe open datasets (AWS Open Data SC Judgments, India Code, IL-TUR)
make data-probe

# Ingest Supreme Court judgments (Phase 1: 2023 validated baseline)
make ingest SOURCE=sc YEARS=2023

# Generate dense embeddings
make embed
```

### 5. Running the Application

```bash
# Start backend API (http://localhost:8000)
make run-backend

# Start frontend UI (http://localhost:5173)
make run-frontend
```

### 6. Operations: Smoke Test & Backup/Restore

```bash
# Run deployment smoke test
make smoke

# Create database backup dump with SHA-256 manifest
make backup

# Restore database from latest backup
make restore
```

---

## Documentation Index

- [**User Guide**](docs/user_guide.md): Complete walkthrough of Search, Q&A, Case Law Reader, Summarisation, Private Uploads, and the Reviewer Portal.
- [**Deployment Runbook**](docs/deployment.md): Sizing, Docker Compose setup, storage budgeting, and disaster recovery.
- [**Evaluation Report**](docs/eval/eval_report.md): Measured metrics, ablations, error taxonomy, and QA multi-run variance.
- [**Limitations and Future Work**](docs/limitations_and_future_work.md): Technical boundaries, non-lawyer positioning, and roadmap.
- [**Completion Report**](docs/completion_report.md): Final completion report in the five required status buckets.
- [**Requirements Traceability Matrix**](docs/traceability.md): Complete mapping of FR-01 through FR-18 and all NFRs.

---

## Important Notice & Disclaimers

> [!IMPORTANT]
> **Legal Information Disclaimer**: LegalJarvis provides automated legal research and informational analysis based on public court judgments and statutory texts. It **does not** provide legal advice, case-specific litigation strategy, or establish an attorney-client relationship under the Advocates Act, 1961. All citations should be verified independently against authoritative sources.

> [!NOTE]
> **Statute Transition Caveat**: With effect from 1 July 2024, the Indian Penal Code (IPC), Code of Criminal Procedure (CrPC), and Indian Evidence Act have been replaced by the Bharatiya Nyaya Sanhita (BNS), Bharatiya Nagarik Suraksha Sanhita (BNSS), and Bharatiya Sakshya Adhiniyam (BSA). Pre-July 2024 judgments reflect the previous statutory regime. LegalJarvis automatically generates a Criminal Law Transition Notice whenever pre-reform sections are referenced.

---

## Licensing and Attribution

Judgments are sourced from the AWS Open Data Registry under Creative Commons Attribution 4.0 International (CC-BY-4.0).
See [ATTRIBUTION.md](ATTRIBUTION.md) for full licensing details.
