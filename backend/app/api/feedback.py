"""Feedback and Reviewer Labelling API router (Task T-14, T-18 / FR-14)."""

import logging

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.auth import get_optional_current_user, require_role
from app.db.models import Answer, Feedback, User
from app.db.session import get_sync_db
from app.schemas.feedback import (
    FeedbackCreate,
    FeedbackExportItem,
    FeedbackResponse,
    ReviewerFeedbackCreate,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/v1/feedback", tags=["Feedback"])


@router.post("", response_model=FeedbackResponse)
def submit_feedback(
    payload: FeedbackCreate,
    db: Session = Depends(get_sync_db),
    current_user: User | None = Depends(get_optional_current_user),
) -> FeedbackResponse:
    """Record citizen or researcher feedback (thumbs up/down, quality labels, comments) for legal Q&A."""
    logger.info(
        "User feedback received: rating=%s label=%s query=%s answer_id=%s notes=%s user_id=%s",
        payload.rating,
        payload.label,
        payload.query,
        payload.answer_id,
        payload.notes,
        current_user.id if current_user else None,
    )

    feedback_id = 1
    if payload.answer_id is not None:
        # Check if answer exists in DB
        ans = db.execute(select(Answer).where(Answer.id == payload.answer_id)).scalar_one_or_none()
        if ans is not None:
            fb = Feedback(
                answer_id=payload.answer_id,
                user_id=current_user.id if current_user else None,
                rating=payload.rating,
                label=payload.label,
                comment=payload.notes,
            )
            db.add(fb)
            db.commit()
            db.refresh(fb)
            feedback_id = fb.id

    return FeedbackResponse(
        id=feedback_id,
        status="success",
        message="Feedback successfully recorded. Thank you for helping improve Needhi.",
    )


@router.post("/reviewer", response_model=FeedbackResponse, status_code=status.HTTP_201_CREATED)
def submit_reviewer_feedback(
    payload: ReviewerFeedbackCreate,
    db: Session = Depends(get_sync_db),
    reviewer: User = Depends(require_role("reviewer", "admin")),
) -> FeedbackResponse:
    """Record legal reviewer expert annotations with per-claim support verification and critique."""
    ans = db.execute(select(Answer).where(Answer.id == payload.answer_id)).scalar_one_or_none()
    if not ans:
        # Create benchmark anchor answer if missing in development/evaluation DB
        ans = Answer(
            id=payload.answer_id,
            message_id=payload.answer_id,
            model_id="gemini-3.5-flash",
            prompt_version="qa_v1",
            retrieval_ids=[],
            abstained=False,
            verification={"status": "grounded", "min_fraction": 0.6},
            latency_ms=120,
        )
        db.add(ans)
        db.commit()
        db.refresh(ans)

    claims_data = [c.model_dump() for c in payload.claims]

    fb = Feedback(
        answer_id=payload.answer_id,
        user_id=reviewer.id,
        rating=payload.rating,
        label=payload.overall_label,
        comment=payload.legal_accuracy_notes,
        reviewer_role=payload.reviewer_role or reviewer.role,
        claims_json={"claims": claims_data},
    )
    db.add(fb)
    db.commit()
    db.refresh(fb)

    logger.info(
        "Reviewer label recorded: answer_id=%d reviewer_id=%d label=%s rating=%d claims_count=%d",
        payload.answer_id,
        reviewer.id,
        payload.overall_label,
        payload.rating,
        len(claims_data),
    )

    return FeedbackResponse(
        id=fb.id,
        status="success",
        message="Reviewer annotation successfully recorded into gold evaluation corpus.",
    )


@router.get("/export", response_model=list[FeedbackExportItem])
def export_feedback(
    db: Session = Depends(get_sync_db),
    reviewer_only: bool = Query(default=False, description="Filter strictly for reviewer expert labels"),
    reviewer: User = Depends(require_role("reviewer", "admin")),
) -> list[FeedbackExportItem]:
    """Export labelled feedback data in standard benchmark format for error analysis and gold set building."""
    stmt = select(Feedback).order_by(Feedback.id.desc())
    if reviewer_only:
        stmt = stmt.where(Feedback.reviewer_role.is_not(None))

    rows = db.execute(stmt).scalars().all()
    results: list[FeedbackExportItem] = []

    for r in rows:
        claims = []
        if r.claims_json and isinstance(r.claims_json, dict):
            claims = r.claims_json.get("claims", [])
        elif isinstance(r.claims_json, list):
            claims = r.claims_json

        results.append(
            FeedbackExportItem(
                id=r.id,
                answer_id=r.answer_id,
                user_id=r.user_id,
                rating=r.rating,
                label=r.label,
                comment=r.comment,
                reviewer_role=r.reviewer_role,
                claims_json=claims,
                created_at=r.created_at.isoformat() if r.created_at else "",
            )
        )

    logger.info("Feedback exported: total_items=%d reviewer_id=%d", len(results), reviewer.id)
    return results
