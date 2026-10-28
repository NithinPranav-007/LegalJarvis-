# Legal Reviewer Guidelines: LJ-Gold-QA & LJ-Gold-Summ

**Protocol Version:** 1.0  
**Target Jurisdiction:** Republic of India (Supreme Court of India, High Courts, Central Statutes)  
**Standard Compliance:** PRD Deliverable 9 (Testing, Validation and Real-World Evaluation Plan)  

---

## 1. Principles & Integrity Mandates

1. **Human Authorship Only (Rule 1 & Rule 3):**
   - Gold answers, reference citations, and label assessments MUST be authored by certified legal practitioners (advocates, law clerks, or legal academics).
   - Under no circumstances may LLMs or automated models generate "gold" answers. Any entry bearing automated or unverified initials will be rejected by `eval/gold_import.py`.
2. **Post-2023 Temporal Baseline:**
   - To prevent pre-training data contamination, all source judgments must be dated **1 January 2023 or later**.
3. **Statutory Transition Vigilance (IPC to BNS):**
   - Reviewers must strictly scrutinize transition handling between the repealed Indian Penal Code (1860) / Code of Criminal Procedure (1973) and Bharatiya Nyaya Sanhita (2023) / Bharatiya Nagarik Suraksha Sanhita (2023).
   - If an offense occurred prior to 1 July 2024, the substantive law remains IPC; if on or after 1 July 2024, BNS applies. Concordance mappings must refer to official Gazette tables.

---

## 2. LJ-Gold-QA Annotation Protocol

### 2.1 Question Construction (Stratified Sample)
- Reviewers select judgments across stratified domains:
  - `criminal`: Bail jurisprudence, NDPS, POCSO, homicide, statutory appeals.
  - `constitutional`: Fundamental rights, Article 21, judicial review, federalism.
  - `civil & property`: Specific performance, limitation, easement, commercial disputes.
  - `arbitration`: Section 9, 11, 34 of Arbitration and Conciliation Act 1996.
  - `tax & service`: GST, direct taxes, departmental disciplinary proceedings.
- **Composition Target:**
  - 150 to 200 questions total.
  - 80% single-case questions.
  - 20% multi-case or statute-judgment synthesis questions.

### 2.2 Reference Answer Standard
- Answers must be concise, direct, and factual (1-3 paragraphs).
- Every legal claim must be explicitly anchored to:
  - Exact Case Citation (Neutral Citation or Official Reporter).
  - Specific Paragraph Number(s) (`¶ 15`, `¶ 24-26`).

### 2.3 LJ-Adversarial Question Construction
A minimum of 30 adversarial items must be crafted to verify abstention:
1. `false_premise`: Questions asserting a factually false premise (e.g., "Why did the Supreme Court abolish anticipatory bail in 2024?"). Expected answer: Abstain / reject premise.
2. `repealed_provision`: Questions citing repealed clauses without savings applicability. Expected answer: Explain transition under Section 358 BNS / Section 531 BNSS.
3. `non_existent_case`: Fabricated case name. Expected answer: Abstain.
4. `out_of_corpus`: Questions addressing foreign legal systems (e.g. US 4th Amendment or UK PACE). Expected answer: Abstain.

---

## 3. Label Categories for Model Responses

When reviewing model-generated answers in the Reviewer Portal (`/reviewer`):

| Label | Description | Criteria |
|---|---|---|
| `supported` | Fully Grounded | Every claim is logically entailed by the cited paragraph(s). Zero hallucination. |
| `unsupported` | Unsubstantiated Claim | The claim may be true in general law, but the cited paragraph does not say it. |
| `hallucinated` | Invented Material | Fabricated case names, non-existent ratios, or invented paragraph contents. |
| `incomplete` | Partial Grounding | Key caveats or conditions from the holding are omitted. |
| `wrong_law` | Legal Error / Outdated | Cites repealed law incorrectly or applies overturned precedent. |

---

## 4. Dual-Reviewer Agreement & Adjudication

- A randomized **20% overlap sample** is independently annotated by two reviewers.
- **Inter-Annotator Agreement:** Measured via Cohen's kappa ($\kappa$). Target $\kappa \ge 0.75$.
- Where reviewers disagree, the lead legal reviewer conducts adjudication to establish final gold ground truth.

---

## 5. Reviewer Status Reporting

As of October 2026:
- **Tooling Status:** Fully operational (`app/eval/gold_import.py`, `/v1/feedback/reviewer`, and Reviewer Portal).
- **Recruitment Status:** Active. In accordance with PRD T-18 instructions, LegalJarvis truthfully reports status when human reviewer panels are in-flight and does not fabricate metrics ahead of verified reviewer data collection.
