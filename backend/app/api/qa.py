"""Question Answering API router (Task T-11 / FR-05)."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.search import get_sync_db
from app.qa.orchestrator import QAOrchestrator
from app.schemas.qa import QARequest, QAResponse

router = APIRouter(prefix="/v1", tags=["Question Answering"])

_ORCHESTRATOR: QAOrchestrator | None = None


def get_orchestrator() -> QAOrchestrator:
    """Dependency provider for QA orchestrator singleton."""
    global _ORCHESTRATOR
    if _ORCHESTRATOR is None:
        _ORCHESTRATOR = QAOrchestrator()
    return _ORCHESTRATOR


@router.post("/qa", response_model=QAResponse)
def answer_legal_question(
    payload: QARequest,
    db: Session = Depends(get_sync_db),
    orchestrator: QAOrchestrator = Depends(get_orchestrator),
) -> QAResponse:
    """Citation-verified Question Answering over Indian legal corpus."""
    return orchestrator.ask(
        db=db,
        question=payload.question,
        court_codes=payload.court_codes,
        year_from=payload.year_from,
        year_to=payload.year_to,
    )
