"""Simple persisted dense index suitable for a modest local corpus."""

from __future__ import annotations

import math
from typing import Iterable

from app.models.domain import Chunk
from .embeddings import Embedder
from .types import RetrievalHit
from .bm25 import MetadataFilter


def _cosine(left: list[float], right: list[float]) -> float:
    return sum(a * b for a, b in zip(left, right)) / (
        (math.sqrt(sum(value * value for value in left)) or 1.0)
        * (math.sqrt(sum(value * value for value in right)) or 1.0)
    )


class DenseIndex:
    def __init__(self, chunks: Iterable[Chunk], embedder: Embedder) -> None:
        self.chunks = tuple(chunks)
        self.embedder = embedder
        self.vectors = embedder.embed(chunk.text for chunk in self.chunks)

    def search(
        self,
        query: str,
        top_k: int = 20,
        metadata_filter: MetadataFilter | None = None,
    ) -> tuple[RetrievalHit, ...]:
        if not query.strip() or not self.chunks:
            return ()
        query_vector = self.embedder.embed([query])[0]
        scored = []
        for chunk, vector in zip(self.chunks, self.vectors):
            if metadata_filter and not metadata_filter.matches(chunk):
                continue
            scored.append((_cosine(query_vector, vector), chunk))
        scored.sort(key=lambda item: (-item[0], item[1].chunk_id))
        return tuple(
            RetrievalHit(chunk=chunk, score=score, rank=rank, dense_score=score)
            for rank, (score, chunk) in enumerate(scored[:top_k], start=1)
        )
