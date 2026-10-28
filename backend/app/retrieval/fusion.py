"""Reciprocal Rank Fusion (RRF) for hybrid retrieval (Task T-08 / FR-04)."""

from typing import TypeVar

from app.retrieval.lexical import SearchResultItem

T = TypeVar("T", bound=SearchResultItem)


def reciprocal_rank_fusion(
    ranked_lists: list[list[SearchResultItem]],
    k: int = 60,
    limit: int = 50,
) -> list[SearchResultItem]:
    """Combine multiple ranked result lists using Reciprocal Rank Fusion (RRF).

    Formula:
        RRF_score(d) = sum_{m in M} 1 / (k + rank_m(d))
    where:
        - k is the smoothing constant (default: 60, per Cormack et al. 2009 and PRD)
        - rank_m(d) is the 1-based rank position of document d in ranking list m.

    Items appearing in multiple candidate lists accumulate reciprocal rank contributions
    and naturally rank higher than items appearing in only a single modality.
    """
    scores: dict[int, float] = {}
    item_map: dict[int, SearchResultItem] = {}

    for ranked_list in ranked_lists:
        for rank_idx, item in enumerate(ranked_list, start=1):
            chunk_id = item.chunk_id
            rrf_contrib = 1.0 / (k + rank_idx)
            scores[chunk_id] = scores.get(chunk_id, 0.0) + rrf_contrib

            # Store best metadata representation
            if chunk_id not in item_map:
                item_map[chunk_id] = item

    # Sort candidates descending by accumulated RRF score
    sorted_chunk_ids = sorted(scores.keys(), key=lambda cid: scores[cid], reverse=True)
    fused_results: list[SearchResultItem] = []

    for cid in sorted_chunk_ids[:limit]:
        original_item = item_map[cid]
        fused_item = SearchResultItem(
            chunk_id=original_item.chunk_id,
            document_id=original_item.document_id,
            title=original_item.title,
            court=original_item.court,
            decision_date=original_item.decision_date,
            neutral_citation=original_item.neutral_citation,
            para_no=original_item.para_no,
            segment_type=original_item.segment_type,
            snippet=original_item.snippet,
            score=round(scores[cid], 6),
            attribution=original_item.attribution,
        )
        fused_results.append(fused_item)

    return fused_results
