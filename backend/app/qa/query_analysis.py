"""Query analysis detecting statutory mentions, case names, neutral citations, and transitional criminal law notices (Task T-11 / FR-05, FR-13)."""

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
RE_TARGET_YEAR = re.compile(r"\b(19\d{2}|20[0-2]\d)\s+(?:judgment|order|ruling|decision|case)\b", re.IGNORECASE)

RE_NEUTRAL_CITATION = re.compile(r"\b(\d{4}\s+INSC\s+\d+)\b", re.IGNORECASE)
RE_SCC_CITATION = re.compile(r"\b(?:\(\d{4}\)|\d{4})\s+\d+\s+SCC\s+\d+\b", re.IGNORECASE)
RE_AIR_CITATION = re.compile(r"\bAIR\s+\d{4}\s+SC\s+\d+\b", re.IGNORECASE)

ASPECT_KEYWORDS = {
    "legal issue": ["legal issue", "issue", "question of law", "matter in issue"],
    "reasoning": ["reasoning", "reasons", "rationale", "grounds", "court's reasoning"],
    "decision": ["decision", "final decision", "holding", "order", "decree", "outcome"],
}


@dataclass
class QueryAnalysisResult:
    clean_query: str
    detected_sections: list[str] = field(default_factory=list)
    detected_statutes: list[str] = field(default_factory=list)
    requires_criminal_notice: bool = False
    notice_text: str | None = None
    detected_years: list[int] = field(default_factory=list)
    target_case_name: str | None = None
    target_citations: list[str] = field(default_factory=list)
    target_year: int | None = None
    requested_aspects: list[str] = field(default_factory=list)


def extract_target_case_name(query: str) -> str | None:
    """Extract legal case title (e.g. 'Party A v. Party B') from query."""
    v_match = re.search(r"\b(?:v\.|vs\.|versus|v)\s+", query, re.IGNORECASE)
    if not v_match:
        return None

    v_start, v_end = v_match.span()
    before_text = query[:v_start].strip()
    after_text = query[v_end:].strip()

    # Party 1 is typically preceded by phrases like 'judgment in', 'in ', 'case of ', or sentence start
    p1_m = re.search(
        r"(?:(?:judgment|order|ruling|decision|case|matter)\s+in\s+|case\s+of\s+|matter\s+of\s+|\bin\s+)?([A-Z][A-Za-z0-9\s.,'()\-&]+)$",
        before_text,
        re.IGNORECASE,
    )
    p1 = p1_m.group(1).strip() if p1_m else ""

    # If there is 'judgment in', 'case of', 'in ', take whatever comes after
    after_prefix = re.search(
        r"(?:(?:judgment|order|ruling|decision|case|matter|guidelines|holding|ratio)\s+(?:in|of|on)|decide\s+in|hold\s+in|\bin)\s+([A-Z].*)$",
        p1,
        re.IGNORECASE,
    )
    if after_prefix:
        p1 = after_prefix.group(1).strip()

    # Strip any leading prepositions, articles, or dates
    p1_clean = re.sub(r"^(?:in|regarding|about|for|the|\d{4})\s+", "", p1, flags=re.IGNORECASE).strip()

    # Party 2 ends at punctuation (. , ; ? !) or stop keywords
    p2_m = re.search(
        r"^([A-Z][A-Za-z0-9\s.,'()\-&]+?)(?=[.,;!?]|\s+(?:judgment|order|ruling|case|corpus|decision|para|\d{4}|\bexplain\b|\bwhat\b|\bhow\b|\busing\b|\bheld\b|\bconcerning\b|\bregarding\b|\bwhen\b|\bunder\b|\bfor\b)|\Z)",
        after_text,
        re.IGNORECASE,
    )
    p2 = p2_m.group(1).strip() if p2_m else ""

    if p1_clean and p2 and len(p1_clean) >= 2 and len(p2) >= 2:
        v_str = query[v_start:v_end].strip()
        return f"{p1_clean} {v_str} {p2}"

    return None


def extract_target_citations(query: str) -> list[str]:
    """Extract standard Indian legal citations from query."""
    citations: list[str] = []
    for m in RE_NEUTRAL_CITATION.finditer(query):
        citations.append(m.group(0).strip())
    for m in RE_SCC_CITATION.finditer(query):
        citations.append(m.group(0).strip())
    for m in RE_AIR_CITATION.finditer(query):
        citations.append(m.group(0).strip())
    return citations


def extract_target_year(query: str, detected_years: list[int]) -> int | None:
    """Identify if a specific year is explicitly designated as the case/judgment year."""
    m = RE_TARGET_YEAR.search(query)
    if m:
        return int(m.group(1))

    # If only one plausible year is mentioned in the entire query, assume it's the target year
    if len(detected_years) == 1:
        return detected_years[0]

    return None


def extract_requested_aspects(query: str) -> list[str]:
    """Detect which aspects of the judgment were requested (e.g. issues, reasoning, decision)."""
    q_lower = query.lower()
    aspects = []
    for aspect_name, keywords in ASPECT_KEYWORDS.items():
        if any(kw in q_lower for kw in keywords):
            aspects.append(aspect_name)
    return aspects


def analyze_query(query: str) -> QueryAnalysisResult:
    """Analyze query for statutory references, years, case names, citations, and criminal transition applicability."""
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

    target_case = extract_target_case_name(query)
    target_citations = extract_target_citations(query)
    target_year = extract_target_year(query, years)
    aspects = extract_requested_aspects(query)

    return QueryAnalysisResult(
        clean_query=query.strip(),
        detected_sections=sections,
        detected_statutes=statutes,
        requires_criminal_notice=requires_notice,
        notice_text=notice,
        detected_years=years,
        target_case_name=target_case,
        target_citations=target_citations,
        target_year=target_year,
        requested_aspects=aspects,
    )
