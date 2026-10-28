"""Unified hybrid search orchestrator combining lexical, dense, RRF, and reranking (Task T-08 / FR-04)."""

from sqlalchemy.orm import Session

from app.retrieval.dense import search_dense
from app.retrieval.fusion import reciprocal_rank_fusion
from app.retrieval.lexical import SearchResultItem, search_lexical_db
from app.retrieval.rerank import get_reranker


def search_hybrid(
    db: Session,
    query: str,
    court_codes: list[str] | None = None,
    year_from: int | None = None,
    year_to: int | None = None,
    user_id: int | None = None,
    k_lex: int = 50,
    k_dense: int = 50,
    rrf_constant: int = 60,
    rerank: bool = True,
    limit: int = 20,
    offset: int = 0,
) -> list[SearchResultItem]:
    """Execute hybrid search pipeline:
    1. Lexical retrieval (Postgres FTS / BM25Plus).
    2. Dense vector similarity (BGE-M3 embeddings).
    3. Reciprocal Rank Fusion (RRF, constant k=60).
    4. Cross-encoder reranking over top candidates.
    """
    # 1. Lexical search branch
    lexical_hits = search_lexical_db(
        db=db,
        query=query,
        court_codes=court_codes,
        year_from=year_from,
        year_to=year_to,
        user_id=user_id,
        limit=k_lex,
    )

    # 2. Dense vector search branch
    dense_hits = search_dense(
        db=db,
        query=query,
        court_codes=court_codes,
        year_from=year_from,
        year_to=year_to,
        user_id=user_id,
        limit=k_dense,
    )

    # If only one modality returned hits, fallback cleanly
    if not dense_hits:
        fused = lexical_hits
    elif not lexical_hits:
        fused = dense_hits
    else:
        # 3. Reciprocal Rank Fusion
        fused = reciprocal_rank_fusion(
            ranked_lists=[lexical_hits, dense_hits],
            k=rrf_constant,
            limit=max(k_lex, k_dense),
        )

    # 4. Optional cross-encoder reranking
    if rerank and fused:
        reranker = get_reranker()
        reranked = reranker.rerank(query=query, items=fused, top_k=limit + offset)
        return reranked[offset : offset + limit]

    return fused[offset : offset + limit]
