"""Tests for Document Viewer and Feedback API endpoints (Task T-14 / FR-05, FR-14)."""

import datetime

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.api.search import get_sync_db
from app.db.models import Base, Chunk, Court, DatasetSnapshot, Document, IngestionRun
from app.main import app


@pytest.fixture
def doc_db() -> Session:
    """In-memory database for testing document viewer and feedback."""
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

    run = IngestionRun(
        snapshot_id=snapshot.id,
        params={"year": 2023},
        status="success",
    )
    session.add(run)
    session.commit()

    doc = Document(
        run_id=run.id,
        court_id=court.id,
        external_id="1965_sc_72",
        title="State of Maharashtra v. Mayer Hans George",
        decision_date=datetime.date(1965, 3, 22),
        neutral_citation="1965 INSC 72",
        source_file_path="data/raw/sc/1965_72.pdf",
        source_sha256="a" * 64,
        extraction_status="ok",
        extraction_quality=0.98,
        raw_metadata={"bench": "K. Subba Rao, J.C. Shah, R.S. Bachawat", "dataset_name": "sc_2023"},
    )
    session.add(doc)
    session.commit()
    session.refresh(doc)

    c1 = Chunk(
        document_id=doc.id,
        para_no=1,
        segment_type="facts",
        start_char=0,
        end_char=17,
        text="Paragraph 1 text.",
    )
    c2 = Chunk(
        document_id=doc.id,
        para_no=2,
        segment_type="holding",
        start_char=19,
        end_char=44,
        text="Paragraph 2 holding text.",
    )
    session.add_all([c1, c2])
    session.commit()

    yield session
    session.close()


@pytest.mark.asyncio
async def test_get_document_and_list_endpoints(doc_db: Session) -> None:
    """Test retrieving full document text, chunks, and metadata for Case Viewer."""

    def override_db():
        yield doc_db

    app.dependency_overrides[get_sync_db] = override_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Test get document
        resp = await client.get("/v1/documents/1")
        assert resp.status_code == 200, resp.text
        data = resp.json()
        assert data["id"] == 1
        assert data["title"] == "State of Maharashtra v. Mayer Hans George"
        assert data["court_code"] == "sc"
        assert data["neutral_citation"] == "1965 INSC 72"
        assert data["bench"] == "K. Subba Rao, J.C. Shah, R.S. Bachawat"
        assert len(data["chunks"]) == 2
        assert data["chunks"][0]["para_no"] == 1
        assert data["chunks"][0]["segment_type"] == "facts"
        assert data["chunks"][1]["para_no"] == 2
        assert data["chunks"][1]["segment_type"] == "holding"
        assert "Paragraph 1 text." in data["text"]
        assert "Paragraph 2 holding text." in data["text"]
        assert (
            "Supreme Court" in data["attribution"]
            or "Open Government" in data["attribution"]
            or "Creative Commons" in data["attribution"]
        )

        # 2. Test 404 for non-existent document
        resp_404 = await client.get("/v1/documents/999999")
        assert resp_404.status_code == 404

        # 3. Test list documents
        resp_list = await client.get("/v1/documents?limit=10")
        assert resp_list.status_code == 200
        docs = resp_list.json()
        assert any(d["id"] == 1 for d in docs)

    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_submit_feedback_endpoint(doc_db: Session) -> None:
    """Test user feedback capture endpoint."""

    def override_db():
        yield doc_db

    app.dependency_overrides[get_sync_db] = override_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Positive feedback with supported label
        resp = await client.post(
            "/v1/feedback",
            json={
                "query": "What is the test for anticipatory bail?",
                "rating": 1,
                "label": "supported",
                "notes": "Accurate paragraph citation to Gurbaksh Singh Sibbia.",
            },
        )
        assert resp.status_code == 200, resp.text
        data = resp.json()
        assert data["status"] == "success"

        # Negative feedback with hallucinated label
        resp_neg = await client.post(
            "/v1/feedback",
            json={
                "query": "Section 420 IPC elements",
                "rating": -1,
                "label": "hallucinated",
                "notes": "Citation was irrelevant to cheating definition.",
            },
        )
        assert resp_neg.status_code == 200, resp_neg.text
        assert resp_neg.json()["status"] == "success"

        # Invalid label rejection
        resp_bad_label = await client.post(
            "/v1/feedback",
            json={"rating": 1, "label": "totally_random_invalid_label"},
        )
        assert resp_bad_label.status_code == 422

    app.dependency_overrides.clear()
