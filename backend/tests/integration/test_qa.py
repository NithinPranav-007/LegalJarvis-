"""Integration and API tests for Question Answering orchestrator (Task T-11 / FR-05)."""

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.api.search import get_sync_db
from app.db.models import Base, Chunk, Court, DatasetSnapshot, Document, IngestionRun
from app.ingest.embed import DeterministicHashEmbedder
from app.llm.gateway import LLMGateway
from app.llm.providers.fake import FakeProvider
from app.main import app
from app.qa.orchestrator import QAOrchestrator


@pytest.fixture
def qa_db() -> Session:
    """In-memory database pre-populated with Indian case law and embeddings."""
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    session = Session(engine)

    court = Court(code="sc", name="Supreme Court of India", level="supreme")
    snapshot = DatasetSnapshot(
        source_key="sc_judgments",
        source_url="https://registry.opendata.aws/indian-supreme-court-judgments/",
        license="CC-BY-4.0",
        attribution="Dattam Labs",
        manifest_path="data/manifests/sc_2023.sha256",
    )
    session.add_all([court, snapshot])
    session.commit()

    run = IngestionRun(snapshot_id=snapshot.id, params={"year": 2023}, status="success")
    session.add(run)
    session.commit()

    doc1 = Document(
        run_id=run.id,
        court_id=court.id,
        external_id="2023_16_872_887",
        title="Eldeco Housing and Industries Ltd v. Ashok Vidyarthi",
        neutral_citation="2023 INSC 1043",
        source_file_path="data/raw/sc/year=2023/2023_16_872_887_EN.pdf",
        source_sha256="1" * 64,
        extraction_status="ok",
    )
    doc2 = Document(
        run_id=run.id,
        court_id=court.id,
        external_id="2023_7_322_346",
        title="Central GST Delhi v. Delhi International Airport Ltd",
        neutral_citation="2023 INSC 540",
        source_file_path="data/raw/sc/year=2023/2023_7_322_346_EN.pdf",
        source_sha256="2" * 64,
        extraction_status="ok",
    )
    session.add_all([doc1, doc2])
    session.commit()

    embedder = DeterministicHashEmbedder()
    t1 = "A suit for specific performance requires the plaintiff to establish readiness and willingness under Section 16(c) of Specific Relief Act."
    t2 = "The levy of service tax on user development fee collected under the Airports Authority Act is invalid."

    chunk1 = Chunk(
        document_id=doc1.id,
        para_no=14,
        segment_type="reasoning",
        start_char=0,
        end_char=len(t1),
        text=t1,
        embedding=embedder.embed_text(t1),
    )
    chunk2 = Chunk(
        document_id=doc2.id,
        para_no=22,
        segment_type="holding",
        start_char=0,
        end_char=len(t2),
        text=t2,
        embedding=embedder.embed_text(t2),
    )
    session.add_all([chunk1, chunk2])
    session.commit()

    yield session
    session.close()


def test_qa_grounded_answer_with_citations(qa_db: Session) -> None:
    fake_llm = FakeProvider(
        canned_response="The plaintiff must establish continuous readiness and willingness under Section 16(c) [C1]."
    )
    gw = LLMGateway(provider_name="fake")
    gw._provider_instance = fake_llm

    orchestrator = QAOrchestrator(gateway=gw)
    resp = orchestrator.ask(
        db=qa_db,
        question="What is the requirement for specific performance under Section 16(c)?",
    )

    assert resp.abstained is False
    assert "[C1]" in resp.answer
    assert len(resp.citations) >= 1
    cit = resp.citations[0]
    assert cit.marker == "[C1]"
    assert "Eldeco Housing" in cit.title
    assert cit.para_no == 14
    assert cit.chunk_id == 1
    assert "Dattam Labs" in cit.attribution
    assert "provides automated legal research" in resp.disclaimer


def test_qa_low_evidence_abstention(qa_db: Session) -> None:
    fake_llm = FakeProvider(
        canned_response="[INSUFFICIENT_EVIDENCE] The provided legal materials do not address French admiralty jurisdiction."
    )
    gw = LLMGateway(provider_name="fake")
    gw._provider_instance = fake_llm

    orchestrator = QAOrchestrator(gateway=gw)
    resp = orchestrator.ask(
        db=qa_db,
        question="What is the limitation period for French maritime cabotage?",
    )

    assert resp.abstained is True
    assert resp.generation_status == "abstained"
    assert "insufficient evidence" in resp.abstention_reason.lower()


def test_qa_criminal_law_transition_notice(qa_db: Session) -> None:
    fake_llm = FakeProvider(
        canned_response="Inherent power to quash is exercised under Section 482 CrPC [C1]."
    )
    gw = LLMGateway(provider_name="fake")
    gw._provider_instance = fake_llm

    orchestrator = QAOrchestrator(gateway=gw)
    resp = orchestrator.ask(
        db=qa_db,
        question="Can criminal proceedings under IPC and CrPC be quashed under Section 482?",
    )

    assert resp.criminal_transition_notice is not None
    assert "1 July 2024" in resp.criminal_transition_notice
    assert "Bharatiya Nyaya Sanhita" in resp.criminal_transition_notice


def test_qa_generator_down_graceful_fallback(qa_db: Session) -> None:
    # Gateway configured with no credentials
    gw = LLMGateway(provider_name="openai", api_key="")
    orchestrator = QAOrchestrator(gateway=gw)

    resp = orchestrator.ask(
        db=qa_db,
        question="Is service tax payable on user development fee at airports?",
    )

    assert resp.generation_status == "generation_unavailable"
    assert "unavailable" in resp.answer.lower()
    # Source passages should still be returned as citations
    assert len(resp.citations) >= 1
    assert any("Central GST" in c.title for c in resp.citations)


@pytest.mark.asyncio
async def test_qa_api_endpoint(qa_db: Session) -> None:
    def override_db():
        yield qa_db

    app.dependency_overrides[get_sync_db] = override_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post(
            "/v1/qa",
            json={
                "question": "What are the rules for specific performance readiness and willingness?"
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "question" in data
        assert "answer" in data
        assert "citations" in data
        assert "disclaimer" in data

    app.dependency_overrides.clear()
