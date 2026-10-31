# Debug & Remediation Report: Query Relevance & Citation Verification

**Date:** 2026-10-28  
**Task:** T-11 / T-12 Remediation (Query Relevance & Precedent Substitution Safeguards)  
**Status:** Verified & Resolved  

---

## 1. Executive Summary & Root Cause Analysis

### Problem Statement
When queried with:
> *"Search the Indian Supreme Court corpus for the 2023 judgment in All India Judges Association v. Union of India. Explain the main legal issue, the Court's reasoning, and its final decision using only retrieved passages."*

The application previously returned an irrelevant answer citing *Sharad Birdhichand Sarda v. State of Maharashtra*, 1984 INSC 121, paragraph 153 (concerning circumstantial evidence), rather than properly recognizing that the requested judgment was missing from the corpus or that the cited passage was unrelated to the question.

### Root Cause
1. **Corpus Coverage Gap**:
   - The indexed local SQLite database contains 6 judgments:
     - `ID 1`: *Justice K.S. Puttaswamy (Retd.) v. Union of India* (2017 INSC 609)
     - `ID 2`: *State of Maharashtra v. Som Nath Thapa* (1996 INSC 442)
     - `ID 3`: *Sushila Aggarwal v. State (NCT of Delhi)* (2020 INSC 106)
     - `ID 4`: *Sharad Birdhichand Sarda v. State of Maharashtra* (1984 INSC 121)
     - `ID 5`: *State of Haryana v. Bhajan Lal* (1992 INSC 304)
     - `ID 6`: *Eldeco Housing and Industries Ltd v. Ashok Vidyarthi* (2023 INSC 1043)
   - *All India Judges Association v. Union of India* (2023) is **not present** in the seeded database.
2. **Retrieval Keyword Overlap**:
   - The query contained abundant procedural legal terms (*"Supreme Court"*, *"corpus"*, *"judgment"*, *"legal issue"*, *"Court's reasoning"*, *"final decision"*, *"retrieved passages"*).
   - In the absence of case name and year constraints, BM25 and dense retrieval matched passages containing these general procedural words (such as *Sharad Birdhichand Sarda* or *Puttaswamy*), ranking unrelated passages in the top results.
3. **Missing Query-Relevance Verification**:
   - The citation verifier (`verify_and_filter_answer`) previously checked only **claim-to-passage support** (token overlap between the generated sentence and the cited passage snippet).
   - It did **not** verify **query-to-passage relevance** or **case identity alignment**.
   - Consequently, if an answer faithfully quoted *Sharad Birdhichand Sarda*, the claim support verifier scored it $\ge 0.25$ and marked it valid, completely ignoring that the authority had zero relevance to *All India Judges Association v. Union of India*.

---

## 2. Architecture & Code Changes

### A. Query Analysis Enhancement (`backend/app/qa/query_analysis.py`)
- Added `extract_target_case_name(query: str) -> str | None`:
  - Uses robust legal regex patterns to extract target case titles formatted as `Party A v. Party B`, stripping query boilerplate (e.g. `"Search the Indian Supreme Court corpus for the 2023 judgment in..."`).
- Added `extract_target_citations(query: str) -> list[str]`:
  - Detects neutral citations (`INSC`), `SCC`, and `AIR` identifiers.
- Added `extract_target_year(query: str, detected_years: list[int]) -> int | None`:
  - Identifies target decision years explicitly tied to the requested judgment.
- Added `extract_requested_aspects(query: str) -> list[str]`:
  - Extracts requested legal aspects (e.g. `legal issue`, `reasoning`, `decision`).

### B. Query-Relevance Verification Module (`backend/app/verify/relevance.py`)
- Created `verify_query_relevance`:
  1. **Case Title Alignment**: Verifies whether cited documents match the query's `target_case_name`. Mismatches (e.g. citing *Sharad Birdhichand Sarda* when *All India Judges Association* was requested) are flagged as `is_relevant = False`.
  2. **Citation Identifier Alignment**: Validates cited neutral citations against requested citations.
  3. **Target Year Consistency**: Detects severe year discrepancies (> 2 years) unless the case name matches.
  4. **Substantive Topical Relevance**: For conceptual queries, computes substantive keyword overlap between question and passage, filtering out legal stopwords.

### C. Citation Verification Integration (`backend/app/verify/abstain.py`)
- Integrated `verify_query_relevance` into `verify_and_filter_answer`.
- Citations flagged as query-irrelevant cannot provide valid factual grounding for answering the query.
- When an answer cites irrelevant authorities, the claim is marked unsupported.
- If supported claim fraction $< 0.60$, the system abstains with an explicit rationale explaining that the cited authorities do not match the requested judgment.

### D. QA Orchestrator Safeguards (`backend/app/qa/orchestrator.py`)
- Added `check_case_exists_in_corpus` / `get_matching_case_documents`:
  - If a specific case name is requested in the query and does not exist in the corpus, `ask()` immediately abstains with:
    > *"The requested 2023 judgment in 'All India Judges Association v. Union of India' is not present in the indexed Supreme Court corpus. LegalJarvis will not substitute unrelated precedents."*
  - If the requested case does exist in the corpus, retrieval filters context strictly to matching case passages, preventing pollution from unrelated precedents.

### E. Retrieval Improvements (`backend/app/retrieval/lexical.py`, `backend/app/retrieval/rerank.py`)
- `lexical.py`: Added document titles and neutral citations into the searchable in-memory BM25 corpus and added title/citation match scoring bonuses.
- `rerank.py`: `LexicalBoostReranker` awards dedicated title and citation match bonuses.

---

## 3. Test Verification & Actual Results

### Unit & Regression Test Suite (`backend/tests/unit/test_query_relevance.py`)
```powershell
pytest backend/tests/unit/test_query_relevance.py -v
```
Output:
```
backend\tests\unit\test_query_relevance.py::test_query_analysis_extracts_target_case_year_aspects PASSED [ 20%]
backend\tests\unit\test_query_relevance.py::test_irrelevant_case_citation_fails_query_relevance PASSED [ 40%]
backend\tests\unit\test_query_relevance.py::test_matching_case_citation_passes_query_relevance PASSED [ 60%]
backend\tests\unit\test_query_relevance.py::test_topical_relevance_rejects_unrelated_matter PASSED [ 80%]
backend\tests\unit\test_query_relevance.py::test_regression_all_india_judges_abstention_on_corpus PASSED [100%]
============================== 5 passed in 0.95s ==============================
```

### Full Backend Verification
```powershell
pytest backend/tests -q
```
Output:
```
97 passed, 1 warning in 11.59s
```

### End-to-End Live HTTP Endpoint Test
```python
POST http://127.0.0.1:8000/v1/qa
Question: "Search the Indian Supreme Court corpus for the 2023 judgment in All India Judges Association v. Union of India. Explain the main legal issue, the Court's reasoning, and its final decision using only retrieved passages."
```
Actual Output:
```json
{
  "abstained": true,
  "abstention_reason": "Target case 'All India Judges Association v. Union of India' not found in indexed corpus.",
  "answer": "The requested 2023 judgment in 'All India Judges Association v. Union of India' is not present in the indexed Supreme Court corpus. LegalJarvis will not substitute unrelated precedents.",
  "citations": []
}
```

---

## 4. Limitations & Safeguards
- **Corpus Coverage**: *All India Judges Association v. Union of India* (2023) is genuinely absent from the local seed corpus. Per AGENTS.md Rule 2 and Rule 3, no fake documents or synthetic case text were created.
- **Threshold Integrity**: The $0.60$ minimum supported claim fraction and $0.25$ directional token overlap thresholds remain strictly intact.
- **Precedent Substitution Prevention**: Irrelevant legal passages are strictly rejected, ensuring high-fidelity legal research assistance.

