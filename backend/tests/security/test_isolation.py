"""Security and privacy isolation tests for user document uploads (Task T-17 / FR-08, T-FR08)."""

import datetime
import io
import logging
from pathlib import Path

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.core.security import create_access_token, hash_password
from app.db.models import (
    Base,
    Chunk,
    Court,
    DatasetSnapshot,
    Document,
    IngestionRun,
    User,
    UserDocument,
)
from app.db.rls import POSTGRES_RLS_STATEMENTS
from app.db.session import get_sync_db
from app.jobs.retention import purge_expired_documents
from app.main import app


@pytest.fixture
def db_session():
    """Create clean SQLite in-memory test database."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    with Session(engine) as session:
        # Seed test court and snapshot
        snap = DatasetSnapshot(
            source_key="test_snap",
            source_url="https://example.com/test",
            license="CC-BY-4.0",
            attribution="Test Open Data",
            manifest_path="manifest.json",
        )
        session.add(snap)
        session.flush()

        run = IngestionRun(
            snapshot_id=snap.id,
            params={"mode": "test"},
            status="success",
            git_commit="test_commit",
        )
        session.add(run)

        court = Court(code="sc", name="Supreme Court of India", level="supreme")
        session.add(court)

        # Seed 2 test users: User A (Researcher), User B (Researcher)
        user_a = User(
            id=101,
            email="user_a@example.com",
            password_hash=hash_password("passwordA123"),
            role="researcher",
        )
        user_b = User(
            id=102,
            email="user_b@example.com",
            password_hash=hash_password("passwordB123"),
            role="researcher",
        )
        session.add_all([user_a, user_b])

        # Seed one public document
        pub_doc = Document(
            id=1,
            run_id=run.id,
            court_id=court.id,
            external_id="pub_doc_1",
            title="Public Landmark Judgment",
            language="en",
            source_file_path="dummy_pub.pdf",
            source_sha256="1" * 64,
            extraction_status="ok",
            owner_user_id=None,
        )
        session.add(pub_doc)
        session.flush()

        pub_chunk = Chunk(
            id=1,
            document_id=pub_doc.id,
            para_no=1,
            segment_type="reasoning",
            start_char=0,
            end_char=50,
            text="This is a public precedent on constitutional validity.",
            owner_user_id=None,
        )
        session.add(pub_chunk)
        session.commit()

        yield session

    Base.metadata.drop_all(bind=engine)


@pytest.mark.asyncio
async def test_user_document_cross_user_isolation(db_session: Session):
    """T-FR08: Verify that User B receives 404 on User A's private document and 0 chunks in search."""
    token_a = create_access_token(data={"sub": "101", "role": "researcher"})
    token_b = create_access_token(data={"sub": "102", "role": "researcher"})

    app.dependency_overrides[get_sync_db] = lambda: db_session

    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            # 1. User A uploads a private document
            file_content = b"Confidential memo regarding arbitration agreement and dispute settlement.\n\nParagraph 2: The settlement amount is 5 crores."
            files = {"file": ("private_settlement.txt", file_content, "text/plain")}
            headers_a = {"Authorization": f"Bearer {token_a}"}

            upload_resp = await client.post("/v1/documents/upload", files=files, headers=headers_a)
            assert upload_resp.status_code == 201, upload_resp.text
            data = upload_resp.json()
            doc_id = data["document_id"]
            assert data["chunk_count"] >= 1

            # 2. User A can retrieve the document
            get_a = await client.get(f"/v1/documents/{doc_id}", headers=headers_a)
            assert get_a.status_code == 200
            assert get_a.json()["title"] == "private_settlement.txt"

            # 3. User B receives 404 NOT FOUND on User A's document (preventing existence leak)
            headers_b = {"Authorization": f"Bearer {token_b}"}
            get_b = await client.get(f"/v1/documents/{doc_id}", headers=headers_b)
            assert get_b.status_code == 404
            assert f"Document with ID {doc_id} not found" in get_b.json()["detail"]

            # 4. Anonymous user receives 404 NOT FOUND
            get_anon = await client.get(f"/v1/documents/{doc_id}")
            assert get_anon.status_code == 404

            # 5. Search isolation: User B searches for words unique to User A's document
            search_b = await client.post(
                "/v1/search",
                json={"query": "arbitration settlement 5 crores", "mode": "lexical"},
                headers=headers_b,
            )
            assert search_b.status_code == 200
            b_results = search_b.json()["results"]
            # Assert User B retrieved zero chunks belonging to User A's doc
            assert all(r["document_id"] != doc_id for r in b_results)

            # 6. Anonymous search also retrieves zero chunks
            search_anon = await client.post(
                "/v1/search",
                json={"query": "arbitration settlement 5 crores", "mode": "lexical"},
            )
            assert search_anon.status_code == 200
            assert all(r["document_id"] != doc_id for r in search_anon.json()["results"])

            # 7. User A searches and retrieves their own chunk
            search_a = await client.post(
                "/v1/search",
                json={"query": "arbitration settlement", "mode": "lexical"},
                headers=headers_a,
            )
            assert search_a.status_code == 200
            a_results = search_a.json()["results"]
            assert any(r["document_id"] == doc_id for r in a_results)

    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_document_deletion_removes_files_chunks_and_records(db_session: Session, tmp_path: Path):
    """Verify that deleting a document purges disk file, chunk records, and document metadata."""
    token_a = create_access_token(data={"sub": "101", "role": "researcher"})
    token_b = create_access_token(data={"sub": "102", "role": "researcher"})

    app.dependency_overrides[get_sync_db] = lambda: db_session

    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            headers_a = {"Authorization": f"Bearer {token_a}"}
            headers_b = {"Authorization": f"Bearer {token_b}"}

            # User A uploads a document
            file_content = b"Text for deletion test. Paragraph 1: Important privileged legal opinion."
            files = {"file": ("opinion_to_delete.txt", file_content, "text/plain")}
            upload_resp = await client.post("/v1/documents/upload", files=files, headers=headers_a)
            assert upload_resp.status_code == 201
            doc_id = upload_resp.json()["document_id"]

            # Verify file exists on disk
            doc_record = db_session.get(Document, doc_id)
            assert doc_record is not None
            file_on_disk = Path(doc_record.source_file_path)
            assert file_on_disk.is_file()

            # Verify chunks exist in DB
            chunks = db_session.execute(select(Chunk).where(Chunk.document_id == doc_id)).scalars().all()
            assert len(chunks) > 0

            # User B attempts to delete User A's document -> 404
            del_b = await client.delete(f"/v1/documents/{doc_id}", headers=headers_b)
            assert del_b.status_code == 404

            # User A deletes document
            del_a = await client.delete(f"/v1/documents/{doc_id}", headers=headers_a)
            assert del_a.status_code == 200
            assert del_a.json()["status"] == "deleted"

            # Verify file is removed from disk
            assert not file_on_disk.exists()

            # Verify chunks are removed from DB
            remaining_chunks = db_session.execute(select(Chunk).where(Chunk.document_id == doc_id)).scalars().all()
            assert len(remaining_chunks) == 0

            # Verify Document record is removed
            assert db_session.get(Document, doc_id) is None
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_upload_format_and_size_validation(db_session: Session):
    """Verify 415 on unsupported file types, 413 on oversized files, 422 on empty files."""
    token_a = create_access_token(data={"sub": "101", "role": "researcher"})
    app.dependency_overrides[get_sync_db] = lambda: db_session

    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            headers = {"Authorization": f"Bearer {token_a}"}

            # 1. Unsupported extension (.exe) -> 415
            files = {"file": ("malicious.exe", b"binarycontent", "application/x-msdownload")}
            resp = await client.post("/v1/documents/upload", files=files, headers=headers)
            assert resp.status_code == 415
            assert "Unsupported media type" in resp.json()["detail"]

            # 2. Oversized file (> 20 MB) -> 413
            oversized_content = b"A" * (20 * 1024 * 1024 + 1024)
            files = {"file": ("huge_file.txt", oversized_content, "text/plain")}
            resp_huge = await client.post("/v1/documents/upload", files=files, headers=headers)
            assert resp_huge.status_code == 413
            assert "exceeds maximum allowed upload size" in resp_huge.json()["detail"]

            # 3. Empty content -> 422
            files = {"file": ("empty.txt", b"   \n\n   ", "text/plain")}
            resp_empty = await client.post("/v1/documents/upload", files=files, headers=headers)
            assert resp_empty.status_code == 422
            assert "no extractable content" in resp_empty.json()["detail"]
    finally:
        app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_logs_contain_no_document_text(db_session: Session):
    """Verify that logging captures operational metadata only, with ZERO document text leaked into logs."""
    token_a = create_access_token(data={"sub": "101", "role": "researcher"})
    app.dependency_overrides[get_sync_db] = lambda: db_session

    secret_canary = "SENSITIVE_LEGAL_TOKEN_XY7788_CANARY"
    content = f"Privileged client communication: {secret_canary}. Paragraph 2: Strategy on settlement.".encode()

    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            headers = {"Authorization": f"Bearer {token_a}"}
            files = {"file": ("privileged_client.txt", content, "text/plain")}

            doc_logger = logging.getLogger("app.api.documents")
            doc_logger.disabled = False
            doc_logger.setLevel(logging.INFO)
            log_stream = io.StringIO()
            handler = logging.StreamHandler(log_stream)
            doc_logger.addHandler(handler)

            try:
                resp = await client.post("/v1/documents/upload", files=files, headers=headers)
                assert resp.status_code == 201
                doc_id = resp.json()["document_id"]

                handler.flush()
                log_messages = log_stream.getvalue()

                # Assert canary text NEVER appears in any captured log message
                assert secret_canary not in log_messages
                assert "Privileged client communication" not in log_messages

                # Assert safe metadata IS logged
                assert f"doc_id={doc_id}" in log_messages
                assert "user_id=101" in log_messages
            finally:
                doc_logger.removeHandler(handler)
    finally:
        app.dependency_overrides.clear()


def test_retention_purge_job(db_session: Session, tmp_path: Path):
    """Verify scheduled purge deletes expired user documents while preserving active ones."""
    now = datetime.datetime.now(datetime.UTC)

    # 1. Create expired document (expired 2 days ago)
    file_expired = tmp_path / "expired.txt"
    file_expired.write_text("Expired doc content", encoding="utf-8")

    doc_expired = Document(
        external_id="user_101_expired",
        title="expired.txt",
        source_file_path=str(file_expired),
        source_sha256="e" * 64,
        extraction_status="ok",
        owner_user_id=101,
    )
    db_session.add(doc_expired)
    db_session.flush()

    udoc_expired = UserDocument(
        user_id=101,
        filename="expired.txt",
        sha256="e" * 64,
        expires_at=now - datetime.timedelta(days=2),
        status="processed",
        document_id=doc_expired.id,
    )
    db_session.add(udoc_expired)

    chunk_expired = Chunk(
        document_id=doc_expired.id,
        para_no=1,
        start_char=0,
        end_char=10,
        text="Expired...",
        owner_user_id=101,
    )
    db_session.add(chunk_expired)

    # 2. Create active document (expires in 28 days)
    file_active = tmp_path / "active.txt"
    file_active.write_text("Active doc content", encoding="utf-8")

    doc_active = Document(
        external_id="user_101_active",
        title="active.txt",
        source_file_path=str(file_active),
        source_sha256="a" * 64,
        extraction_status="ok",
        owner_user_id=101,
    )
    db_session.add(doc_active)
    db_session.flush()

    udoc_active = UserDocument(
        user_id=101,
        filename="active.txt",
        sha256="a" * 64,
        expires_at=now + datetime.timedelta(days=28),
        status="processed",
        document_id=doc_active.id,
    )
    db_session.add(udoc_active)
    db_session.commit()

    # Run purge job
    purged_count = purge_expired_documents(db_session, as_of=now)
    assert purged_count == 1

    # Assert expired document file and record are purged
    assert not file_expired.exists()
    assert db_session.get(Document, doc_expired.id) is None
    assert db_session.get(UserDocument, udoc_expired.id) is None

    # Assert active document file and record remain intact
    assert file_active.exists()
    assert db_session.get(Document, doc_active.id) is not None
    assert db_session.get(UserDocument, udoc_active.id) is not None


def test_postgres_rls_ddl_and_policies():
    """Verify PostgreSQL Row-Level Security statements conform to PRD D7 specification."""
    assert len(POSTGRES_RLS_STATEMENTS) == 4
    ddl_concat = " ".join(POSTGRES_RLS_STATEMENTS)

    assert "ALTER TABLE documents ENABLE ROW LEVEL SECURITY" in ddl_concat
    assert "ALTER TABLE chunks ENABLE ROW LEVEL SECURITY" in ddl_concat
    assert "CREATE POLICY documents_isolation_policy ON documents" in ddl_concat
    assert "CREATE POLICY chunks_isolation_policy ON chunks" in ddl_concat
    assert "owner_user_id IS NULL OR owner_user_id = NULLIF(current_setting('app.current_user_id', true), '')::bigint" in ddl_concat
