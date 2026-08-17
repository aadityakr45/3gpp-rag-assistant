"""Retrieval result types with score provenance."""

from __future__ import annotations

from dataclasses import dataclass

from app.models.domain import Chunk


@dataclass(frozen=True)
class RetrievalHit:
    chunk: Chunk
    score: float
    rank: int
    dense_score: float | None = None
    bm25_score: float | None = None
    rrf_score: float | None = None
    reranker_score: float | None = None
