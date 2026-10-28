"""Unit tests for structured audit logging (FR-18)."""

from app.core.logging import log_audit_event


def test_log_audit_event_structure() -> None:
    event = log_audit_event(
        event_type="qa_query",
        user_id=42,
        query="What are the essential elements of cheating under Section 415 IPC?",
        retrieval_chunk_ids=[101, 102],
        model_identifier="test-llm",
        latency_ms=124.5,
        verification_outcome="verified",
    )

    assert "event_id" in event
    assert event["event_type"] == "qa_query"
    assert event["user_id"] == 42
    assert event["query_length"] > 0
    assert event["retrieval_chunk_ids"] == [101, 102]
    assert event["model_identifier"] == "test-llm"
    assert event["latency_ms"] == 124.5
    assert event["verification_outcome"] == "verified"
    assert "timestamp_utc" in event
