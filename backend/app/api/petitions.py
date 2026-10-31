"""FastAPI router for Petition Generator (Task T-19 / Indian Legal Petition Architecture)."""

import json
from typing import Any
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import StreamingResponse
from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.api.auth import get_optional_current_user
from app.db.models import Petition, User
from app.db.session import get_sync_db
from app.petitions.exporter import export_petition_docx, export_petition_pdf
from app.petitions.generator import generate_petition_draft, regenerate_single_section
from app.schemas.petitions import (
    PetitionCreateRequest,
    PetitionDraftListItem,
    PetitionResponse,
    PetitionUpdateRequest,
    SectionRegenerateRequest,
    SectionRegenerateResponse,
)

router = APIRouter(prefix="/v1/petitions", tags=["Petition Generator"])


@router.post("/generate", response_model=PetitionResponse)
def generate_petition(
    payload: PetitionCreateRequest,
    db: Session = Depends(get_sync_db),
    user: User | None = Depends(get_optional_current_user),
) -> PetitionResponse:
    """Generate structured legal petition draft grounded in Indian case law and statutory templates."""
    try:
        response = generate_petition_draft(db=db, payload=payload)

        # Automatically persist initial draft to database
        db_petition = Petition(
            user_id=user.id if user else None,
            title=response.title,
            petition_type=payload.petition_type,
            court_level=payload.court_level,
            court_name=payload.court_name,
            state_ut=payload.state_ut,
            category=payload.category,
            case_number=payload.case_number,
            statutory_provisions=payload.statutory_provisions,
            petitioner_details=[p.model_dump() for p in payload.petitioners],
            respondent_details=[r.model_dump() for r in payload.respondents],
            facts_chronology={
                "dispute_background": payload.dispute_background,
                "events": [e.model_dump() for e in payload.events],
                "previous_orders": [o.model_dump() for o in payload.previous_orders],
                "annexures": [a.model_dump() for a in payload.annexures],
            },
            legal_grounds={
                "grounds": payload.grounds,
                "rights_infringed": payload.rights_infringed,
                "statutes_applied": payload.statutes_applied,
                "urgency_reason": payload.urgency_reason,
                "limitation_explanation": payload.limitation_explanation,
            },
            prayer_relief={
                "main_prayers": payload.main_prayers,
                "interim_prayers": payload.interim_prayers,
            },
            generated_document=response.sections,
            citations=[c.model_dump() for c in response.citations],
            verification_warnings=response.verification_warnings,
            status="generated",
        )
        db.add(db_petition)
        db.commit()
        db.refresh(db_petition)

        response.id = db_petition.id
        response.created_at = db_petition.created_at.isoformat() if db_petition.created_at else None
        response.updated_at = db_petition.updated_at.isoformat() if db_petition.updated_at else None
        return response

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Petition drafting failed: {str(e)}",
        )


@router.get("", response_model=list[PetitionDraftListItem])
def list_petition_drafts(
    petition_type: str | None = Query(None, description="Optional filter by petition type"),
    limit: int = Query(30, ge=1, le=100),
    db: Session = Depends(get_sync_db),
    user: User | None = Depends(get_optional_current_user),
) -> list[PetitionDraftListItem]:
    """List recent saved petition drafts."""
    query = select(Petition)
    if user:
        # If authenticated, show user's drafts or public drafts
        query = query.filter((Petition.user_id == user.id) | (Petition.user_id.is_(None)))
    if petition_type:
        query = query.filter(Petition.petition_type == petition_type)

    query = query.order_by(desc(Petition.updated_at)).limit(limit)
    rows = db.scalars(query).all()

    items = []
    for r in rows:
        p_name = r.petitioner_details[0].get("name", "Petitioner") if r.petitioner_details else "Petitioner"
        r_name = r.respondent_details[0].get("name", "Respondent") if r.respondent_details else "Respondent"
        items.append(
            PetitionDraftListItem(
                id=r.id,
                title=r.title,
                petition_type=r.petition_type,
                court_name=r.court_name,
                petitioner_name=p_name,
                respondent_name=r_name,
                status=r.status,
                created_at=r.created_at.isoformat() if r.created_at else "",
                updated_at=r.updated_at.isoformat() if r.updated_at else "",
            )
        )
    return items


@router.get("/{petition_id}", response_model=PetitionResponse)
def get_petition_draft(
    petition_id: int,
    db: Session = Depends(get_sync_db),
    user: User | None = Depends(get_optional_current_user),
) -> PetitionResponse:
    """Retrieve full saved petition draft by ID."""
    p = db.scalar(select(Petition).filter_by(id=petition_id))
    if not p:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Petition draft not found")

    sections = p.generated_document or {}
    full_text = "\n\n" + ("=" * 70) + "\n\n".join(sections.values())

    return PetitionResponse(
        id=p.id,
        title=p.title,
        petition_type=p.petition_type,
        court_level=p.court_level,
        court_name=p.court_name,
        state_ut=p.state_ut,
        category=p.category,
        case_number=p.case_number,
        sections=sections,
        full_text=full_text,
        citations=p.citations or [],
        verification_warnings=p.verification_warnings or [],
        status=p.status,
        created_at=p.created_at.isoformat() if p.created_at else None,
        updated_at=p.updated_at.isoformat() if p.updated_at else None,
    )


@router.put("/{petition_id}", response_model=PetitionResponse)
def update_petition_draft(
    petition_id: int,
    payload: PetitionUpdateRequest,
    db: Session = Depends(get_sync_db),
    user: User | None = Depends(get_optional_current_user),
) -> PetitionResponse:
    """Update sections, title, or status of an existing petition draft."""
    p = db.scalar(select(Petition).filter_by(id=petition_id))
    if not p:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Petition draft not found")

    if payload.title is not None:
        p.title = payload.title
    if payload.status is not None:
        p.status = payload.status
    if payload.sections is not None:
        p.generated_document = payload.sections

    db.commit()
    db.refresh(p)

    sections = p.generated_document or {}
    full_text = payload.full_text or ("\n\n" + ("=" * 70) + "\n\n".join(sections.values()))

    return PetitionResponse(
        id=p.id,
        title=p.title,
        petition_type=p.petition_type,
        court_level=p.court_level,
        court_name=p.court_name,
        state_ut=p.state_ut,
        category=p.category,
        case_number=p.case_number,
        sections=sections,
        full_text=full_text,
        citations=p.citations or [],
        verification_warnings=p.verification_warnings or [],
        status=p.status,
        created_at=p.created_at.isoformat() if p.created_at else None,
        updated_at=p.updated_at.isoformat() if p.updated_at else None,
    )


@router.delete("/{petition_id}", status_code=status.HTTP_200_OK)
def delete_petition_draft(
    petition_id: int,
    db: Session = Depends(get_sync_db),
    user: User | None = Depends(get_optional_current_user),
) -> dict[str, Any]:
    """Delete saved petition draft."""
    p = db.scalar(select(Petition).filter_by(id=petition_id))
    if not p:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Petition draft not found")

    db.delete(p)
    db.commit()
    return {"status": "deleted", "id": petition_id, "message": "Draft successfully deleted"}


@router.post("/regenerate-section", response_model=SectionRegenerateResponse)
def regenerate_section(
    payload: SectionRegenerateRequest,
    db: Session = Depends(get_sync_db),
) -> SectionRegenerateResponse:
    """Regenerate a single specific section of a petition draft without affecting other sections."""
    return regenerate_single_section(db=db, request=payload)


@router.get("/{petition_id}/export/docx")
def export_saved_petition_docx(
    petition_id: int,
    db: Session = Depends(get_sync_db),
):
    """Download saved petition as genuine DOCX with Indian court styling."""
    p = db.scalar(select(Petition).filter_by(id=petition_id))
    if not p:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Petition draft not found")

    sections = p.generated_document or {}
    buffer = export_petition_docx(sections=sections, title=p.title)

    filename = f"{p.petition_type}_{p.id}_{2026}.docx"
    return StreamingResponse(
        buffer,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/{petition_id}/export/pdf")
def export_saved_petition_pdf(
    petition_id: int,
    db: Session = Depends(get_sync_db),
):
    """Download saved petition as genuine PDF with running headers and verification block."""
    p = db.scalar(select(Petition).filter_by(id=petition_id))
    if not p:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Petition draft not found")

    sections = p.generated_document or {}
    buffer = export_petition_pdf(sections=sections, title=p.title)

    filename = f"{p.petition_type}_{p.id}_{2026}.pdf"
    return StreamingResponse(
        buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.post("/export/direct-docx")
def export_direct_docx(
    payload: dict[str, Any],
):
    """Export currently edited sections directly to DOCX."""
    sections = payload.get("sections", {})
    title = payload.get("title", "Needhi_Petition_Draft")
    buffer = export_petition_docx(sections=sections, title=title)
    return StreamingResponse(
        buffer,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={"Content-Disposition": 'attachment; filename="Needhi_Petition_Draft.docx"'},
    )


@router.post("/export/direct-pdf")
def export_direct_pdf(
    payload: dict[str, Any],
):
    """Export currently edited sections directly to PDF."""
    sections = payload.get("sections", {})
    title = payload.get("title", "Needhi_Petition_Draft")
    buffer = export_petition_pdf(sections=sections, title=title)
    return StreamingResponse(
        buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": 'attachment; filename="Needhi_Petition_Draft.pdf"'},
    )
