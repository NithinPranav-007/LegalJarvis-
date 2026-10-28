"""Query analysis detecting statutory mentions and transitional criminal law notices (Task T-11 / FR-05, FR-13)."""

import re
from dataclasses import dataclass, field

# Notice text mandated by PRD Section D3 / FR-13 and Part F
CRIMINAL_TRANSITION_NOTICE = (
    "Notice: Criminal laws in India underwent major reform on 1 July 2024. "
    "The Bharatiya Nyaya Sanhita (BNS), Bharatiya Nagarik Suraksha Sanhita (BNSS), and "
    "Bharatiya Sakshya Adhiniyam (BSA) came into force on 1 July 2024. "
    "For offences or proceedings initiated prior to 1 July 2024, the Indian Penal Code (IPC), "
    "Code of Criminal Procedure (CrPC), and Indian Evidence Act continue to govern under transitional provisions."
)

RE_SECTION = re.compile(
    r"\bsection\s+(\d+[a-zA-Z]*(?:\([a-zA-Z0-9]+\))*)",
    re.IGNORECASE,
)
RE_IPC = re.compile(r"\b(ipc|indian\s+penal\s+code)\b", re.IGNORECASE)
RE_CRPC = re.compile(r"\b(crpc|code\s+of\s+criminal\s+procedure)\b", re.IGNORECASE)
RE_EVIDENCE = re.compile(r"\b(evidence\s+act|indian\s+evidence\s+act|bsa)\b", re.IGNORECASE)
RE_BNS = re.compile(r"\b(bns|bharatiya\s+nyaya\s+sanhita)\b", re.IGNORECASE)
RE_BNSS = re.compile(r"\b(bnss|bharatiya\s+nagarik\s+suraksha\s+sanhita)\b", re.IGNORECASE)

RE_YEAR = re.compile(r"\b(19\d{2}|20[0-2]\d)\b")


@dataclass
class QueryAnalysisResult:
    clean_query: str
    detected_sections: list[str] = field(default_factory=list)
    detected_statutes: list[str] = field(default_factory=list)
    requires_criminal_notice: bool = False
    notice_text: str | None = None
    detected_years: list[int] = field(default_factory=list)


def analyze_query(query: str) -> QueryAnalysisResult:
    """Analyze query for statutory references, years, and criminal transition applicability."""
    q_lower = query.lower()
    sections = [m.group(1) for m in RE_SECTION.finditer(query)]
    statutes: list[str] = []

    is_ipc = bool(RE_IPC.search(q_lower))
    is_crpc = bool(RE_CRPC.search(q_lower))
    is_evidence = bool(RE_EVIDENCE.search(q_lower))
    is_bns = bool(RE_BNS.search(q_lower))
    is_bnss = bool(RE_BNSS.search(q_lower))

    if is_ipc:
        statutes.append("Indian Penal Code, 1860")
    if is_crpc:
        statutes.append("Code of Criminal Procedure, 1973")
    if is_evidence:
        statutes.append("Indian Evidence Act, 1872")
    if is_bns:
        statutes.append("Bharatiya Nyaya Sanhita, 2023")
    if is_bnss:
        statutes.append("Bharatiya Nagarik Suraksha Sanhita, 2023")

    requires_notice = is_ipc or is_crpc or is_evidence or is_bns or is_bnss
    notice = CRIMINAL_TRANSITION_NOTICE if requires_notice else None

    raw_years = [int(m.group(1)) for m in RE_YEAR.finditer(query)]
    # Keep plausible modern legal judgment years
    years = [y for y in raw_years if 1950 <= y <= 2030]

    return QueryAnalysisResult(
        clean_query=query.strip(),
        detected_sections=sections,
        detected_statutes=statutes,
        requires_criminal_notice=requires_notice,
        notice_text=notice,
        detected_years=years,
    )
