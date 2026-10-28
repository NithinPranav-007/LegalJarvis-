"""Tests for Reviewer Tooling, Gold Standard Datasets, and Disjointness Protocol (Task T-18 / FR-16)."""

import datetime
from pathlib import Path

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.core.security import create_access_token, hash_password
from app.db.models import (
    Answer,
    Base,
    Conversation,
    Court,
    DatasetSnapshot,
    Document,
    IngestionRun,
    Message,
    User,
)
from app.db.session import get_sync_db
from app.eval.gold_import import (
    GoldQAItem,
    export_gold_qa_file,
    load_gold_qa_file,
    validate_gold_qa_item,
    verify_gold_tuning_disjointness,
)
from app.main import app


@pytest.fixture
def eval_db() -> Session:
    """In-memory test database with users, answer, and documents."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    session = Session(engine)

    court = Court(code="sc", name="Supreme Court of India", level="supreme")
    snap = DatasetSnapshot(
        source_key="sc",
        source_url="https://sc.gov.in",
        license="CC-BY-4.0",
        attribution="Open Data",
        manifest_path="m.json",
    )
    session.add_all([court, snap])
    session.flush()

    run = IngestionRun(snapshot_id=snap.id, params={}, status="success")
    session.add(run)
    session.flush()

    # Create users
    reviewer_user = User(
        id=201,
        email="senior_advocate@bar.in",
        password_hash=hash_password("advocatePass123"),
        role="reviewer",
    )
    researcher_user = User(
        id=202,
        email="researcher@legaljarvis.in",
        password_hash=hash_password("resPass123"),
        role="researcher",
    )
    session.add_all([reviewer_user, researcher_user])

    # Create document
    doc = Document(
        id=10,
        run_id=run.id,
        court_id=court.id,
        external_id="sc_2023_101",
        title="State of Haryana v. Bhajan Lal Bench Review",
        decision_date=datetime.date(2023, 5, 12),
        source_file_path="sc_bhajan.pdf",
        source_sha256="b" * 64,
        extraction_status="ok",
    )
    session.add(doc)
    session.flush()

    # Create Conversation, Message, and Answer records to receive reviewer feedback
    conv = Conversation(id=1, user_id=202)
    session.add(conv)
    session.flush()

    msg = Message(
        id=1,
        conversation_id=conv.id,
        role="assistant",
        content="The Supreme Court reiterated the seven Bhajan Lal categories [C1].",
    )
    session.add(msg)
    session.flush()

    ans = Answer(
        id=50,
        message_id=msg.id,
        model_id="gpt-4o-mini",
        prompt_version="qa_v1",
        retrieval_ids=[10],
        abstained=False,
        verification={},
        latency_ms=120,
    )
    session.add(ans)
    session.commit()

    yield session
    session.close()


def test_gold_item_validation_rules() -> None:
    """Verify strict validation of gold items: human reviewer required, post-2023, valid categories."""
    # 1. Valid non-adversarial gold item
    valid_item = {
        "id": "LJ-GOLD-QA-001",
        "question": "Does Section 438 CrPC require exceptional circumstances for anticipatory bail?",
        "reference_answer": "No. The Constitution Bench held that power is not hedged in by rigid conditions.",
        "target_document_ids": [10],
        "gold_paragraph_nos": [15, 16],
        "subject_area": "criminal",
        "decision_year": 2023,
        "reviewer_initials": "ADV-VK",
    }
    is_valid, err = validate_gold_qa_item(valid_item)
    assert is_valid is True
    assert err is None

    # 2. Rejects automated/AI reviewer initials (PRD Rule 1 & Rule 3)
    ai_item = valid_item.copy()
    ai_item["reviewer_initials"] = "GPT-4"
    is_valid, err = validate_gold_qa_item(ai_item)
    assert is_valid is False
    assert "Automated reviewers are strictly prohibited" in (err or "")

    # 3. Rejects missing reviewer initials
    missing_rev = valid_item.copy()
    missing_rev["reviewer_initials"] = ""
    is_valid, err = validate_gold_qa_item(missing_rev)
    assert is_valid is False
    assert "missing 'reviewer_initials'" in (err or "")

    # 4. Rejects pre-2023 decision year (to prevent pretraining contamination)
    old_year = valid_item.copy()
    old_year["decision_year"] = 2020
    is_valid, err = validate_gold_qa_item(old_year)
    assert is_valid is False
    assert "Decision year 2020 < 2023" in (err or "")

    # 5. Valid adversarial question
    adv_item = {
        "id": "LJ-ADV-001",
        "question": "Under what section of the Indian Constitution is anticipatory bail prohibited?",
        "reference_answer": "The Constitution does not prohibit anticipatory bail; the premise is false.",
        "subject_area": "constitutional",
        "decision_year": 2024,
        "reviewer_initials": "ADV-SP",
        "is_adversarial": True,
        "adversarial_category": "false_premise",
    }
    is_valid, err = validate_gold_qa_item(adv_item)
    assert is_valid is True


def test_disjointness_enforcement() -> None:
    """PRD Invariant: No LJ-Gold item, and no document linked to one, may appear in any tuning set."""
    gold_items = [
        {"id": "LJ-GOLD-01", "target_document_ids": [101, 102]},
        {"id": "LJ-GOLD-02", "target_document_ids": [103]},
    ]

    # Test 1: Clean disjoint tuning set
    tuning_set_clean = {201, 202, 203}
    disjoint, overlap = verify_gold_tuning_disjointness(gold_items, tuning_set_clean)
    assert disjoint is True
    assert len(overlap) == 0

    # Test 2: Contaminated tuning set with leaked document
    tuning_set_leaked = {201, 102, 203}
    disjoint, overlap = verify_gold_tuning_disjointness(gold_items, tuning_set_leaked)
    assert disjoint is False
    assert overlap == {102}


@pytest.mark.asyncio
async def test_reviewer_feedback_api_and_export(eval_db: Session) -> None:
    """Test POST /v1/feedback/reviewer and GET /v1/feedback/export endpoints."""
    token_reviewer = create_access_token(data={"sub": "201", "role": "reviewer"})
    token_researcher = create_access_token(data={"sub": "202", "role": "researcher"})

    app.dependency_overrides[get_sync_db] = lambda: eval_db

    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            headers_reviewer = {"Authorization": f"Bearer {token_reviewer}"}
            headers_researcher = {"Authorization": f"Bearer {token_researcher}"}

            # 1. Non-reviewer attempts to submit reviewer feedback -> 403 Forbidden
            unauth_resp = await client.post(
                "/v1/feedback/reviewer",
                json={
                    "answer_id": 50,
                    "rating": 5,
                    "overall_label": "supported",
                    "claims": [],
                },
                headers=headers_researcher,
            )
            assert unauth_resp.status_code == 403

            # 2. Reviewer submits detailed feedback with claims
            payload = {
                "answer_id": 50,
                "rating": 5,
                "overall_label": "supported",
                "claims": [
                    {
                        "claim_index": 0,
                        "claim_text": "The Supreme Court reiterated the seven Bhajan Lal categories.",
                        "is_supported": True,
                        "cited_para_no": 15,
                        "issue_type": "supported",
                        "notes": "Verified against transcript",
                    }
                ],
                "legal_accuracy_notes": "Grounding is 100% faithful to paragraph 15.",
                "reviewer_role": "advocate",
            }
            resp = await client.post("/v1/feedback/reviewer", json=payload, headers=headers_reviewer)
            assert resp.status_code == 201
            assert resp.json()["status"] == "success"

            # 3. Export reviewer feedback
            export_resp = await client.get("/v1/feedback/export?reviewer_only=true", headers=headers_reviewer)
            assert export_resp.status_code == 200
            data = export_resp.json()
            assert len(data) >= 1
            item = data[0]
            assert item["answer_id"] == 50
            assert item["rating"] == 5
            assert item["label"] == "supported"
            assert item["reviewer_role"] == "advocate"
            assert len(item["claims_json"]) == 1
    finally:
        app.dependency_overrides.clear()


def test_gold_dataset_import_export_lifecycle(tmp_path: Path) -> None:
    """Test exporting and re-importing GoldQAItems with 100% schema fidelity."""
    items = [
        GoldQAItem(
            id="LJ-GOLD-QA-100",
            question="What is the legal test for bail under NDPS Act Section 37?",
            reference_answer="Twin conditions require reasonable grounds for believing the accused is not guilty.",
            target_document_ids=[10],
            gold_paragraph_nos=[22, 23],
            subject_area="criminal",
            decision_year=2023,
            reviewer_initials="ADV-SK",
        )
    ]

    out_file = tmp_path / "gold_qa_export.jsonl"
    count = export_gold_qa_file(items, out_file)
    assert count == 1
    assert out_file.is_file()

    loaded = load_gold_qa_file(out_file)
    assert len(loaded) == 1
    assert loaded[0].id == "LJ-GOLD-QA-100"
    assert loaded[0].gold_paragraph_nos == [22, 23]
    assert loaded[0].reviewer_initials == "ADV-SK"
    assert loaded[0].disallow_tuning is True
