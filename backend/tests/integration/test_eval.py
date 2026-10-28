"""Integration tests for retrieval evaluation harness and metrics (Task T-09 / FR-16)."""

import math

from app.eval.datasets import load_benchmark_dataset
from app.eval.metrics import (
    mean_metric,
    ndcg_at_k,
    precision_at_k,
    recall_at_k,
    reciprocal_rank,
)
from app.eval.runner import run_retrieval_benchmark


def test_ir_metrics_calculations() -> None:
    # Relevant: {2, 5}
    # Retrieved: [1, 2, 3, 4, 5, 6, 7]
    retrieved = [1, 2, 3, 4, 5, 6, 7]
    relevant = {2, 5}

    # Recall@K
    assert recall_at_k(retrieved, relevant, 1) == 0.0  # [1] -> 0 hits
    assert recall_at_k(retrieved, relevant, 2) == 0.5  # [1, 2] -> 1/2
    assert recall_at_k(retrieved, relevant, 5) == 1.0  # [1, 2, 3, 4, 5] -> 2/2

    # Precision@K
    assert precision_at_k(retrieved, relevant, 2) == 0.5  # 1 hit / 2 items = 0.5
    assert precision_at_k(retrieved, relevant, 5) == 0.4  # 2 hits / 5 items = 0.4

    # Reciprocal Rank: first hit is at rank 2 -> 1/2 = 0.5
    assert reciprocal_rank(retrieved, relevant, 10) == 0.5
    assert reciprocal_rank([9, 8, 7], relevant, 10) == 0.0

    # nDCG@K:
    # Rank 2: rel=1 -> 1 / log2(2+1) = 1 / log2(3) = 0.6309
    # Rank 5: rel=1 -> 1 / log2(5+1) = 1 / log2(6) = 0.3869
    # DCG = 0.6309 + 0.3869 = 1.0178
    # IDCG (2 items at ranks 1 and 2): 1/log2(2) + 1/log2(3) = 1 + 0.6309 = 1.6309
    # nDCG = 1.0178 / 1.6309 ~ 0.624
    score_ndcg = ndcg_at_k(retrieved, relevant, 5)
    assert 0.60 <= score_ndcg <= 0.65

    # Mean metric
    assert mean_metric([0.5, 0.75, 1.0]) == 0.75


def test_benchmark_dataset_loader() -> None:
    ds = load_benchmark_dataset()
    assert ds.name == "LJ-Retrieval-Benchmark"
    assert len(ds.queries) >= 10
    assert len(ds.corpus) >= 20

    # Check query attributes
    q1 = ds.queries[0]
    assert q1.query_id == "Q-01"
    assert len(q1.relevant_chunk_ids) >= 1

    # Check dictionary serialization
    d = ds.to_dict()
    assert d["num_queries"] == len(ds.queries)
    assert d["num_corpus_items"] == len(ds.corpus)


def test_retrieval_benchmark_reproducibility() -> None:
    # Run 1
    run1 = run_retrieval_benchmark()
    summary1 = run1["summary"]

    # Run 2
    run2 = run_retrieval_benchmark()
    summary2 = run2["summary"]

    # Assert exact reproducibility (identical metrics under seed)
    for method in ["BM25", "Dense", "Hybrid_RRF", "Hybrid_RRF_Rerank"]:
        assert method in summary1
        assert method in summary2
        for metric in ["Recall@5", "Recall@10", "Recall@20", "MRR@10", "nDCG@10"]:
            assert math.isclose(summary1[method][metric], summary2[method][metric], abs_tol=1e-5), (
                f"Mismatch in {method} {metric}: {summary1[method][metric]} != {summary2[method][metric]}"
            )
