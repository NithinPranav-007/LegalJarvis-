"""Documents and Case Viewer API router (Task T-14 / FR-05)."""

from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.api.search import get_sync_db
from app.db.models import Chunk, Document
from app.retrieval.lexical import ATTRIBUTION_TEXT
from app.schemas.document import ChunkOut, DocumentDetail

router = APIRouter(prefix="/v1/documents", tags=["Documents"])


@router.get("/{document_id}", response_model=DocumentDetail)
def get_document(
    document_id: int,
    db: Session = Depends(get_sync_db),
) -> DocumentDetail:
    """Retrieve full judgment text, metadata, and ordered chunks for the Case Viewer."""
    stmt = select(Document).options(selectinload(Document.court)).where(Document.id == document_id)
    doc = db.execute(stmt).scalar_one_or_none()
    if not doc:
        raise HTTPException(status_code=404, detail=f"Document with ID {document_id} not found")

    chunk_stmt = (
        select(Chunk)
        .where(Chunk.document_id == document_id)
        .order_by(Chunk.para_no.asc().nulls_last(), Chunk.start_char.asc())
    )
    chunks = db.execute(chunk_stmt).scalars().all()

    chunks_out = [
        ChunkOut(
            id=c.id,
            para_no=c.para_no,
            segment_type=c.segment_type,
            text=c.text,
            start_char=c.start_char,
            end_char=c.end_char,
        )
        for c in chunks
    ]

    # Resolve document text: from text_path file if it exists, or join chunks
    full_text = ""
    if doc.text_path and Path(doc.text_path).is_file():
        try:
            full_text = Path(doc.text_path).read_text(encoding="utf-8")
        except Exception:
            full_text = "\n\n".join(c.text for c in chunks)
    elif chunks:
        full_text = "\n\n".join(c.text for c in chunks)

    raw_meta = doc.raw_metadata or {}
    bench = raw_meta.get("bench")
    dataset_name = raw_meta.get("dataset_name", "sc_2023")

    return DocumentDetail(
        id=doc.id,
        title=doc.title or f"Judgment #{doc.id}",
        court_code=doc.court.code if doc.court else "sc",
        court_name=doc.court.name if doc.court else "Supreme Court of India",
        decision_date=doc.decision_date.isoformat() if doc.decision_date else None,
        neutral_citation=doc.neutral_citation,
        bench=bench,
        dataset_name=dataset_name,
        extraction_quality=doc.extraction_quality,
        text=full_text,
        chunks=chunks_out,
        attribution=ATTRIBUTION_TEXT,
    )


@router.get("", response_model=list[dict])
def list_documents(
    limit: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_sync_db),
) -> list[dict]:
    """List recent judgments for browsing in the Case Viewer."""
    stmt = (
        select(Document)
        .options(selectinload(Document.court))
        .order_by(Document.id.desc())
        .limit(limit)
    )
    docs = db.execute(stmt).scalars().all()
    return [
        {
            "id": d.id,
            "title": d.title or f"Judgment #{d.id}",
            "court_code": d.court.code if d.court else "sc",
            "court_name": d.court.name if d.court else "Supreme Court of India",
            "decision_date": d.decision_date.isoformat() if d.decision_date else None,
            "neutral_citation": d.neutral_citation,
        }
        for d in docs
    ]
