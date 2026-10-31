"""Comprehensive unit and API tests for Statutes, Versioning, and Concordance (Task T-15 / FR-13)."""

import datetime

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.api.search import get_sync_db
from app.db.models import Base, Court, DatasetSnapshot, Document, IngestionRun
from app.main import app
from app.statutes.concordance import (
    ConcordanceImportSchema,
    import_concordance_entry,
    lookup_concordance,
)
from app.statutes.loader import seed_official_statutes
from app.statutes.references import (
    extract_statute_references,
    link_statute_references_to_document,
)
from app.statutes.versions import (
    CRIMINAL_LAW_TRANSITION_DATE,
    generate_transition_notice,
    get_statute_status_at_date,
)


@pytest.fixture
def statute_db() -> Session:
    """Create in-memory database with official seeded statutes."""
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    session = Session(engine)

    # Seed the 6 central acts
    seed_official_statutes(session)

    yield session
    session.close()


def test_statute_seeding_and_temporal_versioning(statute_db: Session) -> None:
    """Verify official statutes are seeded with correct effective dates and repeal status."""
    # Status before 1 July 2024
    pre_transition = datetime.date(2023, 1, 1)
    assert get_statute_status_at_date("IPC", pre_transition) == "in_force"
    assert get_statute_status_at_date("CrPC", pre_transition) == "in_force"
    assert get_statute_status_at_date("BNS", pre_transition) == "not_yet_in_force"
    assert get_statute_status_at_date("BNSS", pre_transition) == "not_yet_in_force"

    # Status on/after 1 July 2024
    post_transition = datetime.date(2025, 1, 1)
    assert get_statute_status_at_date("IPC", post_transition) == "repealed"
    assert get_statute_status_at_date("CrPC", post_transition) == "repealed"
    assert get_statute_status_at_date("Evidence Act", post_transition) == "repealed"
    assert get_statute_status_at_date("BNS", post_transition) == "in_force"
    assert get_statute_status_at_date("BNSS", post_transition) == "in_force"
    assert get_statute_status_at_date("BSA", post_transition) == "in_force"


def test_criminal_transition_notice_generation() -> None:
    """Verify statutory transition notice correctly cites savings clauses (FR-13)."""
    notice_ipc = generate_transition_notice("IPC", section_no="302")
    assert notice_ipc["has_transition"] is True
    assert "Section 358(1) of Bharatiya Nyaya Sanhita, 2023" in notice_ipc["notice"]
    assert "repealed with effect from 1 July 2024" in notice_ipc["notice"]
    assert notice_ipc["transition_date"] == CRIMINAL_LAW_TRANSITION_DATE.isoformat()

    # Pre-2024 incident guidance
    notice_old_incident = generate_transition_notice(
        "IPC",
        section_no="302",
        date_of_incident=datetime.date(2022, 5, 10),
    )
    assert "Old Code Applicable" in notice_old_incident["applicability_guidance"]

    # Post-2024 incident guidance
    notice_new_incident = generate_transition_notice(
        "IPC",
        section_no="302",
        date_of_incident=datetime.date(2024, 8, 15),
    )
    assert "New Code Applicable" in notice_new_incident["applicability_guidance"]

    # Non-criminal act has no transition notice
    notice_arbitration = generate_transition_notice("Arbitration Act")
    assert notice_arbitration["has_transition"] is False
    assert notice_arbitration["notice"] is None


def test_concordance_import_and_rule_3_enforcement(statute_db: Session) -> None:
    """Test importing certified concordance rows and verify strict rejection of uncertified entries (Rule 3)."""
    # 1. Valid certified import (IPC 302 -> BNS 103)
    entry = ConcordanceImportSchema(
        old_statute_code="IPC",
        old_section_no="302",
        new_statute_code="BNS",
        new_section_no="103",
        source_url="https://egazette.gov.in/WriteReadData/2023/250883.pdf",  # type: ignore[arg-type]
        reviewed_by="ADV_SC_LEGAL_TEAM",
        reviewed_at=datetime.date(2024, 7, 2),
        note="Punishment for murder. Subsection (2) of BNS 103 adds specific provisions for mob lynching.",
    )
    imported = import_concordance_entry(statute_db, entry)
    assert imported.reviewed_by == "ADV_SC_LEGAL_TEAM"
    assert "250883.pdf" in imported.source_url

    # 2. Querying mapped section returns verified concordance
    res = lookup_concordance(statute_db, "IPC", "302")
    assert res["verified"] is True
    assert res["replacing_provision"]["statute_code"] == "BNS"
    assert res["replacing_provision"]["section_no"] == "103"
    assert res["replacing_provision"]["heading"] == "Punishment for murder"
    assert res["reviewed_by"] == "ADV_SC_LEGAL_TEAM"
    assert "mob lynching" in res["note"]

    # 3. Querying unmapped section returns verified=False with explicit Rule 3 notice
    res_unmapped = lookup_concordance(statute_db, "IPC", "420")
    assert res_unmapped["verified"] is False
    assert res_unmapped["replacing_provision"] is None
    assert (
        "No verified concordance mapping has been officially certified" in res_unmapped["message"]
    )
    assert (
        "Needhi does not guess or invent mappings" in res_unmapped["message"]
        or "LegalJarvis does not guess or invent mappings" in res_unmapped["message"]
    )

    # 4. Rejection when section does not exist
    with pytest.raises(ValueError, match="does not exist"):
        import_concordance_entry(
            statute_db,
            ConcordanceImportSchema(
                old_statute_code="IPC",
                old_section_no="99999",
                new_statute_code="BNS",
                new_section_no="103",
                source_url="https://egazette.gov.in/test.pdf",  # type: ignore[arg-type]
                reviewed_by="REVIEWER_A",
            ),
        )


def test_statute_reference_extractor_and_document_linking(statute_db: Session) -> None:
    """Test extracting references like 'Section 302 IPC' and associating them with documents."""
    text = (
        "The appellant was convicted under Section 302 IPC and Section 120B of the Indian Penal Code. "
        "The High Court declined anticipatory bail under Section 438 CrPC."
    )
    refs = extract_statute_references(text)
    assert len(refs) == 3
    assert {"statute_code": "IPC", "section_no": "302"} in refs
    assert {"statute_code": "IPC", "section_no": "120B"} in refs
    assert {"statute_code": "CrPC", "section_no": "438"} in refs

    # Test linking to document in DB
    court = Court(code="sc", name="Supreme Court of India", level="supreme")
    snapshot = DatasetSnapshot(
        source_key="sc",
        source_url="https://sc.gov.in",
        license="CC-BY-4.0",
        attribution="Dattam Labs",
        manifest_path="m.sha256",
    )
    statute_db.add_all([court, snapshot])
    statute_db.commit()

    run = IngestionRun(snapshot_id=snapshot.id, params={"year": 2023}, status="success")
    statute_db.add(run)
    statute_db.commit()

    doc = Document(
        run_id=run.id,
        court_id=court.id,
        external_id="doc_stat_test_1",
        title="State v. Accused",
        source_file_path="dummy.pdf",
        source_sha256="f" * 64,
        extraction_status="ok",
    )
    statute_db.add(doc)
    statute_db.commit()
    statute_db.refresh(doc)

    linked = link_statute_references_to_document(statute_db, doc.id, text)
    assert len(linked) >= 2


@pytest.mark.asyncio
async def test_statute_api_endpoints(statute_db: Session) -> None:
    """Test /v1/statutes and /v1/statutes/lookup endpoints."""

    def override_db():
        yield statute_db

    app.dependency_overrides[get_sync_db] = override_db

    # Pre-seed one concordance mapping
    import_concordance_entry(
        statute_db,
        ConcordanceImportSchema(
            old_statute_code="CrPC",
            old_section_no="438",
            new_statute_code="BNSS",
            new_section_no="482",
            source_url="https://egazette.gov.in/WriteReadData/2023/250884.pdf",  # type: ignore[arg-type]
            reviewed_by="BENCH_REVIEWER_1",
            note="Direction for grant of bail to person apprehending arrest",
        ),
    )

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. List statutes
        resp = await client.get("/v1/statutes")
        assert resp.status_code == 200
        statutes = resp.json()
        assert len(statutes) == 6
        ipc_meta = next(s for s in statutes if s["short_name"] == "IPC")
        assert ipc_meta["current_status"] == "repealed"
        assert ipc_meta["act_year"] == 1860

        bns_meta = next(s for s in statutes if s["short_name"] == "BNS")
        assert bns_meta["current_status"] == "in_force"
        assert bns_meta["act_year"] == 2023

        # 2. Lookup CrPC 438 (has verified concordance)
        lookup_resp = await client.get("/v1/statutes/lookup?statute_code=CrPC&section_no=438")
        assert lookup_resp.status_code == 200
        data = lookup_resp.json()
        assert data["found_in_database"] is True
        assert data["current_status"] == "repealed"
        assert data["transition_notice"]["has_transition"] is True
        assert "Section 531(2)(a)" in data["transition_notice"]["notice"]
        assert data["concordance"]["verified"] is True
        assert data["concordance"]["replacing_provision"]["statute_code"] == "BNSS"
        assert data["concordance"]["replacing_provision"]["section_no"] == "482"
        assert data["concordance"]["reviewed_by"] == "BENCH_REVIEWER_1"

        # 3. Lookup unmapped section (IPC 420)
        lookup_unmapped = await client.get("/v1/statutes/lookup?statute_code=IPC&section_no=420")
        assert lookup_unmapped.status_code == 200
        unmapped_data = lookup_unmapped.json()
        assert unmapped_data["concordance"]["verified"] is False
        assert unmapped_data["concordance"]["replacing_provision"] is None
        assert "does not guess or invent mappings" in unmapped_data["concordance"]["message"]

        # 4. Reviewer import endpoint
        import_resp = await client.post(
            "/v1/statutes/concordance/import",
            json={
                "old_statute_code": "IPC",
                "old_section_no": "120A",
                "new_statute_code": "BNS",
                "new_section_no": "61",
                "source_url": "https://egazette.gov.in/WriteReadData/2023/250883.pdf",
                "reviewed_by": "LEGAL_REVIEWER_B",
                "note": "Criminal conspiracy definition",
            },
        )
        assert import_resp.status_code == 200
        assert import_resp.json()["status"] == "success"

    app.dependency_overrides.clear()
