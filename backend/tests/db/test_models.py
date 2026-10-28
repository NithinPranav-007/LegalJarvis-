"""Unit tests for database models, constraints, and relationships."""

from datetime import date

import pytest
from sqlalchemy import create_engine
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db.models import (
    Answer,
    Base,
    Chunk,
    Conversation,
    Court,
    DatasetSnapshot,
    Document,
    IngestionRun,
    Message,
    Statute,
    StatuteConcordance,
    StatuteSection,
    StatuteVersion,
    User,
)


@pytest.fixture
def db_session() -> Session:
    """Provides an isolated in-memory SQLite session for model testing."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        yield session


def test_court_model_and_constraints(db_session: Session) -> None:
    court = Court(code="sc", name="Supreme Court of India", level="supreme")
    db_session.add(court)
    db_session.commit()

    retrieved = db_session.query(Court).filter_by(code="sc").first()
    assert retrieved is not None
    assert retrieved.name == "Supreme Court of India"
    assert retrieved.level == "supreme"


def test_chunk_offset_constraint(db_session: Session) -> None:
    court = Court(code="sc", name="Supreme Court of India", level="supreme")
    snapshot = DatasetSnapshot(
        source_key="sc_judgments",
        source_url="https://registry.opendata.aws/indian-supreme-court-judgments/",
        license="CC-BY-4.0",
        attribution="Dattam Labs",
        manifest_path="data/manifests/sc_2023.sha256",
    )
    db_session.add_all([court, snapshot])
    db_session.commit()

    run = IngestionRun(
        snapshot_id=snapshot.id,
        params={"year": 2023},
        status="success",
    )
    db_session.add(run)
    db_session.commit()

    doc = Document(
        run_id=run.id,
        court_id=court.id,
        external_id="2023_16_872_887",
        title="Test Judgment",
        source_file_path="data/raw/sc/year=2023/2023_16_872_887_EN.pdf",
        source_sha256="a" * 64,
        extraction_status="ok",
    )
    db_session.add(doc)
    db_session.commit()

    # Valid chunk
    valid_chunk = Chunk(
        document_id=doc.id,
        para_no=1,
        segment_type="facts",
        start_char=0,
        end_char=100,
        text="A suit for specific performance was filed seeking enforcement of MoU.",
        embedding=[0.1] * 1024,
    )
    db_session.add(valid_chunk)
    db_session.commit()
    assert valid_chunk.id is not None

    # Offsets round-trip check
    assert valid_chunk.end_char > valid_chunk.start_char

    # Invalid chunk where end_char <= start_char
    invalid_chunk = Chunk(
        document_id=doc.id,
        para_no=2,
        segment_type="facts",
        start_char=50,
        end_char=40,  # Invalid!
        text="Invalid offsets",
    )
    db_session.add(invalid_chunk)
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


def test_statute_and_concordance_model(db_session: Session) -> None:
    statute_bns = Statute(
        short_name="BNS",
        act_year=2023,
        act_no=45,
        source_url="https://www.indiacode.nic.in/handle/123456789/20062",
    )
    statute_ipc = Statute(
        short_name="IPC",
        act_year=1860,
        act_no=45,
        source_url="https://www.indiacode.nic.in/",
    )
    db_session.add_all([statute_bns, statute_ipc])
    db_session.commit()

    v_ipc = StatuteVersion(
        statute_id=statute_ipc.id,
        effective_from=date(1862, 1, 1),
        effective_to=date(2024, 6, 30),
        status="repealed",
        source_sha256="b" * 64,
    )
    v_bns = StatuteVersion(
        statute_id=statute_bns.id,
        effective_from=date(2024, 7, 1),
        status="in_force",
        source_sha256="c" * 64,
    )
    db_session.add_all([v_ipc, v_bns])
    db_session.commit()

    sec_302 = StatuteSection(
        version_id=v_ipc.id,
        section_no="302",
        heading="Punishment for murder",
        text="Whoever commits murder shall be punished with death...",
    )
    sec_103 = StatuteSection(
        version_id=v_bns.id,
        section_no="103",
        heading="Punishment for murder",
        text="Whoever commits murder shall be punished with death...",
    )
    db_session.add_all([sec_302, sec_103])
    db_session.commit()

    # Concordance mapping with official source and reviewer
    concordance = StatuteConcordance(
        old_section_id=sec_302.id,
        new_section_id=sec_103.id,
        source_url="https://egazette.gov.in/WriteReadData/2023/250883.pdf",
        reviewed_by="LEAD_ADVOCATE_REVIEWER",
        reviewed_at=date(2024, 7, 2),
        note="Verified correspondence: IPC Section 302 corresponds to BNS Section 103(1).",
    )
    db_session.add(concordance)
    db_session.commit()

    res = db_session.query(StatuteConcordance).filter_by(old_section_id=sec_302.id).first()
    assert res is not None
    assert res.reviewed_by == "LEAD_ADVOCATE_REVIEWER"
    assert res.new_section_id == sec_103.id


def test_user_and_answer_citations_model(db_session: Session) -> None:
    user = User(
        email="researcher@example.com",
        password_hash="argon2_or_bcrypt_hash_placeholder",
        role="researcher",
    )
    db_session.add(user)
    db_session.commit()

    conv = Conversation(user_id=user.id)
    db_session.add(conv)
    db_session.commit()

    msg = Message(
        conversation_id=conv.id,
        role="user",
        content="What is the holding in the Eldeco case?",
    )
    db_session.add(msg)
    db_session.commit()

    ans = Answer(
        message_id=msg.id,
        model_id="gpt-4o-mini",
        prompt_version="qa_v1",
        retrieval_ids=[101, 102],
        abstained=False,
        verification={"claims": [{"claim": "Plaint was rejected", "status": "supported"}]},
        latency_ms=1200,
    )
    db_session.add(ans)
    db_session.commit()
    assert ans.id is not None
