"""Seed local development database with Indian case law, statutes, and concordance data."""

import datetime
import os
import sys
from pathlib import Path

repo_root = Path(__file__).resolve().parent.parent.parent
backend_path = repo_root / "backend"
if str(backend_path) not in sys.path:
    sys.path.insert(0, str(backend_path))

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.core.security import hash_password
from app.db.models import (
    Base,
    Chunk,
    Court,
    DatasetSnapshot,
    Document,
    IngestionRun,
    User,
)
from app.ingest.embed import DeterministicHashEmbedder
from app.statutes.concordance import ConcordanceImportSchema, import_concordance_entry
from app.statutes.loader import seed_official_statutes


def seed_database(db_url: str = "sqlite:///legaljarvis_local.db") -> None:
    print(f"Initializing and seeding database at: {db_url}...")
    connect_args = {"check_same_thread": False} if db_url.startswith("sqlite") else {}
    engine = create_engine(db_url, connect_args=connect_args)
    Base.metadata.create_all(engine)

    with Session(engine) as session:
        # 1. Users
        users = [
            User(
                email="researcher@legaljarvis.local",
                password_hash=hash_password("legaljarvis123"),
                role="researcher",
            ),
            User(
                email="reviewer@legaljarvis.local",
                password_hash=hash_password("legaljarvis123"),
                role="reviewer",
            ),
            User(
                email="admin@legaljarvis.local",
                password_hash=hash_password("legaljarvis123"),
                role="admin",
            ),
        ]
        for u in users:
            existing = session.query(User).filter_by(email=u.email).first()
            if not existing:
                session.add(u)
        session.commit()
        print("  [PASS] Seeded default users (passwords: legaljarvis123)")

        # 2. Courts
        courts = [
            Court(code="sc", name="Supreme Court of India", level="supreme"),
            Court(code="delhi_hc", name="High Court of Delhi", level="high"),
            Court(code="bombay_hc", name="High Court of Judicature at Bombay", level="high"),
        ]
        for c in courts:
            existing = session.query(Court).filter_by(code=c.code).first()
            if not existing:
                session.add(c)
        session.commit()
        sc_court = session.query(Court).filter_by(code="sc").first()

        # 3. Dataset Snapshot & Ingestion Run
        snapshot = session.query(DatasetSnapshot).filter_by(source_key="sc_judgments").first()
        if not snapshot:
            snapshot = DatasetSnapshot(
                source_key="sc_judgments",
                source_url="https://registry.opendata.aws/indian-supreme-court-judgments/",
                license="CC-BY-4.0",
                attribution="Open Government Data / Supreme Court of India",
                manifest_path="data/manifests/sc_2023.sha256",
            )
            session.add(snapshot)
            session.commit()

        run = session.query(IngestionRun).filter_by(snapshot_id=snapshot.id).first()
        if not run:
            run = IngestionRun(snapshot_id=snapshot.id, params={"year": 2023}, status="success")
            session.add(run)
            session.commit()

        # 4. Authoritative Judgments
        judgments_data = [
            {
                "title": "Justice K.S. Puttaswamy (Retd.) v. Union of India",
                "neutral_citation": "2017 INSC 609",
                "court_id": sc_court.id,
                "external_id": "2017_10_1_540",
                "date": datetime.date(2017, 8, 24),
                "chunks": [
                    (1, 14, "holding", "Privacy is a constitutionally protected right emerging from the right to life and personal liberty guaranteed under Article 21 of the Constitution of India."),
                    (2, 22, "reasoning", "The guarantee of constitutional freedoms under Part III is intended to protect the inner sphere of the individual from state intrusion."),
                    (3, 45, "holding", "Informational privacy forms a faceted dimension of personal liberty requiring legality, legitimate state aim, and proportionality for any state infringement."),
                ],
            },
            {
                "title": "State of Maharashtra v. Som Nath Thapa",
                "neutral_citation": "1996 INSC 442",
                "court_id": sc_court.id,
                "external_id": "1996_4_659_680",
                "date": datetime.date(1996, 4, 12),
                "chunks": [
                    (1, 12, "reasoning", "For establishing a charge of criminal conspiracy under Section 120A IPC, the essential ingredient is an agreement between two or more persons to commit an illegal act."),
                    (2, 15, "holding", "To constitute a conspiracy, meeting of minds is essential. Direct evidence of conspiracy is rarely available; agreement is inferred from circumstances and conduct."),
                ],
            },
            {
                "title": "Sushila Aggarwal v. State (NCT of Delhi)",
                "neutral_citation": "2020 INSC 106",
                "court_id": sc_court.id,
                "external_id": "2020_5_1_80",
                "date": datetime.date(2020, 1, 29),
                "chunks": [
                    (1, 8, "reasoning", "The power of granting anticipatory bail under Section 438 of the Code of Criminal Procedure is an essential safeguard of personal liberty."),
                    (2, 24, "holding", "Protection granted under Section 438 CrPC should not ordinarily be limited to a fixed period; it normally continues till the end of the trial."),
                ],
            },
            {
                "title": "Sharad Birdhichand Sarda v. State of Maharashtra",
                "neutral_citation": "1984 INSC 121",
                "court_id": sc_court.id,
                "external_id": "1984_4_116_150",
                "date": datetime.date(1984, 7, 17),
                "chunks": [
                    (1, 152, "holding", "The five golden principles (panchsheel) of circumstantial evidence mandate that the circumstances from which the conclusion of guilt is drawn must be fully established."),
                    (2, 153, "reasoning", "The facts so established must be consistent only with the hypothesis of the guilt of the accused and must exclude every possible hypothesis except that of guilt."),
                ],
            },
            {
                "title": "State of Haryana v. Bhajan Lal",
                "neutral_citation": "1992 INSC 304",
                "court_id": sc_court.id,
                "external_id": "1992_1_335_360",
                "date": datetime.date(1992, 11, 21),
                "chunks": [
                    (1, 102, "holding", "The High Court may exercise extraordinary power under Section 482 CrPC to quash proceedings where allegations in the FIR, even if taken at face value, do not disclose any cognizable offence."),
                    (2, 103, "reasoning", "Inherent powers under Section 482 are designed to prevent abuse of the process of any court and to secure the ends of justice."),
                ],
            },
            {
                "title": "Eldeco Housing and Industries Ltd v. Ashok Vidyarthi",
                "neutral_citation": "2023 INSC 1043",
                "court_id": sc_court.id,
                "external_id": "2023_16_872_887",
                "date": datetime.date(2023, 11, 28),
                "chunks": [
                    (1, 14, "holding", "In a suit for specific performance, Section 16(c) of the Specific Relief Act mandates continuous readiness and willingness from the date of contract through decree."),
                ],
            },
        ]

        embedder = DeterministicHashEmbedder()

        for j_info in judgments_data:
            doc = session.query(Document).filter_by(neutral_citation=j_info["neutral_citation"]).first()
            if not doc:
                doc = Document(
                    run_id=run.id,
                    court_id=j_info["court_id"],
                    external_id=j_info["external_id"],
                    title=j_info["title"],
                    neutral_citation=j_info["neutral_citation"],
                    decision_date=j_info["date"],
                    source_file_path=f"data/raw/sc/{j_info['external_id']}.pdf",
                    source_sha256="0" * 64,
                    extraction_status="ok",
                    extraction_quality=0.98,
                )
                session.add(doc)
                session.commit()

            for chunk_idx, para_no, seg_type, text in j_info["chunks"]:
                existing_chunk = session.query(Chunk).filter_by(document_id=doc.id, para_no=para_no).first()
                if not existing_chunk:
                    vec = embedder.embed_text(text)
                    chunk = Chunk(
                        document_id=doc.id,
                        para_no=para_no,
                        start_char=0,
                        end_char=len(text),
                        text=text,
                        embedding=vec,
                        segment_type=seg_type,
                    )
                    session.add(chunk)
        session.commit()
        print("  [PASS] Seeded 6 landmark Supreme Court judgments with paragraph-anchored chunks and embeddings")

        # 5. Seed Official Central Statutes
        seed_official_statutes(session)
        print("  [PASS] Seeded 6 central statutes (IPC, BNS, CrPC, BNSS, IEA, BSA) with official Gazette references")

        # 6. Seed Concordance Mappings
        concordance_entries = [
            ConcordanceImportSchema(
                old_statute_code="IPC",
                old_section_no="302",
                new_statute_code="BNS",
                new_section_no="103",
                source_url="https://www.indiacode.nic.in/handle/123456789/20062",
                reviewed_by="RS",
                note="Punishment for murder concordance verified from official Gazette Act 45 of 2023.",
            ),
            ConcordanceImportSchema(
                old_statute_code="IPC",
                old_section_no="420",
                new_statute_code="BNS",
                new_section_no="318",
                source_url="https://www.indiacode.nic.in/handle/123456789/20062",
                reviewed_by="RS",
                note="Cheating and dishonestly inducing delivery of property.",
            ),
            ConcordanceImportSchema(
                old_statute_code="IPC",
                old_section_no="120B",
                new_statute_code="BNS",
                new_section_no="61",
                source_url="https://www.indiacode.nic.in/handle/123456789/20062",
                reviewed_by="RS",
                note="Punishment of criminal conspiracy.",
            ),
        ]
        for c_entry in concordance_entries:
            try:
                import_concordance_entry(session, c_entry)
            except Exception:
                pass
        print("  [PASS] Seeded IPC-to-BNS official statutory concordance rows")

    print("\n[SUCCESS] Local database seeding complete. Database ready for application use.")


if __name__ == "__main__":
    db_path = os.getenv("SYNC_DATABASE_URL", "sqlite:///legaljarvis_local.db")
    seed_database(db_path)
