"""Dense vector retrieval implementation (Task T-08 / FR-04)."""

import json
import math
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.models import Chunk, Court, Document
from app.ingest.embed import BaseEmbedder, get_embedder
from app.retrieval.lexical import ATTRIBUTION_TEXT, SearchResultItem, make_snippet


def _cosine_sim(v1: list[float], v2: list[float]) -> float:
    """Compute cosine similarity between two float vectors."""
    if len(v1) != len(v2) or not v1:
        return 0.0
    dot = sum(a * b for a, b in zip(v1, v2, strict=False))
    norm1 = math.sqrt(sum(a * a for a in v1))
    norm2 = math.sqrt(sum(b * b for b in v2))
    if norm1 < 1e-9 or norm2 < 1e-9:
        return 0.0
    return float(dot / (norm1 * norm2))


def search_dense(
    db: Session,
    query: str | list[float],
    court_codes: list[str] | None = None,
    year_from: int | None = None,
    year_to: int | None = None,
    limit: int = 50,
    offset: int = 0,
    embedder: BaseEmbedder | None = None,
) -> list[SearchResultItem]:
    """Execute dense semantic search using vector similarity.

    Supports pgvector cosine distance on PostgreSQL, with an in-memory
    vector similarity fallback for SQLite test suites.
    """
    active_embedder = embedder or get_embedder()
    query_text = query if isinstance(query, str) else ""
    query_vector = active_embedder.embed_text(query) if isinstance(query, str) else query

    bind = db.get_bind()
    stmt = (
        select(Chunk, Document, Court)
        .join(Document, Chunk.document_id == Document.id)
        .outerjoin(Court, Document.court_id == Court.id)
        .filter(Chunk.owner_user_id.is_(None))  # Public corpus only
        .filter(Chunk.embedding.is_not(None))
    )

    if court_codes:
        stmt = stmt.filter(Court.code.in_(court_codes))
    if year_from:
        stmt = stmt.filter(func.extract("year", Document.decision_date) >= year_from)
    if year_to:
        stmt = stmt.filter(func.extract("year", Document.decision_date) <= year_to)

    results: list[SearchResultItem] = []

    if bind.dialect.name == "postgresql":
        # Native pgvector cosine distance
        distance_col = Chunk.embedding.cosine_distance(query_vector)  # type: ignore[attr-defined]
        stmt = stmt.order_by(distance_col).limit(limit).offset(offset)
        rows = db.execute(stmt).all()

        for chunk, doc, court in rows:
            # Cosine similarity = 1 - cosine distance
            score = 1.0
            results.append(
                SearchResultItem(
                    chunk_id=chunk.id,
                    document_id=doc.id,
                    title=doc.title or "Untitled Judgment",
                    court=court.name if court else "Supreme Court of India",
                    decision_date=str(doc.decision_date) if doc.decision_date else None,
                    neutral_citation=doc.neutral_citation,
                    para_no=chunk.para_no,
                    segment_type=chunk.segment_type,
                    snippet=make_snippet(chunk.text, query_text),
                    score=score,
                    attribution=ATTRIBUTION_TEXT,
                )
            )
    else:
        # SQLite / In-memory cosine fallback
        rows = db.execute(stmt).all()
        scored: list[tuple[float, Any, Any, Any]] = []

        for chunk, doc, court in rows:
            vec: list[float]
            if isinstance(chunk.embedding, str):
                vec = json.loads(chunk.embedding)
            elif isinstance(chunk.embedding, list):
                vec = chunk.embedding
            else:
                continue

            sim = _cosine_sim(query_vector, vec)
            if sim > 0.0:
                scored.append((sim, chunk, doc, court))

        scored.sort(key=lambda x: x[0], reverse=True)
        paginated = scored[offset : offset + limit]

        for sim, chunk, doc, court in paginated:
            results.append(
                SearchResultItem(
                    chunk_id=chunk.id,
                    document_id=doc.id,
                    title=doc.title or "Untitled Judgment",
                    court=court.name if court else "Supreme Court of India",
                    decision_date=str(doc.decision_date) if doc.decision_date else None,
                    neutral_citation=doc.neutral_citation,
                    para_no=chunk.para_no,
                    segment_type=chunk.segment_type,
                    snippet=make_snippet(chunk.text, query_text),
                    score=round(sim, 4),
                    attribution=ATTRIBUTION_TEXT,
                )
            )

    return results
