"""Cross-encoder reranking interface and implementations (Task T-08 / FR-04)."""

import logging
import re
from abc import ABC, abstractmethod
from typing import Any

from app.core.config import settings
from app.retrieval.lexical import SearchResultItem

logger = logging.getLogger(__name__)


class BaseReranker(ABC):
    """Abstract interface for passage reranking."""

    @abstractmethod
    def rerank(
        self,
        query: str,
        items: list[SearchResultItem],
        top_k: int = 20,
    ) -> list[SearchResultItem]:
        """Rerank a list of search result items against the query."""
        pass


class LexicalBoostReranker(BaseReranker):
    """Rule-based reranker combining base score with query phrase and token density.

    Used for fast deterministic testing and CPU fallback when neural reranker weights
    are unavailable.
    """

    def rerank(
        self,
        query: str,
        items: list[SearchResultItem],
        top_k: int = 20,
    ) -> list[SearchResultItem]:
        if not items:
            return []

        q_lower = query.lower()
        q_tokens = [t for t in re.findall(r"\w+", q_lower) if len(t) > 2]

        scored: list[tuple[float, SearchResultItem]] = []
        for item in items:
            text = (item.title + " " + item.snippet).lower()
            token_matches = sum(1 for t in q_tokens if t in text)
            exact_match_bonus = 1.0 if q_lower in text else 0.0

            # Combined score: normalized base score + lexical boosts
            boosted_score = (
                item.score * 0.5
                + (token_matches / max(1, len(q_tokens))) * 0.3
                + exact_match_bonus * 0.2
            )

            reranked_item = SearchResultItem(
                chunk_id=item.chunk_id,
                document_id=item.document_id,
                title=item.title,
                court=item.court,
                decision_date=item.decision_date,
                neutral_citation=item.neutral_citation,
                para_no=item.para_no,
                segment_type=item.segment_type,
                snippet=item.snippet,
                score=round(boosted_score, 4),
                attribution=item.attribution,
            )
            scored.append((boosted_score, reranked_item))

        scored.sort(key=lambda x: x[0], reverse=True)
        return [item for _, item in scored[:top_k]]


class CrossEncoderReranker(BaseReranker):
    """Neural cross-encoder reranker (e.g. BAAI/bge-reranker-base)."""

    def __init__(self, model_name: str = "BAAI/bge-reranker-base"):
        self._model_name = model_name
        self._model: Any = None

    def _load_model(self) -> Any:
        if self._model is None:
            try:
                import importlib

                st_mod = importlib.import_module("sentence_transformers")
                cross_encoder_cls = st_mod.CrossEncoder
                logger.info("Loading cross-encoder reranker: %s", self._model_name)
                self._model = cross_encoder_cls(self._model_name)
            except Exception as exc:
                logger.warning(
                    "Failed to load CrossEncoder %s (%s); falling back to LexicalBoostReranker.",
                    self._model_name,
                    exc,
                )
                self._model = LexicalBoostReranker()
        return self._model

    def rerank(
        self,
        query: str,
        items: list[SearchResultItem],
        top_k: int = 20,
    ) -> list[SearchResultItem]:
        if not items:
            return []

        model = self._load_model()
        if isinstance(model, BaseReranker):
            return model.rerank(query, items, top_k=top_k)

        pairs = [[query, item.title + ". " + item.snippet] for item in items]
        logits = model.predict(pairs)

        reranked_list: list[tuple[float, SearchResultItem]] = []
        for score, item in zip(logits, items, strict=True):
            f_score = float(score)
            reranked_item = SearchResultItem(
                chunk_id=item.chunk_id,
                document_id=item.document_id,
                title=item.title,
                court=item.court,
                decision_date=item.decision_date,
                neutral_citation=item.neutral_citation,
                para_no=item.para_no,
                segment_type=item.segment_type,
                snippet=item.snippet,
                score=round(f_score, 4),
                attribution=item.attribution,
            )
            reranked_list.append((f_score, reranked_item))

        reranked_list.sort(key=lambda x: x[0], reverse=True)
        return [item for _, item in reranked_list[:top_k]]


_CACHED_RERANKER: BaseReranker | None = None


def get_reranker(model_name: str | None = None) -> BaseReranker:
    """Factory returning configured reranker instance."""
    global _CACHED_RERANKER
    target: str = str(model_name or getattr(settings, "RERANK_MODEL", "BAAI/bge-reranker-base"))

    if _CACHED_RERANKER is not None:
        return _CACHED_RERANKER

    import importlib.util

    if importlib.util.find_spec("sentence_transformers") is not None:
        _CACHED_RERANKER = CrossEncoderReranker(model_name=target)
    else:
        logger.info("sentence_transformers not installed; using LexicalBoostReranker")
        _CACHED_RERANKER = LexicalBoostReranker()

    return _CACHED_RERANKER
