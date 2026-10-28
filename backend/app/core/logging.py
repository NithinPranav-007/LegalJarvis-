"""Structured audit logging and observability (FR-18 / NFR-LOG).

Records query metadata, retrieval IDs, model identifiers, latency, and verification
outcomes into structured JSON logs without persisting private document text.
"""

import json
import logging
import sys
import time
import uuid
from typing import Any

logger = logging.getLogger("legaljarvis.audit")
logger.setLevel(logging.INFO)

# JSON stream handler
if not logger.handlers:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter("%(message)s"))
    logger.addHandler(handler)


def log_audit_event(
    event_type: str,
    user_id: int | None = None,
    query: str | None = None,
    retrieval_chunk_ids: list[int] | None = None,
    model_identifier: str | None = None,
    latency_ms: float | None = None,
    verification_outcome: str | None = None,
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Emit a structured JSON audit log entry."""
    audit_record: dict[str, Any] = {
        "event_id": str(uuid.uuid4()),
        "event_type": event_type,
        "timestamp_utc": time.time(),
        "user_id": user_id,
        "query_length": len(query) if query else 0,
        "retrieval_chunk_ids": retrieval_chunk_ids or [],
        "model_identifier": model_identifier,
        "latency_ms": round(latency_ms, 2) if latency_ms is not None else None,
        "verification_outcome": verification_outcome,
    }
    if extra:
        audit_record.update(extra)

    logger.info(json.dumps(audit_record))
    return audit_record
