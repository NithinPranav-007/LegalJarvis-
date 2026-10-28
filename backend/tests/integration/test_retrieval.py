"""Integration tests for embeddings, dense retrieval, RRF, and hybrid search (Task T-08 / FR-04)."""

import math

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.db.models import Base, Chunk, Court, DatasetSnapshot, Document, IngestionRun
from app.ingest.embed import (
    DEFAULT_DIMENSION,
    DeterministicHashEmbedder,
    embed_unindexed_chunks,
)
from app.retrieval.dense import search_dense
from app.retrieval.fusion import reciprocal_rank_fusion
from app.retrieval.hybrid import search_hybrid
from app.retrieval.lexical import SearchResultItem, search_lexical_db
from app.retrieval.rerank import LexicalBoostReranker


@pytest.fixture
def retrieval_db() -> Session:
    """In-memory database with populated test judgments, chunks, and embeddings."""
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
        source_sha256="a" * 64,
        extraction_status="ok",
    )
    doc2 = Document(
        run_id=run.id,
        court_id=court.id,
        external_id="2023_7_322_346",
        title="Central GST Delhi v. Delhi International Airport Ltd",
        neutral_citation="2023 INSC 540",
        source_file_path="data/raw/sc/year=2023/2023_7_322_346_EN.pdf",
        source_sha256="b" * 64,
        extraction_status="ok",
    )
    session.add_all([doc1, doc2])
    session.commit()

    embedder = DeterministicHashEmbedder(dimension=DEFAULT_DIMENSION)

    chunk1_text = (
        "A suit for specific performance was filed seeking enforcement of the agreement for sale."
    )
    chunk2_text = "The levy of service tax on user development fee collected under the Airports Authority Act."
    chunk3_text = (
        "Specific relief cannot be granted if damages provide adequate relief under the contract."
    )

    chunk1 = Chunk(
        document_id=doc1.id,
        para_no=1,
        segment_type="facts",
        start_char=0,
        end_char=len(chunk1_text),
        text=chunk1_text,
        embedding=embedder.embed_text(chunk1_text),
    )
    chunk2 = Chunk(
        document_id=doc2.id,
        para_no=5,
        segment_type="reasoning",
        start_char=0,
        end_char=len(chunk2_text),
        text=chunk2_text,
        embedding=embedder.embed_text(chunk2_text),
    )
    chunk3 = Chunk(
        document_id=doc1.id,
        para_no=12,
        segment_type="holding",
        start_char=0,
        end_char=len(chunk3_text),
        text=chunk3_text,
        embedding=None,  # Intentionally unembedded for batch test
    )

    session.add_all([chunk1, chunk2, chunk3])
    session.commit()

    yield session
    session.close()


def test_embedder_dimension_and_normalization() -> None:
    embedder = DeterministicHashEmbedder(dimension=DEFAULT_DIMENSION)
    assert embedder.dimension == 1024

    vec = embedder.embed_text("Specific Relief Act Section 10 enforcement")
    assert len(vec) == 1024
    assert all(isinstance(v, float) for v in vec)

    # Check unit norm (sum of squares == 1.0 within tolerance)
    norm = math.sqrt(sum(v * v for v in vec))
    assert math.isclose(norm, 1.0, rel_tol=1e-3)


def test_batch_embedding_persistence(retrieval_db: Session) -> None:
    embedder = DeterministicHashEmbedder(dimension=DEFAULT_DIMENSION)
    count = embed_unindexed_chunks(retrieval_db, batch_size=10, embedder=embedder)
    assert count == 1  # chunk3 was unembedded

    # Verify chunk3 now has embedding
    chunk3 = retrieval_db.query(Chunk).filter_by(para_no=12).one()
    assert chunk3.embedding is not None
    assert len(chunk3.embedding) == 1024


def test_dense_retrieval(retrieval_db: Session) -> None:
    embedder = DeterministicHashEmbedder(dimension=DEFAULT_DIMENSION)
    results = search_dense(
        db=retrieval_db,
        query="specific performance enforcement of agreement",
        limit=5,
        embedder=embedder,
    )
    assert len(results) >= 1
    top_hit = results[0]
    assert "Eldeco Housing" in top_hit.title
    assert top_hit.para_no == 1
    assert top_hit.score > 0.0
    assert "Dattam Labs" in top_hit.attribution


def test_reciprocal_rank_fusion_math() -> None:
    item_a = SearchResultItem(
        chunk_id=101,
        document_id=1,
        title="Doc A",
        court="Supreme Court",
        decision_date="2023-01-01",
        neutral_citation="2023 INSC 1",
        para_no=1,
        segment_type="facts",
        snippet="Text A",
        score=1.0,
    )
    item_b = SearchResultItem(
        chunk_id=102,
        document_id=2,
        title="Doc B",
        court="Supreme Court",
        decision_date="2023-01-01",
        neutral_citation="2023 INSC 2",
        para_no=2,
        segment_type="reasoning",
        snippet="Text B",
        score=0.9,
    )

    # List 1: [A (rank 1), B (rank 2)]
    # List 2: [A (rank 1)]
    fused = reciprocal_rank_fusion(
        ranked_lists=[[item_a, item_b], [item_a]],
        k=60,
    )
    assert len(fused) == 2
    # Item A is rank 1 in both: 1/(60+1) + 1/(60+1) = 2/61 ~ 0.032787
    # Item B is rank 2 in list 1 only: 1/(60+2) = 1/62 ~ 0.016129
    assert fused[0].chunk_id == 101
    assert math.isclose(fused[0].score, 2 / 61, rel_tol=1e-4)
    assert fused[1].chunk_id == 102
    assert math.isclose(fused[1].score, 1 / 62, rel_tol=1e-4)


def test_reranker_execution() -> None:
    reranker = LexicalBoostReranker()
    item1 = SearchResultItem(
        chunk_id=1,
        document_id=1,
        title="Income Tax Assessment",
        court="Supreme Court",
        decision_date=None,
        neutral_citation=None,
        para_no=1,
        segment_type=None,
        snippet="Assessment of capital gains under section 45.",
        score=0.1,
    )
    item2 = SearchResultItem(
        chunk_id=2,
        document_id=2,
        title="Specific Relief Suit",
        court="Supreme Court",
        decision_date=None,
        neutral_citation=None,
        para_no=2,
        segment_type=None,
        snippet="Enforcement of contract for specific performance.",
        score=0.05,
    )

    reranked = reranker.rerank(
        query="contract specific performance",
        items=[item1, item2],
        top_k=2,
    )
    assert len(reranked) == 2
    # Item 2 has high query token overlap so should be promoted
    assert reranked[0].chunk_id == 2


def test_hybrid_search_end_to_end(retrieval_db: Session) -> None:
    # Ensure all chunks are embedded
    embed_unindexed_chunks(retrieval_db)

    # 1. Lexical search
    lex_hits = search_lexical_db(retrieval_db, query="service tax user development fee")
    assert len(lex_hits) >= 1
    assert "Central GST" in lex_hits[0].title

    # 2. Dense search
    dense_hits = search_dense(retrieval_db, query="service tax user development fee")
    assert len(dense_hits) >= 1
    assert "Central GST" in dense_hits[0].title

    # 3. Hybrid search (lexical + dense + RRF + rerank)
    hybrid_hits = search_hybrid(
        retrieval_db,
        query="service tax user development fee",
        rerank=True,
        limit=5,
    )
    assert len(hybrid_hits) >= 1
    assert "Central GST" in hybrid_hits[0].title
    assert hybrid_hits[0].score > 0.0
