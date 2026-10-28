# ADR 0001: Reconciliation of "Indicative Research Projects" with PRD

## Context
During initial project setup, two background PDFs were provided:
1. `LegalJarvis_ AI-Powered Legal Research and Assistance System.pdf` (5-page early research and design concept draft, dated 2026-10-28)
2. `LegalJarvis Indicative Projects.pdf` (1-page Sponsored Research Programme notice by Legal Jarvis AI Labs Private Limited with Sree Eshwar College of Engineering, Coimbatore)

Per SETUP Step 4, we inspected whether `LegalJarvis Indicative Projects.pdf` changes scope, jurisdiction, or requirements, or conflicts with `docs/PRD.md`.

## Analysis
- **Jurisdiction**: Both documents confirm Indian law (English language) as the jurisdiction. The Indicative Projects note explicitly targets "Indian judgments and orders aggregated from public sources" and statutory provisions of the Bharatiya Nyaya Sanhita (BNS), Bharatiya Nagarik Suraksha Sanhita (BNSS), and Bharatiya Sakshya Adhiniyam (BSA).
- **Core Objective & Architecture**: The Indicative Projects note lists three semester projects:
  - Project 1: Indian Legal Corpus Builder (data engineering, public judgment ingestion, metadata extraction, deduplication, storage).
  - Project 2: Petition Retrieval Engine (RAG) (semantic retrieval, legal embeddings, vector database, API).
  - Project 3: Statutory Section Classifier (BNS / BNSS / BSA) (mapping fact patterns to new criminal codes).
- **Alignment with PRD**: `docs/PRD.md` comprehensively incorporates these three facets:
  - Corpus builder & metadata -> PRD Part C & Tasks T-02, T-04..T-06.
  - Hybrid RAG retrieval engine -> PRD FR-01..FR-04, Tasks T-07..T-09.
  - Statutory concordance (IPC to BNS/BNSS/BSA) -> PRD FR-09, Task T-15.
  - In addition, the PRD provides rigorous citation verification (FR-02, T-11), hallucination safeguards/abstention (FR-03, T-12), and legal disclaimer protections.

## Conclusion & Decision
There is no conflict in jurisdiction or core objective between the Indicative Projects document and the PRD. The PRD (`docs/PRD.md`) remains the authoritative specification and source of truth for implementation. No jurisdiction or scope changes are required.
