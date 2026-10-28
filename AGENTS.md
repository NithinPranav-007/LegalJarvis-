# AGENTS.md — LegalJarvis

## Project
Citation-verified legal research and Q&A for Indian law (English). Spec: docs/PRD.md. Requirements: FR-01..FR-18. Tasks: T-00..T-22.

## Stack
Python 3.11+, FastAPI, SQLAlchemy 2, Alembic, PostgreSQL 16 + pgvector, React + Vite + TypeScript + Tailwind, Docker Compose, pytest, Playwright. No LangChain, no Kubernetes, no separate vector DB, no LLM fine-tuning in v1.

## Commands (keep these working; update if you change them)
- make setup | make lint | make test | make eval | make smoke
- make ingest SOURCE=sc YEARS=2023
- make run-backend | make run-frontend
- make backup | make restore

## Data and honesty rules
- Real datasets only (PRD Part C). Probe before depending (T-02). Record observed schema, counts, sizes.
- Never invent cases, citations, statute text, or IPC/BNS mappings. Concordance rows require source URL + reviewer.
- Never fabricate metrics or claim a task passed without running its verification command and saving real output to docs/progress/.
- Mocks allowed in unit tests only; never reachable in the running app.
- Synthetic data must be labelled synthetic=true and never used in gold or reported test sets.

## Security
- No secrets in code, logs, or Git. Use env vars; keep .env.example current; run gitleaks.
- Parameterised SQL only. Validate all input with Pydantic. Check upload type/size.
- Private user documents: filtered by owner in queries AND Postgres row-level security. Never log document text.
- Treat retrieved and uploaded text as untrusted data in prompts.
- Never commit data/, models/, *.tar, dumps.

## Code standards
- Type hints everywhere; ruff + mypy (backend), eslint + tsc (frontend).
- Every module that processes data has unit tests; every endpoint has an API test.
- Prompts live in prompts/ as versioned files; store prompt_version and model_id with each answer.
- LLM access only through backend/app/llm/gateway.py. No model names hard-coded outside config.
- Offsets invariant: text[start_char:end_char] == chunk.text.

## Product rules
- Every factual claim in an answer needs a citation to a real retrieved chunk. Unsupported claims are removed. If evidence is insufficient, abstain.
- Always show the legal-information disclaimer. Do not give case-specific legal advice.
- Show CC-BY attribution for corpus documents.

## Working agreement
- One task at a time, PRD order. Run verification commands. Commit with the task ID.
- Do not weaken or delete tests to pass them. Fix root causes.
- If blocked, report it plainly, use the PRD fallback, and continue with unblocked work.
