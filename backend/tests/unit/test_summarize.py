"""Unit and API tests for Structured Summarization and Rhetorical Role Segmentation (Task T-16 / FR-09)."""

import datetime

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.api.search import get_sync_db
from app.db.models import Base, Chunk, Court, DatasetSnapshot, Document, IngestionRun
from app.main import app
from app.summarize.segmenter_model import RhetoricalSegmenter
from app.summarize.summarizer import StructuredSummarizer


@pytest.fixture
def summary_db() -> Session:
    """In-memory database populated with multi-paragraph judgment fixture for summarization."""
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    session = Session(engine)

    court = Court(code="sc", name="Supreme Court of India", level="supreme")
    snapshot = DatasetSnapshot(
        source_key="sc", source_url="https://sc.gov.in", license="CC-BY-4.0", attribution="Dattam Labs", manifest_path="m.sha256"
    )
    session.add_all([court, snapshot])
    session.commit()

    run = IngestionRun(snapshot_id=snapshot.id, params={"year": 2023}, status="success")
    session.add(run)
    session.commit()

    doc = Document(
        run_id=run.id,
        court_id=court.id,
        external_id="summary_test_case_1",
        title="Gurbaksh Singh Sibbia v. State of Punjab",
        decision_date=datetime.date(1980, 4, 9),
        neutral_citation="1980 INSC 77",
        source_file_path="sc_sibbia.pdf",
        source_sha256="1" * 64,
        extraction_status="ok",
    )
    session.add(doc)
    session.commit()
    session.refresh(doc)

    chunks_data = [
        (
            1,
            "facts",
            "The appellants filed petitions before the High Court of Punjab and Haryana for anticipatory bail under Section 438.",
        ),
        (
            2,
            "issues",
            "The questions for determination are regarding the scope, ambit, and limitations on the power to grant anticipatory bail.",
        ),
        (
            3,
            "arguments",
            "Learned counsel for the appellant argued that the power under Section 438 is wide and not hedged in by rigid conditions.",
        ),
        (
            4,
            "reasoning",
            "We have carefully considered the statutory scheme. The power to grant anticipatory bail is of wide amplitude and should not be circumscribed by rules not contained in the Code.",
        ),
        (
            5,
            "holding",
            "In the result, the judgment of the Full Bench of the High Court is set aside, and the matters are remanded for disposal in light of these principles.",
        ),
    ]

    for p_no, seg_type, txt in chunks_data:
        chunk = Chunk(
            document_id=doc.id,
            para_no=p_no,
            segment_type=seg_type,
            start_char=0,
            end_char=len(txt),
            text=txt,
        )
        session.add(chunk)
    session.commit()

    yield session
    session.close()


def test_summary_structured_per_sentence_paragraph_anchors(summary_db: Session) -> None:
    """Verify summaries have per-sentence source paragraph numbers and verifier applies (FR-09 / T-16)."""
    summarizer = StructuredSummarizer()
    summary = summarizer.summarize_document(summary_db, document_id=1, max_sentences_per_section=3)

    assert summary.document_id == 1
    assert "Gurbaksh Singh Sibbia" in summary.case_title

    # Check that all 5 rhetorical sections are present
    assert len(summary.facts) > 0
    assert len(summary.issues) > 0
    assert len(summary.arguments) > 0
    assert len(summary.reasoning) > 0
    assert len(summary.holding) > 0

    # Strict invariant: Every sentence has at least one source paragraph number
    for sec_name, sentences in [
        ("facts", summary.facts),
        ("issues", summary.issues),
        ("arguments", summary.arguments),
        ("reasoning", summary.reasoning),
        ("holding", summary.holding),
    ]:
        for s in sentences:
            assert len(s.source_para_nos) >= 1, f"Sentence in {sec_name} missing paragraph citation: {s.text}"
            assert s.supported is True, f"Sentence in {sec_name} failed verifier support: {s.text}"
            assert s.support_score >= 0.20

    # Faithfulness score
    assert summary.overall_faithfulness_score >= 0.80
    assert summary.supported_sentences == summary.total_sentences
    assert summary.unsupported_sentences == 0


def test_summary_rhetorical_role_segmenter_and_macro_f1() -> None:
    """Test rhetorical role segmenter rules and calculate macro-F1 on benchmark sample."""
    segmenter = RhetoricalSegmenter()

    # Rule checks
    assert segmenter.predict_role("Brief facts of the case are that an FIR was registered.") == "facts"
    assert segmenter.predict_role("The question of law for determination is whether...") == "issues"
    assert segmenter.predict_role("Learned counsel submitted that the appellant is innocent.") == "arguments"
    assert segmenter.predict_role("In our considered view, the statutory interpretation requires...") == "reasoning"
    assert segmenter.predict_role("In the result, the appeal is dismissed with costs.") == "holding"

    # Evaluation on a dev gold set
    gold_dev_data = [
        {"text": "Brief facts of the prosecution case are...", "label": "facts", "para_no": 1},
        {"text": "The point for determination is whether Section 438 applies...", "label": "issues", "para_no": 2},
        {"text": "Learned Senior Counsel argued that the trial court erred...", "label": "arguments", "para_no": 3},
        {"text": "We have considered the ratio of the precedent in Sibbia...", "label": "ratio of the decision", "para_no": 4},
        {"text": "In the result, the appeal is allowed and order is set aside...", "label": "holding", "para_no": 5},
    ]

    metrics = segmenter.evaluate_on_dataset(gold_dev_data)
    assert metrics["macro_f1"] >= 0.70
    assert metrics["accuracy"] >= 0.80
    assert metrics["total"] == 5


@pytest.mark.asyncio
async def test_summary_api_endpoints(summary_db: Session) -> None:
    """Test POST /v1/summarize and GET /v1/documents/{id}/summary API endpoints."""
    def override_db():
        yield summary_db

    app.dependency_overrides[get_sync_db] = override_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. POST /v1/summarize
        resp = await client.post(
            "/v1/summarize",
            json={"document_id": 1, "max_sentences_per_section": 3},
        )
        assert resp.status_code == 200, resp.text
        data = resp.json()
        assert data["document_id"] == 1
        assert len(data["facts"]) > 0
        assert data["facts"][0]["source_para_nos"] == [1]
        assert data["holding"][0]["source_para_nos"] == [5]
        assert data["overall_faithfulness_score"] >= 0.80

        # 2. GET /v1/documents/1/summary
        get_resp = await client.get("/v1/documents/1/summary")
        assert get_resp.status_code == 200
        get_data = get_resp.json()
        assert get_data["case_title"] == "Gurbaksh Singh Sibbia v. State of Punjab"

        # 3. 404 on missing document
        missing_resp = await client.get("/v1/documents/99999/summary")
        assert missing_resp.status_code == 404

    app.dependency_overrides.clear()
