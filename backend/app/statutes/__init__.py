"""LegalJarvis Statutes, Versioning, and Concordance package (Task T-15 / FR-13)."""

from app.statutes.versions import (
    CRIMINAL_LAW_TRANSITION_DATE,
    generate_transition_notice,
    get_statute_status_at_date,
)

__all__ = [
    "CRIMINAL_LAW_TRANSITION_DATE",
    "generate_transition_notice",
    "get_statute_status_at_date",
]
