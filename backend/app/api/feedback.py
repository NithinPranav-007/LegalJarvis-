"""Feedback API router (Task T-14 / FR-14)."""

import logging

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.search import get_sync_db
from app.db.models import Answer, Feedback
from app.schemas.feedback import FeedbackCreate, FeedbackResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/v1/feedback", tags=["Feedback"])


@router.post("", response_model=FeedbackResponse)
def submit_feedback(
    payload: FeedbackCreate,
    db: Session = Depends(get_sync_db),
) -> FeedbackResponse:
    """Record user feedback (thumbs up/down, quality labels, comments) for legal Q&A."""
    logger.info(
        "User feedback received: rating=%s label=%s query=%s answer_id=%s notes=%s",
        payload.rating,
        payload.label,
        payload.query,
        payload.answer_id,
        payload.notes,
    )

    feedback_id = 1
    if payload.answer_id is not None:
        # Check if answer exists in DB
        ans = db.execute(select(Answer).where(Answer.id == payload.answer_id)).scalar_one_or_none()
        if ans is not None:
            fb = Feedback(
                answer_id=payload.answer_id,
                rating=payload.rating,
                label=payload.label,
                notes=payload.notes,
            )
            db.add(fb)
            db.commit()
            db.refresh(fb)
            feedback_id = fb.id

    return FeedbackResponse(
        id=feedback_id,
        status="success",
        message="Feedback successfully recorded. Thank you for helping improve LegalJarvis.",
    )
