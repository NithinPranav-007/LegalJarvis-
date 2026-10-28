# LegalJarvis

> **Citation-Verified Legal Research and Q&A for Indian Law**

LegalJarvis is an AI-driven legal intelligence system for Indian law (Supreme Court of India, High Courts, and Central Statutes). Every generated answer is grounded in retrieved passages, verified against real paragraph citations, and designed to abstain when evidence is insufficient or when asked for case-specific legal advice.

---

## Architecture & Technology Stack

- **Backend**: Python 3.11+, FastAPI, SQLAlchemy 2, Alembic, Pydantic v2
- **Vector & Full-Text Search**: PostgreSQL 16 + pgvector (`vector` extension) + PostgreSQL FTS
- **Frontend**: React, Vite, TypeScript, Tailwind CSS, Lucide icons
- **Models**:
  - Dense Retriever: `BAAI/bge-m3` (1024-dim embeddings)
  - Cross-Encoder Reranker: `BAAI/bge-reranker-base`
  - Generator: Configurable LLM gateway (Hosted or local)
  - Rhetorical Role Encoder: `law-ai/InLegalBERT`
- **Testing & Quality Assurance**: pytest, pytest-asyncio, ruff, mypy, bandit, gitleaks, Playwright

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
cd legaljarvis

# Configure environment variables
cp .env.example .env

# Start database container
docker compose up -d db

# Install dependencies
make setup
# Or on Windows PowerShell:
.\make.ps1 setup
```

### 3. Running Verification and Tests

```bash
# Run linters and typecheckers
make lint
# Or on Windows PowerShell:
.\make.ps1 lint

# Run automated tests
make test
# Or on Windows PowerShell:
.\make.ps1 test
```

### 4. Corpus Ingestion & Data Probing

```bash
# Probe open datasets (AWS Open Data SC Judgments, India Code, IL-TUR)
make data-probe

# Ingest Supreme Court judgments (Phase 1: one year)
make ingest SOURCE=sc YEARS=2023
```

### 5. Running the Application

```bash
# Start backend API (http://localhost:8000)
make run-backend

# Start frontend UI (http://localhost:5173)
make run-frontend
```

---

## Important Notice & Disclaimers

> [!IMPORTANT]
> **Legal Information Disclaimer**: LegalJarvis provides automated legal research and informational analysis based on public court judgments and statutory texts. It **does not** provide legal advice, case-specific litigation strategy, or establish an attorney-client relationship. All citations should be verified independently against authoritative sources.

> [!NOTE]
> **Statute Transition Caveat**: With effect from 1 July 2024, the Indian Penal Code (IPC), Code of Criminal Procedure (CrPC), and Indian Evidence Act have been replaced by the Bharatiya Nyaya Sanhita (BNS), Bharatiya Nagarik Suraksha Sanhita (BNSS), and Bharatiya Sakshya Adhiniyam (BSA). Pre-July 2024 judgments reflect the previous statutory regime.

---

## Licensing and Attribution

Judgments are sourced from the AWS Open Data Registry under Creative Commons Attribution 4.0 International (CC-BY-4.0).
See [ATTRIBUTION.md](ATTRIBUTION.md) for full licensing details.
