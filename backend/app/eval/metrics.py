"""Information Retrieval evaluation metrics (Task T-09 / FR-16)."""

import math
from typing import Any


def recall_at_k(retrieved_ids: list[Any], relevant_ids: set[Any], k: int) -> float:
    """Compute Recall@K: fraction of relevant documents retrieved in the top K."""
    if not relevant_ids:
        return 0.0
    top_k = retrieved_ids[:k]
    hits = sum(1 for doc_id in top_k if doc_id in relevant_ids)
    return float(hits / len(relevant_ids))


def precision_at_k(retrieved_ids: list[Any], relevant_ids: set[Any], k: int) -> float:
    """Compute Precision@K: fraction of top K retrieved documents that are relevant."""
    if k <= 0:
        return 0.0
    top_k = retrieved_ids[:k]
    hits = sum(1 for doc_id in top_k if doc_id in relevant_ids)
    return float(hits / k)


def reciprocal_rank(retrieved_ids: list[Any], relevant_ids: set[Any], k: int = 10) -> float:
    """Compute Reciprocal Rank (RR@K): reciprocal of rank of first relevant item in top K."""
    if not relevant_ids:
        return 0.0
    for idx, doc_id in enumerate(retrieved_ids[:k], start=1):
        if doc_id in relevant_ids:
            return 1.0 / idx
    return 0.0


def ndcg_at_k(retrieved_ids: list[Any], relevant_ids: set[Any], k: int = 10) -> float:
    """Compute Normalized Discounted Cumulative Gain (nDCG@K) with binary relevance."""
    if not relevant_ids or k <= 0:
        return 0.0

    top_k = retrieved_ids[:k]
    dcg = 0.0
    for idx, doc_id in enumerate(top_k, start=1):
        rel = 1.0 if doc_id in relevant_ids else 0.0
        if rel > 0:
            dcg += rel / math.log2(idx + 1)

    # Ideal DCG with binary relevance
    n_rel = min(k, len(relevant_ids))
    idcg = sum(1.0 / math.log2(i + 1) for i in range(1, n_rel + 1))

    if idcg <= 0.0:
        return 0.0
    return float(dcg / idcg)


def mean_metric(values: list[float]) -> float:
    """Compute arithmetic mean of metric values, rounded to 4 decimals."""
    if not values:
        return 0.0
    return round(float(sum(values) / len(values)), 4)
