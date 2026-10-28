"""Metadata filtering utilities for retrieval (Task T-08 / FR-12)."""

from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.models import Court, Document


def get_available_courts(db: Session) -> list[dict[str, Any]]:
    """Retrieve list of courts with code, display name, and document counts."""
    stmt = (
        select(Court.code, Court.name, Court.level, func.count(Document.id).label("doc_count"))
        .outerjoin(Document, Court.id == Document.court_id)
        .group_by(Court.code, Court.name, Court.level)
        .order_by(Court.level.desc(), Court.name.asc())
    )
    rows = db.execute(stmt).all()
    return [
        {
            "code": r.code,
            "name": r.name,
            "level": r.level,
            "doc_count": r.doc_count,
        }
        for r in rows
    ]
