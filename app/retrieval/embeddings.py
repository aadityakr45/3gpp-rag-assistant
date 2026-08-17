"""Embedding providers with a deterministic local fallback for tests."""

from __future__ import annotations

import hashlib
import math
from typing import Iterable, Protocol

from .bm25 import tokenize


class Embedder(Protocol):
    dimension: int

    def embed(self, texts: Iterable[str]) -> list[list[float]]: ...


class HashEmbedder:
    """Deterministic lexical fallback; not a replacement for semantic embeddings."""

    def __init__(self, dimension: int = 384) -> None:
        self.dimension = dimension

    def embed(self, texts: Iterable[str]) -> list[list[float]]:
        vectors: list[list[float]] = []
        for text in texts:
            vector = [0.0] * self.dimension
            for token in tokenize(text):
                digest = hashlib.blake2b(token.encode(), digest_size=8).digest()
                index = int.from_bytes(digest[:4], "big") % self.dimension
                sign = 1.0 if digest[4] & 1 else -1.0
                vector[index] += sign
            norm = math.sqrt(sum(value * value for value in vector)) or 1.0
            vectors.append([value / norm for value in vector])
        return vectors


class SentenceTransformerEmbedder:
    """Lazy sentence-transformers adapter for production dense retrieval."""

    def __init__(self, model_name: str) -> None:
        try:
            from sentence_transformers import SentenceTransformer  # type: ignore[import-not-found]
        except ImportError as exc:  # pragma: no cover
            raise RuntimeError("Install sentence-transformers for dense embeddings") from exc
        self._model = SentenceTransformer(model_name)
        self.dimension = int(self._model.get_sentence_embedding_dimension())

    def embed(self, texts: Iterable[str]) -> list[list[float]]:
        values = list(texts)
        if not values:
            return []
        encoded = self._model.encode(values, normalize_embeddings=True, show_progress_bar=False)
        return encoded.tolist()
