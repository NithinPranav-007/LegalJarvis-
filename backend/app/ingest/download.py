"""Corpus downloader, checksum verifier, and registration pipeline (Task T-04)."""

import tarfile
import urllib.request
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pandas as pd  # type: ignore[import-untyped]
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.checksum import compute_sha256, generate_manifest
from app.core.config import settings
from app.db.models import Court, DatasetSnapshot, Document, IngestionRun

HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) LegalJarvis/0.1"}


class IngestionError(Exception):
    """Custom exception raised during corpus download or registration."""
    pass


def check_remote_size(url: str) -> int:
    """Perform HEAD request to determine remote file size in bytes."""
    if not url.startswith(("https://", "http://")):
        raise IngestionError(f"Unsupported URL scheme: {url}")
    req = urllib.request.Request(url, method="HEAD", headers=HEADERS)
    with urllib.request.urlopen(req, timeout=15) as resp:  # nosec B310
        return int(resp.headers.get("Content-Length", 0))


def download_file_with_gate(
    url: str,
    dest_path: Path,
    max_gb: float = settings.MAX_DOWNLOAD_GB,
    force: bool = False,
) -> int:
    """Download remote file after validating size against MAX_DOWNLOAD_GB gate."""
    size_bytes = check_remote_size(url)
    size_gb = size_bytes / (1024 * 1024 * 1024)

    if size_gb > max_gb and not force:
        raise IngestionError(
            f"Download size {size_gb:.2f} GB exceeds MAX_DOWNLOAD_GB ({max_gb} GB). "
            f"Specify force=True to proceed."
        )

    dest_path.parent.mkdir(parents=True, exist_ok=True)
    if dest_path.exists() and dest_path.stat().st_size == size_bytes:
        print(f"File already downloaded and size matches: {dest_path}")
        return size_bytes

    print(f"Downloading {url} ({size_bytes / (1024*1024):.2f} MB)...")
    if not url.startswith(("https://", "http://")):
        raise IngestionError(f"Unsupported URL scheme: {url}")
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=120) as resp, open(dest_path, "wb") as out_f:  # nosec B310
        while chunk := resp.read(65536):
            out_f.write(chunk)

    print(f"Downloaded successfully: {dest_path} ({dest_path.stat().st_size} bytes)")
    return size_bytes


def unpack_tar(tar_path: Path, extract_dir: Path) -> list[str]:
    """Verify tar archive integrity and unpack members into extract_dir."""
    extract_dir.mkdir(parents=True, exist_ok=True)
    extracted_files = []
    print(f"Unpacking {tar_path} into {extract_dir}...")
    with tarfile.open(tar_path, "r:*") as tar:
        for member in tar:
            if member.isfile():
                try:
                    tar.extract(member, path=extract_dir, filter="data")
                except TypeError:
                    tar.extract(member, path=extract_dir)
                extracted_files.append(member.name)
    print(f"Unpacked {len(extracted_files)} files.")
    return extracted_files


def ingest_supreme_court_year(
    db: Session,
    year: int = 2023,
    data_dir: Path | None = None,
    sample_limit: int | None = None,
    skip_download: bool = False,
) -> dict[str, Any]:
    """Ingest, verify, and register Supreme Court judgments for a given year."""
    if data_dir is None:
        data_dir = Path("data/raw/sc") / f"year={year}"

    data_dir.mkdir(parents=True, exist_ok=True)

    # 1. Ensure court record exists
    court = db.execute(select(Court).filter_by(code="sc")).scalar_one_or_none()
    if not court:
        court = Court(code="sc", name="Supreme Court of India", level="supreme")
        db.add(court)
        db.flush()

    # 2. Get or create snapshot record
    snapshot_url = (
        f"https://indian-supreme-court-judgments.s3.amazonaws.com/data/tar/year={year}/english/"
    )
    snapshot = db.execute(
        select(DatasetSnapshot).filter_by(source_key="sc_judgments", source_url=snapshot_url)
    ).scalar_one_or_none()

    manifest_path = Path("data/manifests") / f"sc_{year}_manifest.sha256"

    if not snapshot:
        snapshot = DatasetSnapshot(
            source_key="sc_judgments",
            source_url=snapshot_url,
            license="CC-BY-4.0",
            attribution="Indian Supreme Court Judgments, Dattam Labs, accessed from AWS Open Data Registry.",
            snapshot_note=f"Supreme Court English judgments for year {year}",
            manifest_path=str(manifest_path),
        )
        db.add(snapshot)
        db.flush()

    # 3. Create ingestion run record
    run = IngestionRun(
        snapshot_id=snapshot.id,
        params={"source": "sc", "year": year, "sample_limit": sample_limit},
        status="running",
    )
    db.add(run)
    db.commit()

    try:
        parquet_path = data_dir / "metadata.parquet"
        tar_path = data_dir / "english.tar"

        if not skip_download:
            parquet_url = f"https://indian-supreme-court-judgments.s3.amazonaws.com/metadata/parquet/year={year}/metadata.parquet"
            download_file_with_gate(parquet_url, parquet_path)

            tar_url = f"https://indian-supreme-court-judgments.s3.amazonaws.com/data/tar/year={year}/english/english.tar"
            download_file_with_gate(tar_url, tar_path)

        df_meta = pd.read_parquet(parquet_path)
        meta_by_path = {row["path"]: row for _, row in df_meta.iterrows()}

        # Unpack PDFs
        pdf_dir = data_dir / "pdf"
        unpacked_files = unpack_tar(tar_path, pdf_dir)

        # Generate manifest
        generate_manifest(pdf_dir, manifest_path)

        n_downloaded = len(unpacked_files)
        n_registered = 0
        n_skipped = 0
        n_failed = 0

        # Register documents in database
        items_to_process = unpacked_files[:sample_limit] if sample_limit else unpacked_files

        for filename in items_to_process:
            file_path = pdf_dir / filename
            if not file_path.is_file():
                continue

            # Strip suffix to find base path (e.g. 2023_16_872_887_EN.pdf -> 2023_16_872_887)
            base_id = filename.replace("_EN.pdf", "").replace(".pdf", "")
            meta = meta_by_path.get(base_id)

            sha256_hash = compute_sha256(file_path)

            # Check if document already registered
            existing_doc = db.execute(
                select(Document).filter_by(court_id=court.id, external_id=base_id)
            ).scalar_one_or_none()

            if existing_doc:
                n_skipped += 1
                continue

            decision_date = None
            if meta is not None and pd.notna(meta.get("decision_date")):
                try:
                    # format DD-MM-YYYY
                    decision_date = datetime.strptime(str(meta["decision_date"]), "%d-%m-%Y").date()
                except Exception:
                    decision_date = None

            raw_meta = meta.to_dict() if meta is not None else {}
            # remove raw_html from stored json to save memory/storage if large
            raw_meta.pop("raw_html", None)

            doc = Document(
                run_id=run.id,
                court_id=court.id,
                external_id=base_id,
                title=str(meta.get("title", "")) if meta is not None and pd.notna(meta.get("title")) else None,
                decision_date=decision_date,
                neutral_citation=str(meta.get("nc_display", "")) if meta is not None and pd.notna(meta.get("nc_display")) else None,
                language="en",
                source_file_path=str(file_path.relative_to(Path(".")) if file_path.is_relative_to(Path(".")) else file_path),
                source_sha256=sha256_hash,
                extraction_status="pending",
                raw_metadata=raw_meta,
            )
            db.add(doc)
            n_registered += 1

        db.commit()

        run.status = "success"
        run.n_downloaded = n_downloaded
        run.n_registered = n_registered
        run.finished_at = datetime.now(UTC)
        db.commit()

        return {
            "run_id": run.id,
            "status": "success",
            "n_downloaded": n_downloaded,
            "n_registered": n_registered,
            "n_skipped": n_skipped,
            "n_failed": n_failed,
        }

    except Exception as e:
        db.rollback()
        run.status = "failed"
        run.finished_at = datetime.now(UTC)
        db.commit()
        raise e
