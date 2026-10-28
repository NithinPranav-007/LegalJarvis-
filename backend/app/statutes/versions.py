"""Statute versioning and criminal law transition notice generator (Task T-15 / FR-13)."""

import datetime
from typing import Any

# Official date of enforcement for Bharatiya Nyaya Sanhita (BNS),
# Bharatiya Nagarik Suraksha Sanhita (BNSS), and Bharatiya Sakshya Adhiniyam (BSA)
CRIMINAL_LAW_TRANSITION_DATE = datetime.date(2024, 7, 1)

REPEALED_CODES_MAP: dict[str, dict[str, str]] = {
    "IPC": {
        "full_name": "Indian Penal Code, 1860",
        "replacing_code": "Bharatiya Nyaya Sanhita, 2023 (BNS)",
        "replacing_short": "BNS",
        "savings_clause": "Section 358(1) of Bharatiya Nyaya Sanhita, 2023",
        "savings_rule": "Offences committed prior to 1 July 2024 remain punishable and triable under the Indian Penal Code, 1860.",
    },
    "CrPC": {
        "full_name": "Code of Criminal Procedure, 1973",
        "replacing_code": "Bharatiya Nagarik Suraksha Sanhita, 2023 (BNSS)",
        "replacing_short": "BNSS",
        "savings_clause": "Section 531(2)(a) of Bharatiya Nagarik Suraksha Sanhita, 2023",
        "savings_rule": "Investigations, inquiries, trials, and appeals pending immediately before 1 July 2024 continue under the Code of Criminal Procedure, 1973.",
    },
    "Evidence Act": {
        "full_name": "Indian Evidence Act, 1872",
        "replacing_code": "Bharatiya Sakshya Adhiniyam, 2023 (BSA)",
        "replacing_short": "BSA",
        "savings_clause": "Section 170 of Bharatiya Sakshya Adhiniyam, 2023",
        "savings_rule": "Proceedings, rights, obligations, or liabilities commenced or acquired prior to 1 July 2024 remain governed by the Indian Evidence Act, 1872.",
    },
}

NEW_CODES_MAP: dict[str, str] = {
    "BNS": "Bharatiya Nyaya Sanhita, 2023",
    "BNSS": "Bharatiya Nagarik Suraksha Sanhita, 2023",
    "BSA": "Bharatiya Sakshya Adhiniyam, 2023",
}


def get_statute_status_at_date(
    short_name: str,
    query_date: datetime.date | None = None,
) -> str:
    """Determine operational legal status ('in_force', 'repealed', or 'not_yet_in_force') at a given date."""
    ref_date = query_date or datetime.date.today()
    normalized = short_name.upper().strip()

    if normalized in ["IPC", "CRPC", "EVIDENCE ACT", "IEA"]:
        if ref_date >= CRIMINAL_LAW_TRANSITION_DATE:
            return "repealed"
        return "in_force"

    if normalized in ["BNS", "BNSS", "BSA"]:
        if ref_date < CRIMINAL_LAW_TRANSITION_DATE:
            return "not_yet_in_force"
        return "in_force"

    # Default assumed in-force for general Central Statutes unless explicitly marked
    return "in_force"


def generate_transition_notice(
    short_name: str,
    section_no: str | None = None,
    date_of_incident: datetime.date | None = None,
) -> dict[str, Any]:
    """Generate statutory transition advice strictly adhering to Gazette notifications (FR-13)."""
    norm = short_name.strip()
    lookup_key = None
    if norm.upper() in ["IPC", "INDIAN PENAL CODE"]:
        lookup_key = "IPC"
    elif norm.upper() in ["CRPC", "CODE OF CRIMINAL PROCEDURE"]:
        lookup_key = "CrPC"
    elif norm.upper() in ["EVIDENCE ACT", "INDIAN EVIDENCE ACT", "IEA"]:
        lookup_key = "Evidence Act"

    if not lookup_key:
        return {
            "has_transition": False,
            "notice": None,
        }

    meta = REPEALED_CODES_MAP[lookup_key]
    section_prefix = f"Section {section_no} of " if section_no else ""

    notice_text = (
        f"Statutory Transition Notice: {section_prefix}{meta['full_name']} was repealed with effect from "
        f"1 July 2024 and replaced by the {meta['replacing_code']}. "
        f"Under {meta['savings_clause']}, {meta['savings_rule']}"
    )

    if date_of_incident:
        if date_of_incident < CRIMINAL_LAW_TRANSITION_DATE:
            applicability = f"Old Code Applicable: Incident date ({date_of_incident}) predates 1 July 2024. Governed by {meta['full_name']}."
        else:
            applicability = f"New Code Applicable: Incident date ({date_of_incident}) is on or after 1 July 2024. Governed by {meta['replacing_code']}."
    else:
        applicability = "Check incident date: Offences or proceedings prior to 1 July 2024 continue under old law; acts on or after 1 July 2024 fall under new Sanhita."

    return {
        "has_transition": True,
        "old_statute": meta["full_name"],
        "replacing_statute": meta["replacing_code"],
        "replacing_short": meta["replacing_short"],
        "transition_date": CRIMINAL_LAW_TRANSITION_DATE.isoformat(),
        "savings_clause": meta["savings_clause"],
        "notice": notice_text,
        "applicability_guidance": applicability,
    }
