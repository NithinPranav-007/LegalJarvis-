"""Unit tests for query-relevance verification and regression prevention (Task T-12 / FR-06)."""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.db.models import Base, Court, Document, IngestionRun, DatasetSnapshot, Chunk
from app.ingest.embed import DeterministicHashEmbedder
from app.llm.gateway import LLMGateway
from app.llm.providers.fake import FakeProvider
from app.qa.orchestrator import QAOrchestrator
from app.qa.query_analysis import analyze_query
from app.retrieval.lexical import SearchResultItem
from app.verify.abstain import verify_and_filter_answer
from app.verify.relevance import verify_query_relevance


def make_item(
    chunk_id: int,
    doc_id: int,
    title: str,
    date: str,
    citation: str,
    snippet: str,
) -> SearchResultItem:
    return SearchResultItem(
        chunk_id=chunk_id,
        document_id=doc_id,
        title=title,
        court="Supreme Court of India",
        decision_date=date,
        neutral_citation=citation,
        para_no=153,
        segment_type="reasoning",
        snippet=snippet,
        score=1.0,
    )


def test_query_analysis_extracts_target_case_year_aspects() -> None:
    """Verify that query analysis extracts the target case, year, and legal aspects."""
    query = (
        "Search the Indian Supreme Court corpus for the 2023 judgment in All India Judges Association v. Union of India. "
        "Explain the main legal issue, the Court's reasoning, and its final decision using only retrieved passages."
    )
    analysis = analyze_query(query)

    assert analysis.target_case_name == "All India Judges Association v. Union of India"
    assert analysis.target_year == 2023
    assert "legal issue" in analysis.requested_aspects
    assert "reasoning" in analysis.requested_aspects
    assert "decision" in analysis.requested_aspects


def test_irrelevant_case_citation_fails_query_relevance() -> None:
    """Regression test: An answer citing Sharad Birdhichand Sarda for All India Judges Association must fail."""
    sarda_item = make_item(
        chunk_id=4,
        doc_id=4,
        title="Sharad Birdhichand Sarda v. State of Maharashtra",
        date="1984-07-17",
        citation="1984 INSC 121",
        snippet="Circumstantial evidence must satisfy the five golden principles enunciated by this Court.",
    )
    citation_map = {"[C1]": sarda_item}

    query = (
        "Search the Indian Supreme Court corpus for the 2023 judgment in All India Judges Association v. Union of India. "
        "Explain the main legal issue, the Court's reasoning, and its final decision using only retrieved passages."
    )

    # Even if the LLM faithfully quotes the Sarda snippet:
    answer = (
        "In Sharad Birdhichand Sarda v. State of Maharashtra [C1], the Supreme Court established "
        "that circumstantial evidence must satisfy the five golden principles."
    )

    relevance_res = verify_query_relevance(query, citation_map)
    assert relevance_res.is_fully_relevant is False
    assert "[C1]" in relevance_res.irrelevant_markers
    assert "Sharad Birdhichand Sarda" in relevance_res.citation_evaluations["[C1]"].rationale

    # verify_and_filter_answer must reject the citation and abstain
    v_res = verify_and_filter_answer(answer, citation_map, query=query)
    assert v_res.passed is False
    assert v_res.abstained is True
    assert "[C1]" in v_res.irrelevant_citations
    assert "irrelevant authorities cited" in v_res.abstention_reason
    assert "Abstained" in v_res.verified_answer


def test_matching_case_citation_passes_query_relevance() -> None:
    """Verify that citing the matching case succeeds."""
    eldeco_item = make_item(
        chunk_id=14,
        doc_id=6,
        title="Eldeco Housing and Industries Ltd v. Ashok Vidyarthi",
        date="2023-11-28",
        citation="2023 INSC 1043",
        snippet="In a suit for specific performance, Section 16(c) of the Specific Relief Act mandates continuous readiness and willingness.",
    )
    citation_map = {"[C1]": eldeco_item}

    query = (
        "What did the Supreme Court hold in Eldeco Housing and Industries Ltd v. Ashok Vidyarthi "
        "regarding readiness and willingness under Section 16(c)?"
    )
    answer = (
        "Under Section 16(c) of the Specific Relief Act, continuous readiness and willingness "
        "is mandatory in a suit for specific performance [C1]."
    )

    relevance_res = verify_query_relevance(query, citation_map)
    assert relevance_res.is_fully_relevant is True
    assert len(relevance_res.irrelevant_markers) == 0

    v_res = verify_and_filter_answer(answer, citation_map, query=query)
    assert v_res.passed is True
    assert v_res.abstained is False
    assert v_res.supported_fraction >= 0.60
    assert "readiness and willingness" in v_res.verified_answer


def test_topical_relevance_rejects_unrelated_matter() -> None:
    """A conceptual query on specific performance must reject unrelated criminal law passages."""
    bhajan_item = make_item(
        chunk_id=5,
        doc_id=5,
        title="State of Haryana v. Bhajan Lal",
        date="1992-11-21",
        citation="1992 INSC 304",
        snippet="Inherent powers under Section 482 CrPC are used to prevent abuse of the process of any court.",
    )
    citation_map = {"[C1]": bhajan_item}

    query = "What is the requirement of readiness and willingness in specific performance of contract?"
    relevance_res = verify_query_relevance(query, citation_map)
    assert relevance_res.is_fully_relevant is False
    assert "[C1]" in relevance_res.irrelevant_markers


def test_regression_all_india_judges_abstention_on_corpus() -> None:
    """Regression test: End-to-end query for All India Judges Association must abstain and NEVER return Sarda."""
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    session = Session(engine)

    court = Court(code="sc", name="Supreme Court of India", level="supreme")
    snapshot = DatasetSnapshot(
        source_key="sc_judgments",
        source_url="https://registry.opendata.aws/sc/",
        license="CC-BY-4.0",
        attribution="Dattam Labs",
        manifest_path="manifest.sha256",
    )
    session.add_all([court, snapshot])
    session.commit()

    run = IngestionRun(snapshot_id=snapshot.id, params={"year": 1984}, status="success")
    session.add(run)
    session.commit()

    # Index Sharad Birdhichand Sarda
    sarda_doc = Document(
        run_id=run.id,
        court_id=court.id,
        external_id="1984_sc_121",
        title="Sharad Birdhichand Sarda v. State of Maharashtra",
        neutral_citation="1984 INSC 121",
        source_file_path="1984.pdf",
        source_sha256="sarda" * 12,
        extraction_status="ok",
    )
    session.add(sarda_doc)
    session.commit()

    embedder = DeterministicHashEmbedder()
    sarda_text = (
        "Paragraph 153: The circumstantial evidence must be fully established and consistent only with guilt."
    )
    chunk = Chunk(
        document_id=sarda_doc.id,
        para_no=153,
        segment_type="reasoning",
        start_char=0,
        end_char=len(sarda_text),
        text=sarda_text,
        embedding=embedder.embed_text(sarda_text),
    )
    session.add(chunk)
    session.commit()

    orchestrator = QAOrchestrator()
    query = (
        "Search the Indian Supreme Court corpus for the 2023 judgment in All India Judges Association v. Union of India. "
        "Explain the main legal issue, the Court's reasoning, and its final decision using only retrieved passages."
    )

    resp = orchestrator.ask(db=session, question=query)

    assert resp.abstained is True
    assert "not present in the indexed Supreme Court corpus" in resp.answer
    assert "All India Judges Association v. Union of India" in resp.answer
    # Must never mention circumstantial evidence or Sharad Birdhichand Sarda
    assert "Sharad Birdhichand Sarda" not in resp.answer
    assert "circumstantial evidence" not in resp.answer.lower()
    assert "1984 INSC 121" not in resp.answer
    assert len(resp.citations) == 0

    session.close()
