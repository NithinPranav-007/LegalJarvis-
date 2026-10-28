"""Search API router (Task T-07 / FR-04)."""

from collections.abc import Generator

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import sync_session_maker
from app.retrieval.lexical import ATTRIBUTION_TEXT, search_lexical_db
from app.schemas.search import SearchItem, SearchRequest, SearchResponse

router = APIRouter(prefix="/v1", tags=["Search"])


def get_sync_db() -> Generator[Session, None, None]:
    """Dependency for synchronous database session in search queries."""
    with sync_session_maker() as session:
        yield session


@router.post("/search", response_model=SearchResponse)
def search_cases(
    payload: SearchRequest,
    db: Session = Depends(get_sync_db),
) -> SearchResponse:
    """Hybrid and lexical case law search."""
    results = search_lexical_db(
        db=db,
        query=payload.query,
        court_codes=payload.court_codes,
        year_from=payload.year_from,
        year_to=payload.year_to,
        limit=payload.limit,
        offset=payload.offset,
    )

    items = [SearchItem(**r.to_dict()) for r in results]
    return SearchResponse(
        query=payload.query,
        total=len(items),
        results=items,
        attribution=ATTRIBUTION_TEXT,
    )
