"""Statute reference extraction and linking for judgments (Task T-15 / FR-13)."""

import re

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import Statute, StatuteReference, StatuteSection, StatuteVersion

# Regex pattern matching references like "Section 302 IPC", "Section 438 of the Code of Criminal Procedure", etc.
STATUTE_REF_PATTERN = re.compile(
    r"(?:Section|Sec\.|s\.)\s*(\d+[A-Z]?)\s*(?:of\s*(?:the\s*)?)?(IPC|Indian Penal Code|CrPC|Code of Criminal Procedure|BNS|Bharatiya Nyaya Sanhita|BNSS|Bharatiya Nagarik Suraksha Sanhita|Evidence Act|Indian Evidence Act|BSA|Bharatiya Sakshya Adhiniyam)",
    re.IGNORECASE,
)

CANONICAL_CODE_MAP = {
    "IPC": "IPC",
    "INDIAN PENAL CODE": "IPC",
    "CRPC": "CrPC",
    "CODE OF CRIMINAL PROCEDURE": "CrPC",
    "BNS": "BNS",
    "BHARATIYA NYAYA SANHITA": "BNS",
    "BNSS": "BNSS",
    "BHARATIYA NAGARIK SURAKSHA SANHITA": "BNSS",
    "EVIDENCE ACT": "Evidence Act",
    "INDIAN EVIDENCE ACT": "Evidence Act",
    "BSA": "BSA",
    "BHARATIYA SAKSHYA ADHINIYAM": "BSA",
}


def extract_statute_references(text: str) -> list[dict[str, str]]:
    """Extract all statutory section references from judgment text."""
    matches = STATUTE_REF_PATTERN.findall(text)
    references = []
    seen = set()

    for sec_no, code_raw in matches:
        canon_code = CANONICAL_CODE_MAP.get(code_raw.upper().strip())
        if canon_code:
            key = (canon_code, sec_no.upper().strip())
            if key not in seen:
                seen.add(key)
                references.append(
                    {
                        "statute_code": canon_code,
                        "section_no": sec_no.upper().strip(),
                    }
                )

    return references


def link_statute_references_to_document(
    db: Session,
    document_id: int,
    text: str,
) -> list[StatuteReference]:
    """Extract statute references from text and register in statute_references table."""
    refs = extract_statute_references(text)
    linked = []

    for ref in refs:
        # Locate statute section in DB
        sec = (
            db.execute(
                select(StatuteSection)
                .join(StatuteVersion, StatuteSection.version_id == StatuteVersion.id)
                .join(Statute, StatuteVersion.statute_id == Statute.id)
                .where(
                    Statute.short_name == ref["statute_code"],
                    StatuteSection.section_no == ref["section_no"],
                )
            )
            .scalars()
            .first()
        )

        if sec:
            existing = db.execute(
                select(StatuteReference).where(
                    StatuteReference.document_id == document_id,
                    StatuteReference.section_id == sec.id,
                )
            ).scalar_one_or_none()

            if not existing:
                stat_ref = StatuteReference(
                    document_id=document_id,
                    section_id=sec.id,
                )
                db.add(stat_ref)
                linked.append(stat_ref)

    if linked:
        db.commit()

    return linked
