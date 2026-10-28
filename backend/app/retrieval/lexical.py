"""Lexical search implementation using PostgreSQL Full-Text Search and in-memory BM25 (Task T-07 / FR-04)."""

import re
from typing import Any

from rank_bm25 import BM25Plus  # type: ignore[import-untyped]
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.db.models import Chunk, Court, Document

ATTRIBUTION_TEXT = (
    "Indian Supreme Court Judgments / Indian High Court Judgments, Dattam Labs, "
    "accessed from AWS Open Data Registry (CC-BY-4.0)."
)


class SearchResultItem:
    def __init__(
        self,
        chunk_id: int,
        document_id: int,
        title: str,
        court: str,
        decision_date: str | None,
        neutral_citation: str | None,
        para_no: int | None,
        segment_type: str | None,
        snippet: str,
        score: float,
        attribution: str = ATTRIBUTION_TEXT,
    ):
        self.chunk_id = chunk_id
        self.document_id = document_id
        self.title = title
        self.court = court
        self.decision_date = decision_date
        self.neutral_citation = neutral_citation
        self.para_no = para_no
        self.segment_type = segment_type
        self.snippet = snippet
        self.score = round(score, 6)
        self.attribution = attribution

    def to_dict(self) -> dict[str, Any]:
        return {
            "chunk_id": self.chunk_id,
            "document_id": self.document_id,
            "title": self.title,
            "court": self.court,
            "decision_date": self.decision_date,
            "neutral_citation": self.neutral_citation,
            "para_no": self.para_no,
            "segment_type": self.segment_type,
            "snippet": self.snippet,
            "score": self.score,
            "attribution": self.attribution,
        }


def make_snippet(text: str, query: str, max_chars: int = 250) -> str:
    """Create a highlight snippet around the first occurrence of query tokens."""
    tokens = [t.lower() for t in re.findall(r"\w+", query) if len(t) > 2]
    best_pos = -1
    lower_text = text.lower()

    for token in tokens:
        pos = lower_text.find(token)
        if pos != -1:
            best_pos = pos
            break

    if best_pos == -1 or len(text) <= max_chars:
        return text[:max_chars].strip() + ("..." if len(text) > max_chars else "")

    start = max(0, best_pos - 60)
    end = min(len(text), start + max_chars)
    snippet = text[start:end].strip()

    prefix = "..." if start > 0 else ""
    suffix = "..." if end < len(text) else ""
    return f"{prefix}{snippet}{suffix}"


def search_lexical_db(
    db: Session,
    query: str,
    court_codes: list[str] | None = None,
    year_from: int | None = None,
    year_to: int | None = None,
    user_id: int | None = None,
    limit: int = 20,
    offset: int = 0,
) -> list[SearchResultItem]:
    """Execute lexical search.

    Uses PostgreSQL FTS (to_tsvector/plainto_tsquery) when on Postgres;
    falls back to in-memory BM25 over matching candidate records on SQLite.
    Isolates private chunks unless owner matches user_id.
    """
    bind = db.get_bind()
    stmt = (
        select(Chunk, Document, Court)
        .join(Document, Chunk.document_id == Document.id)
        .outerjoin(Court, Document.court_id == Court.id)
    )

    if user_id is None:
        stmt = stmt.filter(Chunk.owner_user_id.is_(None))  # Public corpus only
    else:
        stmt = stmt.filter(or_(Chunk.owner_user_id.is_(None), Chunk.owner_user_id == user_id))

    if court_codes:
        stmt = stmt.filter(Court.code.in_(court_codes))
    if year_from:
        stmt = stmt.filter(func.extract("year", Document.decision_date) >= year_from)
    if year_to:
        stmt = stmt.filter(func.extract("year", Document.decision_date) <= year_to)

    results: list[SearchResultItem] = []

    if bind.dialect.name == "postgresql":
        # Native PostgreSQL Full-Text Search
        tsquery = func.plainto_tsquery("english", query)
        rank = func.ts_rank_cd(func.to_tsvector("english", Chunk.text), tsquery)
        stmt = stmt.filter(func.to_tsvector("english", Chunk.text).op("@@")(tsquery))
        stmt = stmt.order_by(rank.desc()).limit(limit).offset(offset)

        rows = db.execute(stmt).all()
        for chunk, doc, court in rows:
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
                    snippet=make_snippet(chunk.text, query),
                    score=1.0,
                )
            )
    else:
        # SQLite / In-memory BM25 Fallback for offline testing
        rows = db.execute(stmt).all()
        if not rows:
            return []

        corpus = [chunk.text for chunk, _, _ in rows]
        tokenized_corpus = [re.findall(r"\w+", doc_text.lower()) for doc_text in corpus]
        tokenized_query = re.findall(r"\w+", query.lower())

        if not tokenized_query or not tokenized_corpus:
            return []

        bm25 = BM25Plus(tokenized_corpus)
        scores = bm25.get_scores(tokenized_query)

        query_set = set(tokenized_query)
        scored_candidates = []
        for i, score in enumerate(scores):
            doc_tokens = set(tokenized_corpus[i])
            overlap = len(query_set.intersection(doc_tokens))
            if overlap > 0:
                chunk, doc, court = rows[i]
                scored_candidates.append((float(score), chunk, doc, court))

        scored_candidates.sort(key=lambda x: x[0], reverse=True)
        paginated = scored_candidates[offset : offset + limit]

        for score, chunk, doc, court in paginated:
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
                    snippet=make_snippet(chunk.text, query),
                    score=float(score),
                )
            )

    return results
