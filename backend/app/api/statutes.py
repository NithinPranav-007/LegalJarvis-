"""Statutes and Concordance API router (Task T-15 / FR-13)."""

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.api.search import get_sync_db
from app.db.models import Statute, StatuteSection, StatuteVersion
from app.statutes.concordance import (
    ConcordanceImportSchema,
    import_concordance_entry,
    lookup_concordance,
)
from app.statutes.versions import generate_transition_notice, get_statute_status_at_date

router = APIRouter(prefix="/v1/statutes", tags=["Statutes"])


@router.get("", response_model=list[dict[str, Any]])
def list_statutes(db: Session = Depends(get_sync_db)) -> list[dict[str, Any]]:
    """List all registered central acts with active legal status and versions."""
    statutes = db.execute(select(Statute).options(selectinload(Statute.versions))).scalars().all()
    results = []
    for s in statutes:
        latest_version = s.versions[-1] if s.versions else None
        results.append(
            {
                "id": s.id,
                "short_name": s.short_name,
                "act_year": s.act_year,
                "act_no": s.act_no,
                "source_url": s.source_url,
                "current_status": get_statute_status_at_date(s.short_name),
                "versions_count": len(s.versions),
                "effective_from": latest_version.effective_from.isoformat()
                if latest_version
                else None,
                "effective_to": latest_version.effective_to.isoformat()
                if latest_version and latest_version.effective_to
                else None,
            }
        )
    return results


@router.get("/lookup")
def lookup_statute_section(
    statute_code: str = Query(..., description="Statute code, e.g. IPC, BNS, CrPC"),
    section_no: str = Query(..., description="Section number, e.g. 302, 103, 438"),
    db: Session = Depends(get_sync_db),
) -> dict[str, Any]:
    """Look up a statute provision, legal status, transition notice, and verified concordance."""
    clean_code = statute_code.upper().strip()
    clean_sec = section_no.upper().strip()

    # Locate section in DB
    sec = (
        db.execute(
            select(StatuteSection)
            .join(StatuteVersion, StatuteSection.version_id == StatuteVersion.id)
            .join(Statute, StatuteVersion.statute_id == Statute.id)
            .where(
                func.upper(Statute.short_name) == clean_code,
                StatuteSection.section_no == clean_sec,
            )
        )
        .scalars()
        .first()
    )

    # Generate temporal transition notice
    transition = generate_transition_notice(clean_code, clean_sec)

    # Concordance lookup
    concordance = lookup_concordance(db, clean_code, clean_sec)

    return {
        "statute_code": clean_code,
        "section_no": clean_sec,
        "found_in_database": sec is not None,
        "heading": sec.heading if sec else None,
        "text": sec.text if sec else None,
        "current_status": get_statute_status_at_date(clean_code),
        "transition_notice": transition,
        "concordance": concordance,
    }


@router.post("/concordance/import")
def import_concordance(
    payload: ConcordanceImportSchema,
    db: Session = Depends(get_sync_db),
) -> dict[str, Any]:
    """Reviewer workflow: import verified concordance row with source and reviewer signatures."""
    try:
        concordance = import_concordance_entry(db, payload)
        return {
            "status": "success",
            "message": "Concordance row successfully imported and certified.",
            "source_url": concordance.source_url,
            "reviewed_by": concordance.reviewed_by,
            "reviewed_at": concordance.reviewed_at.isoformat(),
        }
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e)) from e
