"""Search API router (Task T-07 / FR-04)."""

from typing import Any


from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.auth import get_optional_current_user
from app.db.models import User
from app.db.session import get_sync_db
from app.retrieval.dense import search_dense
from app.retrieval.hybrid import search_hybrid
from app.retrieval.lexical import ATTRIBUTION_TEXT, search_lexical_db
from app.schemas.search import SearchItem, SearchRequest, SearchResponse

router = APIRouter(prefix="/v1", tags=["Search"])


@router.post("/search", response_model=SearchResponse)
def search_cases(
    payload: SearchRequest,
    db: Session = Depends(get_sync_db),
    current_user: User | None = Depends(get_optional_current_user),
) -> SearchResponse:
    """Hybrid, lexical, or dense case law search."""
    user_id = current_user.id if current_user else None
    if payload.mode == "lexical":
        results = search_lexical_db(
            db=db,
            query=payload.query,
            court_codes=payload.court_codes,
            year_from=payload.year_from,
            year_to=payload.year_to,
            user_id=user_id,
            limit=payload.limit,
            offset=payload.offset,
        )
    elif payload.mode == "dense":
        results = search_dense(
            db=db,
            query=payload.query,
            court_codes=payload.court_codes,
            year_from=payload.year_from,
            year_to=payload.year_to,
            user_id=user_id,
            limit=payload.limit,
            offset=payload.offset,
        )
    else:
        results = search_hybrid(
            db=db,
            query=payload.query,
            court_codes=payload.court_codes,
            year_from=payload.year_from,
            year_to=payload.year_to,
            user_id=user_id,
            rerank=payload.rerank,
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


@router.get("/search/facets")
def get_facets(db: Session = Depends(get_sync_db)) -> dict[str, Any]:
    """Retrieve metadata facets (courts, document counts) per FR-12."""
    from app.retrieval.filters import get_available_courts
    courts = get_available_courts(db)
    return {"courts": courts}
