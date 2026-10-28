"""Retention and scheduled purge job for expired user documents (Task T-17 / FR-08)."""

import datetime
import logging
from collections.abc import Sequence
from pathlib import Path

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.db.models import Chunk, Document, UserDocument

logger = logging.getLogger(__name__)


def purge_expired_documents(db: Session, as_of: datetime.datetime | None = None) -> int:
    """Find and purge all private user documents that have passed their retention period (expires_at).

    Per PRD FR-08 / D7:
    - User uploads expire after a configurable retention period (default 30 days).
    - Purge removes the stored file on disk, document record, chunk records, and embeddings.
    - Logs contain NO document text; only purged counts and identifiers.
    """
    now = as_of or datetime.datetime.now(datetime.UTC)

    # 1. Select expired user_documents
    stmt = select(UserDocument).where(UserDocument.expires_at <= now)
    expired_records: Sequence[UserDocument] = db.execute(stmt).scalars().all()

    if not expired_records:
        logger.info("Retention purge ran: 0 expired user documents found.")
        return 0

    purged_count = 0
    for udoc in expired_records:
        doc_id = udoc.document_id
        doc: Document | None = None
        if doc_id:
            doc = db.get(Document, doc_id)
        else:
            doc_stmt = select(Document).where(
                Document.owner_user_id == udoc.user_id,
                Document.source_sha256 == udoc.sha256,
            )
            doc = db.execute(doc_stmt).scalar_one_or_none()

        if doc:
            # Delete physical files on disk
            if doc.source_file_path and Path(doc.source_file_path).is_file():
                try:
                    Path(doc.source_file_path).unlink(missing_ok=True)
                except Exception as e:
                    logger.warning("Failed to remove source file %s: %s", doc.source_file_path, e)

            if doc.text_path and Path(doc.text_path).is_file():
                try:
                    Path(doc.text_path).unlink(missing_ok=True)
                except Exception as e:
                    logger.warning("Failed to remove text file %s: %s", doc.text_path, e)

            # Explicitly delete chunks if needed or rely on cascade
            db.execute(delete(Chunk).where(Chunk.document_id == doc.id))
            db.delete(doc)

        db.delete(udoc)
        purged_count += 1
        logger.info(
            "Purged expired user document: user_id=%d, udoc_id=%d, sha256=%s",
            udoc.user_id,
            udoc.id,
            udoc.sha256,
        )

    db.commit()
    logger.info("Retention purge completed: %d documents purged successfully.", purged_count)
    return purged_count


if __name__ == "__main__":
    from app.db.session import sync_session_maker

    logging.basicConfig(level=logging.INFO)
    with sync_session_maker() as session:
        count = purge_expired_documents(session)
        print(f"Purged {count} expired user documents.")
