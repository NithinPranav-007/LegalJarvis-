# Requirements Traceability Matrix — LegalJarvis

## 1. Overview
This matrix traces every Functional Requirement (FR-01 to FR-18) and Non-Functional Requirement (NFR) specified in `docs/PRD.md` to its planned implementation module, associated automated test(s), and current implementation status.

Status values:
- `not started`: Requirement specified and mapped; implementation not yet begun.
- `in progress`: Implementation or testing underway.
- `implemented`: Code written, automated test passing, output recorded in `docs/progress/`.
- `blocked`: Progress blocked on external dependency (credentials, reviewer, compute); fallback applied.

---

## 2. Functional Requirements (FR-01 .. FR-18)

| Requirement ID | Title | Priority | Planned Module(s) | Planned Test(s) | Status |
|---|---|---|---|---|---|
| **FR-01** | Corpus ingestion (SC/HC/statutes) | P0 | `backend/app/ingest/download.py`, `cli.py`, `scripts/data/` | `backend/tests/integration/test_ingest.py` (T-FR01) | implemented |
| **FR-02** | Text extraction and normalisation | P0 | `backend/app/ingest/extract.py`, `backend/app/ingest/clean.py` | `backend/tests/unit/test_extract.py` (T-FR02) | implemented |
| **FR-03** | Structure-aware segmentation | P0 | `backend/app/ingest/segment.py` | `backend/tests/unit/test_segment.py` (T-FR03 offsets test) | implemented |
| **FR-04** | Hybrid search with filters | P0 | `backend/app/retrieval/` (`lexical.py`, `dense.py`, `fusion.py`, `rerank.py`, `hybrid.py`, `filters.py`), `api/search.py` | `backend/tests/integration/test_retrieval.py` (T-FR04), `tests/api/test_search.py` | implemented |
| **FR-05** | Cited question answering | P0 | `backend/app/qa/` (`orchestrator.py`, `query_analysis.py`, `context_builder.py`), `prompts/qa_v1.txt`, `api/qa.py` | `backend/tests/integration/test_qa.py` (T-FR05) | implemented |
| **FR-06** | Citation verification and abstention | P0 | `backend/app/verify/` (`existence.py`, `support.py`, `abstain.py`), `prompts/judge_v1.txt` | `backend/tests/unit/test_verify.py` (T-FR06 seeded failures) | implemented |
| **FR-07** | Document viewer with source highlighting | P0 | `backend/app/api/documents.py`, `frontend/src/pages/CaseViewer.tsx` | `frontend/tests/e2e/app.spec.ts` (T-FR07), `frontend/tests/unit/CaseViewer.test.tsx`, `backend/tests/api/test_documents_and_feedback.py` | implemented |
| **FR-08** | Upload and analyse user documents | P1 | `backend/app/api/documents.py`, `backend/app/db/models.py` (RLS), `frontend/src/pages/MyDocuments.tsx` | `backend/tests/security/test_isolation.py` (T-FR08) | not started |
| **FR-09** | Structured summarisation | P1 | `backend/app/summarize/`, `prompts/summary_v1.txt` | `backend/tests/unit/test_summarize.py` (T-FR09) | not started |
| **FR-10** | Conversational follow-ups | P1 | `backend/app/qa/query_analysis.py` | `backend/tests/unit/test_followup.py` | not started |
| **FR-11** | Multi-document comparison | P2 | `backend/app/api/compare.py`, `frontend/src/pages/Compare.tsx` | `backend/tests/api/test_compare.py` | not started |
| **FR-12** | Filters and metadata faceting | P0 | `backend/app/retrieval/filters.py`, `backend/app/api/search.py` | `backend/tests/api/test_search_facets.py` | not started |
| **FR-13** | Statute lookup, versioning, IPC/BNS notice | P1 | `backend/app/statutes/` (`loader.py`, `versions.py`, `concordance.py`, `references.py`), `api/statutes.py` | `backend/tests/unit/test_statutes.py` (T-FR13) | implemented |
| **FR-14** | User and reviewer feedback capture | P1 | `backend/app/api/feedback.py`, `frontend/src/components/FeedbackWidget.tsx` | `backend/tests/api/test_documents_and_feedback.py` (T-FR14), `frontend/tests/unit/HistoryAndFeedback.test.tsx` | implemented |
| **FR-15** | Authentication and RBAC | P1 | `backend/app/api/auth.py`, `backend/app/core/security.py` | `backend/tests/api/test_auth.py` (T-FR15) | implemented |
| **FR-16** | Evaluation harness and dashboard | P0 | `backend/app/eval/` (`runner.py`, `metrics.py`, `datasets.py`), `frontend/src/pages/AdminEval.tsx` | `backend/tests/integration/test_eval.py` (T-FR16) | in progress |
| **FR-17** | Safety and legal-advice guardrails | P0 | `backend/app/qa/guardrails.py`, `prompts/qa_v1.txt` | `backend/tests/security/test_guardrails.py` | not started |
| **FR-18** | Audit logging | P1 | `backend/app/core/logging.py`, `backend/app/qa/orchestrator.py` | `backend/tests/unit/test_audit_logging.py` | not started |

---

## 3. Non-Functional Requirements (NFRs)

| Requirement ID | Dimension | Priority | Target / Pass Condition | Planned Module(s) | Planned Test(s) | Status |
|---|---|---|---|---|---|---|
| **NFR-PERF** | Performance | P0 | Search p95 <= 2s; Q&A p95 <= 20s; stream first token <= 5s | `backend/app/retrieval/`, `backend/app/qa/` | `tests/perf/locustfile.py` (T-NFR-PERF) | not started |
| **NFR-ACC** | Accuracy | P0 | Citation existence 100%; supported-claim rate measured | `backend/app/verify/` | `backend/tests/unit/test_verify.py` (T-FR06) | implemented |
| **NFR-REL** | Reliability | P0 | Graceful degradation; `/health` endpoint; generator-down fallback | `backend/app/api/health.py`, `backend/app/qa/orchestrator.py` | `backend/tests/integration/test_degradation.py` | not started |
| **NFR-SEC** | Security | P0 | OWASP Top 10 compliant; zero secrets in Git; parameterised SQL | `backend/app/core/security.py`, `.env.example`, CI | `scripts/ops/check_secrets.py`, `bandit` | in progress |
| **NFR-PRIV** | Privacy | P0 | Private document cross-user isolation closed; RLS enabled | `backend/app/db/models.py`, `backend/app/api/documents.py` | `backend/tests/security/test_isolation.py` (T-FR08) | not started |
| **NFR-SCAL** | Scalability | P1 | Incremental ingestion; single-node Postgres + pgvector scaling | `backend/app/ingest/` | `backend/tests/integration/test_ingest_incremental.py` | not started |
| **NFR-A11Y** | Accessibility | P1 | WCAG 2.1 AA for core flows; visible focus; axe-core checks | `frontend/src/` | `frontend/tests/e2e/a11y.spec.ts` (T-NFR-A11Y) | not started |
| **NFR-MAINT** | Maintainability | P0 | Ruff, mypy, eslint, tsc; >= 80% line coverage on core logic | Codebase standards, CI | `make lint && make test` | in progress |
| **NFR-FAULT** | Fault Tolerance | P0 | Resumable ingestion; all ingestion stages idempotent | `backend/app/ingest/` | `backend/tests/integration/test_ingest.py` | implemented |
| **NFR-INTEG** | Data Integrity | P0 | Full provenance: chunk -> document -> raw file -> sha256 -> snapshot | `backend/app/db/models.py`, `backend/app/ingest/` | `backend/tests/db/test_models.py` | in progress |
| **NFR-LOG** | Logging & Metrics | P1 | Structured JSON logs; request IDs; `/metrics` in Prometheus format | `backend/app/core/logging.py`, `backend/app/api/metrics.py` | `backend/tests/api/test_metrics.py` | not started |
| **NFR-DEP** | Deployment & Recovery | P0 | Clean reproduction from README; smoke test; backup/restore | `docker-compose.yml`, `scripts/ops/` | `scripts/ops/smoke.sh`, `scripts/ops/backup.sh`, `scripts/ops/restore.sh` | not started |
