"""Integration and API tests for POST /v1/search (Task T-07 / FR-04)."""

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.api.search import get_sync_db
from app.db.models import Base, Chunk, Court, DatasetSnapshot, Document, IngestionRun
from app.main import app


@pytest.fixture
def populated_db() -> Session:
    """Create in-memory database populated with real-style Indian judgment fixtures."""
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

    chunk1 = Chunk(
        document_id=doc1.id,
        para_no=1,
        segment_type="facts",
        start_char=0,
        end_char=80,
        text="A suit for specific performance was filed seeking enforcement of the agreement.",
    )
    chunk2 = Chunk(
        document_id=doc2.id,
        para_no=5,
        segment_type="reasoning",
        start_char=0,
        end_char=90,
        text="The levy of service tax on user development fee collected under the Airports Authority Act.",
    )
    session.add_all([chunk1, chunk2])
    session.commit()

    yield session
    session.close()


@pytest.mark.asyncio
async def test_search_api_endpoint(populated_db: Session) -> None:
    def override_db():
        yield populated_db

    # Override database dependency with populated in-memory database
    app.dependency_overrides[get_sync_db] = override_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Search for specific performance
        resp = await client.post(
            "/v1/search",
            json={"query": "specific performance"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["query"] == "specific performance"
        assert data["total"] >= 1
        assert len(data["results"]) >= 1

        first_hit = data["results"][0]
        assert "Eldeco Housing" in first_hit["title"]
        assert first_hit["court"] == "Supreme Court of India"
        assert first_hit["para_no"] == 1
        assert "specific performance" in first_hit["snippet"].lower()
        assert "attribution" in data
        assert "Dattam Labs" in data["attribution"]

    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_search_validation_error() -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Query too short (1 char < min_length 2)
        resp = await client.post(
            "/v1/search",
            json={"query": "a"},
        )
        assert resp.status_code == 422
