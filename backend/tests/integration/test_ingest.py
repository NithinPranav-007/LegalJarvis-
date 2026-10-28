"""Integration tests for corpus ingestion, checksums, and idempotency (Task T-04 / T-FR01)."""

import tarfile
from pathlib import Path

import pandas as pd
import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from app.core.checksum import generate_manifest, verify_manifest
from app.db.models import Base, Court, Document
from app.ingest.download import ingest_supreme_court_year, unpack_tar


@pytest.fixture
def in_memory_db() -> Session:
    """Isolated database session for ingestion testing."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        yield session


def test_checksum_manifest_lifecycle(tmp_path: Path) -> None:
    source_dir = tmp_path / "files"
    source_dir.mkdir()

    f1 = source_dir / "case_1.pdf"
    f2 = source_dir / "case_2.pdf"
    f1.write_bytes(b"%PDF-1.4 test case 1 content")
    f2.write_bytes(b"%PDF-1.4 test case 2 content")

    manifest = tmp_path / "manifest.sha256"
    generate_manifest(source_dir, manifest)
    assert manifest.exists()

    # Verification passes
    assert verify_manifest(manifest, source_dir) is True

    # Tampered file fails verification
    f1.write_bytes(b"%PDF-1.4 tampered content")
    assert verify_manifest(manifest, source_dir) is False


def test_unpack_tar_integrity(tmp_path: Path) -> None:
    tar_path = tmp_path / "test.tar"
    extract_dir = tmp_path / "extracted"

    # Create test tar
    with tarfile.open(tar_path, "w") as tar:
        f_path = tmp_path / "doc1.pdf"
        f_path.write_bytes(b"%PDF dummy data")
        tar.add(f_path, arcname="doc1.pdf")

    unpacked = unpack_tar(tar_path, extract_dir)
    assert len(unpacked) == 1
    assert "doc1.pdf" in unpacked
    assert (extract_dir / "doc1.pdf").exists()


def test_ingestion_idempotency_with_fixtures(in_memory_db: Session, tmp_path: Path) -> None:
    data_dir = tmp_path / "sc_year=2023"
    data_dir.mkdir()
    pdf_dir = data_dir / "pdf"
    pdf_dir.mkdir()

    # Create 3 mock fixture PDFs
    cases = ["2023_1_10_20", "2023_1_21_30", "2023_1_31_40"]
    for c in cases:
        pdf_file = pdf_dir / f"{c}_EN.pdf"
        pdf_file.write_bytes(b"%PDF-1.4 fake court judgment text " + c.encode())

    # Create mock tar
    tar_path = data_dir / "english.tar"
    with tarfile.open(tar_path, "w") as tar:
        for c in cases:
            pdf_file = pdf_dir / f"{c}_EN.pdf"
            tar.add(pdf_file, arcname=f"{c}_EN.pdf")

    # Create mock parquet metadata
    df = pd.DataFrame(
        [
            {
                "path": c,
                "title": f"Case Title {c}",
                "decision_date": "15-05-2023",
                "nc_display": f"2023 INSC {c[-2:]}",
                "court": "Supreme Court of India",
            }
            for c in cases
        ]
    )
    df.to_parquet(data_dir / "metadata.parquet")

    # Seed Court
    court = Court(code="sc", name="Supreme Court of India", level="supreme")
    in_memory_db.add(court)
    in_memory_db.commit()

    # First ingestion run
    res1 = ingest_supreme_court_year(
        db=in_memory_db,
        year=2023,
        data_dir=data_dir,
        skip_download=True,
    )
    assert res1["status"] == "success"
    assert res1["n_registered"] == 3
    assert res1["n_skipped"] == 0

    docs_count1 = in_memory_db.execute(select(Document)).scalars().all()
    assert len(docs_count1) == 3

    # Verify fields of registered document
    first_doc = docs_count1[0]
    assert "Case Title" in first_doc.title
    assert first_doc.neutral_citation.startswith("2023 INSC")
    assert first_doc.decision_date is not None
    assert len(first_doc.source_sha256) == 64

    # Second ingestion run (Idempotency test: T-FR01)
    res2 = ingest_supreme_court_year(
        db=in_memory_db,
        year=2023,
        data_dir=data_dir,
        skip_download=True,
    )
    assert res2["status"] == "success"
    assert res2["n_registered"] == 0
    assert res2["n_skipped"] == 3  # All 3 were skipped, 0 new rows registered!

    docs_count2 = in_memory_db.execute(select(Document)).scalars().all()
    assert len(docs_count2) == 3  # Count remains exactly 3!
