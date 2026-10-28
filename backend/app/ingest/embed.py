"""Embedding interface and batch generation (Task T-08 / FR-04)."""

import hashlib
import logging
import math
from abc import ABC, abstractmethod
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.models import Chunk

logger = logging.getLogger(__name__)

DEFAULT_DIMENSION = 1024


class BaseEmbedder(ABC):
    """Abstract base class for dense text embedding models."""

    @property
    @abstractmethod
    def dimension(self) -> int:
        """Vector output dimension."""
        pass

    @abstractmethod
    def embed_texts(self, texts: list[str], batch_size: int = 32) -> list[list[float]]:
        """Generate normalized vector embeddings for a list of texts."""
        pass

    def embed_text(self, text: str) -> list[float]:
        """Generate normalized vector embedding for a single text."""
        return self.embed_texts([text])[0]


class DeterministicHashEmbedder(BaseEmbedder):
    """Deterministic feature hashing embedder.

    Produces normalized 1024-dimensional float embeddings using token and n-gram
    hashing. Used for fast offline CI testing, air-gapped environments, and fallbacks
    without downloading large neural model weights.
    """

    def __init__(self, dimension: int = DEFAULT_DIMENSION):
        self._dim = dimension

    @property
    def dimension(self) -> int:
        return self._dim

    def embed_texts(self, texts: list[str], batch_size: int = 32) -> list[list[float]]:
        results: list[list[float]] = []
        for text in texts:
            vec = [0.0] * self._dim
            if not text:
                results.append(vec)
                continue

            # Tokenize into words and character trigrams
            words = text.lower().split()
            features: list[str] = list(words)
            for word in words:
                if len(word) >= 3:
                    for i in range(len(word) - 2):
                        features.append(word[i : i + 3])

            for feat in features:
                # Deterministic hash mapped to bucket and sign
                h = int(hashlib.sha256(feat.encode("utf-8")).hexdigest(), 16)
                idx = h % self._dim
                sign = 1.0 if ((h >> 32) % 2 == 0) else -1.0
                vec[idx] += sign

            # L2 normalise vector
            norm = math.sqrt(sum(v * v for v in vec))
            if norm > 1e-9:
                vec = [round(v / norm, 6) for v in vec]
            else:
                vec = [0.0] * self._dim

            results.append(vec)
        return results


class SentenceTransformerEmbedder(BaseEmbedder):
    """Neural dense embedding wrapper using SentenceTransformers (e.g. BAAI/bge-m3)."""

    def __init__(self, model_name: str = "BAAI/bge-m3", dimension: int = DEFAULT_DIMENSION):
        self._model_name = model_name
        self._dim = dimension
        self._model: Any = None

    @property
    def dimension(self) -> int:
        return self._dim

    def _load_model(self) -> Any:
        if self._model is None:
            try:
                from sentence_transformers import (
                    SentenceTransformer,  # type: ignore[import-not-found]
                )

                logger.info("Loading sentence transformer model: %s", self._model_name)
                self._model = SentenceTransformer(self._model_name)
            except Exception as exc:
                logger.warning(
                    "Failed to load SentenceTransformer %s (%s); falling back to hash embedder.",
                    self._model_name,
                    exc,
                )
                self._model = DeterministicHashEmbedder(dimension=self._dim)
        return self._model

    def embed_texts(self, texts: list[str], batch_size: int = 32) -> list[list[float]]:
        model = self._load_model()
        if isinstance(model, BaseEmbedder):
            return model.embed_texts(texts, batch_size=batch_size)

        # Use loaded neural model
        embeddings = model.encode(
            texts,
            batch_size=batch_size,
            normalize_embeddings=True,
            show_progress_bar=False,
        )
        return [list(map(float, vec)) for vec in embeddings]


_CACHED_EMBEDDER: BaseEmbedder | None = None


def get_embedder(model_name: str | None = None) -> BaseEmbedder:
    """Factory returning configured embedder instance."""
    global _CACHED_EMBEDDER
    target: str = str(model_name or getattr(settings, "EMBED_MODEL", "BAAI/bge-m3"))

    if _CACHED_EMBEDDER is not None:
        return _CACHED_EMBEDDER

    # Check if sentence_transformers is available
    try:
        import sentence_transformers  # noqa: F401

        _CACHED_EMBEDDER = SentenceTransformerEmbedder(model_name=target, dimension=DEFAULT_DIMENSION)
    except ImportError:
        logger.info("sentence_transformers not installed; using DeterministicHashEmbedder")
        _CACHED_EMBEDDER = DeterministicHashEmbedder(dimension=DEFAULT_DIMENSION)

    return _CACHED_EMBEDDER


def embed_unindexed_chunks(
    db: Session,
    batch_size: int = 64,
    embedder: BaseEmbedder | None = None,
) -> int:
    """Find chunks without vector embeddings, compute them, and persist to database.

    Returns the number of newly embedded chunks.
    """
    active_embedder = embedder or get_embedder()
    unembedded_stmt = select(Chunk).filter(Chunk.embedding.is_(None)).limit(batch_size)
    total_embedded = 0

    while True:
        chunks = list(db.scalars(unembedded_stmt).all())
        if not chunks:
            break

        texts = [c.text for c in chunks]
        vectors = active_embedder.embed_texts(texts, batch_size=batch_size)

        for chunk, vec in zip(chunks, vectors, strict=True):
            chunk.embedding = vec

        db.commit()
        total_embedded += len(chunks)

        if len(chunks) < batch_size:
            break

    return total_embedded
