"""Summarization API router (Task T-16 / FR-09)."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.search import get_sync_db
from app.summarize.schemas import StructuredSummary, SummaryRequest
from app.summarize.summarizer import StructuredSummarizer

router = APIRouter(prefix="/v1", tags=["Summarization"])

_SUMMARIZER: StructuredSummarizer | None = None


def get_summarizer() -> StructuredSummarizer:
    """Dependency provider for StructuredSummarizer singleton."""
    global _SUMMARIZER
    if _SUMMARIZER is None:
        _SUMMARIZER = StructuredSummarizer()
    return _SUMMARIZER


@router.post("/summarize", response_model=StructuredSummary)
def summarize_case(
    payload: SummaryRequest,
    db: Session = Depends(get_sync_db),
    summarizer: StructuredSummarizer = Depends(get_summarizer),
) -> StructuredSummary:
    """Generate structured judgment summary with verified per-sentence paragraph numbers."""
    try:
        return summarizer.summarize_document(
            db=db,
            document_id=payload.document_id,
            max_sentences_per_section=payload.max_sentences_per_section,
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e


@router.get("/documents/{document_id}/summary", response_model=StructuredSummary)
def get_document_summary(
    document_id: int,
    db: Session = Depends(get_sync_db),
    summarizer: StructuredSummarizer = Depends(get_summarizer),
) -> StructuredSummary:
    """Retrieve structured summary for a judgment document."""
    try:
        return summarizer.summarize_document(
            db=db,
            document_id=document_id,
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
