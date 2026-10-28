# Statute Sources and Concordance Provenance Report (FR-13 / T-15)

## 1. Overview
On 1 July 2024, three major criminal law enactments came into force in the Republic of India:
1. **Bharatiya Nyaya Sanhita, 2023 (Act No. 45 of 2023)** — replacing the Indian Penal Code, 1860 (Act No. 45 of 1860).
2. **Bharatiya Nagarik Suraksha Sanhita, 2023 (Act No. 46 of 2023)** — replacing the Code of Criminal Procedure, 1973 (Act No. 2 of 1974).
3. **Bharatiya Sakshya Adhiniyam, 2023 (Act No. 47 of 2023)** — replacing the Indian Evidence Act, 1872 (Act No. 1 of 1872).

Per Section 358(1) BNS, Section 531(2)(a) BNSS, and Section 170 BSA, offences committed, investigations pending, and proceedings initiated prior to 1 July 2024 continue to be governed and prosecuted under the repealed codes.

---

## 2. Official Primary Sources

| Short Name | Act Name & Number | Gazette / India Code Source URL | Status as of 1 July 2024 |
|---|---|---|---|
| **IPC** | Indian Penal Code, 1860 (Act 45 of 1860) | https://www.indiacode.nic.in/handle/123456789/2263 | **Repealed** (with savings for pre-July 2024 acts) |
| **BNS** | Bharatiya Nyaya Sanhita, 2023 (Act 45 of 2023) | https://egazette.gov.in/WriteReadData/2023/250883.pdf | **In Force** |
| **CrPC** | Code of Criminal Procedure, 1973 (Act 2 of 1974) | https://www.indiacode.nic.in/handle/123456789/16225 | **Repealed** (with savings for pre-July 2024 proceedings) |
| **BNSS** | Bharatiya Nagarik Suraksha Sanhita, 2023 (Act 46 of 2023) | https://egazette.gov.in/WriteReadData/2023/250884.pdf | **In Force** |
| **Evidence Act** | Indian Evidence Act, 1872 (Act 1 of 1872) | https://www.indiacode.nic.in/handle/123456789/15351 | **Repealed** (with savings for pre-July 2024 matters) |
| **BSA** | Bharatiya Sakshya Adhiniyam, 2023 (Act 47 of 2023) | https://egazette.gov.in/WriteReadData/2023/250885.pdf | **In Force** |

---

## 3. Strict Non-Fabrication Concordance Protocol (Rule 3)
In compliance with Rule 3 of the Antigravity Master Execution Prompt and PRD FR-13:
1. **No Model Recall Concordance:** Concordance mappings between repealed codes (IPC/CrPC/Evidence Act) and new codes (BNS/BNSS/BSA) are **strictly forbidden** from being hallucinated or inferred by LLM weights.
2. **Reviewer Signature Mandatory:** Every entry in `statute_concordance` requires:
   - `source_url`: Official Gazette of India URL or Parliamentary Standing Committee Report URL.
   - `reviewed_by`: Initials or Identifier of a qualified legal practitioner/reviewer who inspected the statutory texts.
   - `reviewed_at`: ISO timestamp of certification.
   - `note`: Detailed notes on changes in scope, punishment, or subsections.
3. **Absence Handling:** If a section does not have an officially certified reviewer mapping, the system reports:
   > *"No verified concordance mapping has been officially certified by a legal reviewer for this section. LegalJarvis does not guess or invent mappings."*
   The table remains clean and empty for that row.
