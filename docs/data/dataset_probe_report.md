# Dataset Probe Report — LegalJarvis (Task T-02)

- **Probe Date**: 2026-10-28
- **Probed By**: Antigravity Lead Engineer
- **Network Mode**: BypassSandbox (verified external HTTP/HTTPS connectivity)

---

## 1. Executive Summary

| Dataset ID | Name | Provider | Access Status | Verified Size / Count | Notes |
|---|---|---|---|---|---|
| **DS-1** | Indian Supreme Court Judgments (2023) | Dattam Labs (AWS Open Data) | **accessible** | 382.33 MB (tar), 856 decisions | Real English PDFs, metadata JSON + Parquet verified |
| **DS-2** | Indian High Court Judgments | Dattam Labs (AWS Open Data) | **accessible** | Layout verified (`data/`, `metadata/`) | Breadth subset ready |
| **DS-3** | IL-TUR Benchmark & InLegalBERT | Exploration-Lab / law-ai | **accessible** | HTTP 200 on site & HF model | Evaluates PCR, SUMM, RR, LSI |
| **DS-4** | India Code Statutes | Legislative Dept / NIC | **blocked (timeout)** | Direct NIC scraping throttled | Fallback: Gazette texts & official Act PDFs |

---

## 2. Dataset DS-1: Indian Supreme Court Judgments (Year 2023)

### Observed Network Facts
- **S3 Bucket**: `s3://indian-supreme-court-judgments` (ap-south-1)
- **Direct HTTPS URL**: `https://indian-supreme-court-judgments.s3.amazonaws.com/data/tar/year=2023/english/english.tar`
- **Archive Size**: **400906240 bytes (382.33 MB / 0.373 GB)**
  - *Observation*: Well within the `MAX_DOWNLOAD_GB = 5.0 GB` limit.
- **License**: CC-BY-4.0
- **Total Decisions (Year 2023)**: **856** judgments/orders.

### Observed Schema: `metadata.parquet`
Columns observed (18 columns):
```python
['title', 'petitioner', 'respondent', 'description', 'judge', 'author_judge', 'citation', 'case_id', 'cnr', 'decision_date', 'disposal_nature', 'court', 'available_languages', 'raw_html', 'path', 'nc_display', 'scraped_at', 'year']
```

Field Datatypes & Descriptions:
- `title` (string): Case title (e.g. *ELDECO HOUSING AND INDUSTRIES LIMITED versus ASHOK VIDYARTHI AND OTHERS*)
- `petitioner` (string): Primary petitioner/appellant
- `respondent` (string): Primary respondent
- `judge` (string): Presiding bench members (e.g. *VIKRAM NATH, RAJESH BINDAL*)
- `author_judge` (string): Authoring judge where identified
- `citation` (string): Official Supreme Court Reports citation (e.g. *[2023] 16 S.C.R. 872*)
- `case_id` / `nc_display` (string): Neutral Citation (e.g. *2023 INSC 1043*)
- `cnr` (string): eCourt Case Number Record (e.g. *ESCR010008242023*)
- `decision_date` (string): Format `DD-MM-YYYY` (e.g. *30-11-2023*)
- `disposal_nature` (string): Disposal outcome (e.g. *Appeal(s) allowed*)
- `court` (string): *Supreme Court of India*
- `available_languages` (string): Comma-separated language codes (e.g. *ENG,PUN*)
- `path` (string): Base identifier matching PDF file (e.g. *2023_16_872_887*)
- `raw_html` (string): Raw eSCR search card HTML containing headnotes and coram metadata

### Observed PDF Extraction Quality (Sample of 5 Real Judgments)

#### Sample 1: `2023_7_322_346_EN.pdf`
- **File Size**: 523502 bytes (511 KB)
- **Page Count**: 25 pages
- **Native Text Layer**: Present (Readable)
- **First Page Character Count**: 1905 characters
- **Text Preview**: *"322 SUPREME CO[U2R02T3 ]R 7E PSO.CR.RT.S 322 [2023] 7 S.C.R. A CENTRAL GST DELHI - III v. DELHI INTERNATIONAL AIRPORT LTD (Civil Appeal No. 8996 of 2019) B MAY 19, 2023 [S. RAVINDR..."*

#### Sample 2: `2023_16_888_916_EN.pdf`
- **File Size**: 675902 bytes (660 KB)
- **Page Count**: 29 pages
- **Native Text Layer**: Present (Readable)
- **First Page Character Count**: 1893 characters
- **Text Preview**: *"[2023] 16 S.C.R. 888 : 2023 INSC 1048 CASE DETAILS DR. P.N. SHUKLA AND OTHERS v. UNION OF INDIA AND OTHERS (Civil Appeal No.7747 of 2012) NOVEMBER 30, 2023 [HIMA KOHLI AND RAJESH B..."*

#### Sample 3: `2023_7_26_84_EN.pdf`
- **File Size**: 635793 bytes (620 KB)
- **Page Count**: 59 pages
- **Native Text Layer**: Present (Readable)
- **First Page Character Count**: 2076 characters
- **Text Preview**: *"26 SUPREME CO U [R20T2 3R]E 7P OS.RCT.RS. 26 [2023] 7 S.C.R. A ALL INDIA JUDGES ASSOCIATION v. UNION OF INDIA & ORS. (Writ Petition (Civil) No. 643/2015) B MAY 19, 2023 [DR. DHANAN..."*

#### Sample 4: `2023_2_312_325_EN.pdf`
- **File Size**: 327553 bytes (319 KB)
- **Page Count**: 14 pages
- **Native Text Layer**: Present (Readable)
- **First Page Character Count**: 2085 characters
- **Text Preview**: *"312 SUPREME CO U [R20T2 3R]E 2P OS.RCT.RS. 312 [2023] 2 S.C.R. A NATIONAL INSURANCE COMPANY LTD. v. THE CHIEF ELECTORAL OFFICER & ORS. (Civil Appeal No.4769 of 2022) B FEBRUARY 08,..."*

#### Sample 5: `2023_16_1535_1546_EN.pdf`
- **File Size**: 301425 bytes (294 KB)
- **Page Count**: 12 pages
- **Native Text Layer**: Present (Readable)
- **First Page Character Count**: 1900 characters
- **Text Preview**: *"[2023] 16 S.C.R. 1535 : 2023 INSC 1092 CASE DETAILS ASHOK KUMAR MEWARI v. UNION OF INDIA & OTHERS (Civil Appeal No. 7956 of 2023) DECEMBER 05, 2023 [J.K. MAHESHWARI AND K.V. VISWAN..."*

---

## 3. Dataset DS-2: Indian High Court Judgments

- **Bucket**: `s3://indian-high-court-judgments`
- **Status**: Accessible without credentials.
- **Top-Level Prefixes**: `['data/', 'metadata/']`
- **Data Subprefixes**: `['data/pdf/', 'data/tar/']`
- **Subset Plan**: High Court data is reserved for Phase 3 (Delhi & Bombay High Courts) if compute and disk allow.

---

## 4. Benchmark DS-3: IL-TUR & InLegalBERT

- **Landing Page**: `https://exploration-lab.github.io/IL-TUR/` (HTTP 200)
- **Tasks Covered**: Prior Case Retrieval (PCR), Rhetorical Roles (RR), Legal Summarization (SUMM), Statute Identification (LSI).
- **Encoder**: Hugging Face `law-ai/InLegalBERT` (`law-ai/InLegalBERT`).
- **Access Status**: Open access, MIT License.

---

## 5. Dataset DS-4: India Code Statutes & Criminal Law Transition

- **Status**: Direct connection to `indiacode.nic.in` timed out (`blocked: The read operation timed out`).
- **PRD Fallback Policy**: Official statutory text for BNS (2023), BNSS (2023), BSA (2023), and IPC/CrPC will be ingested from official Ministry of Law and Justice Gazette publications and preserved under `data/raw/statutes/`.
- **Concordance Policy**: Per PRD FR-13 and AGENTS.md, concordance mappings between IPC and BNS are strictly loaded only with official source URL and legal reviewer name. No concordance rows will be fabricated by LLM generation.
