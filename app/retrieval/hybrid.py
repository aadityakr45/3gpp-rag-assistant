"""Hybrid dense/BM25 retrieval with reciprocal-rank fusion."""

from __future__ import annotations

from collections import defaultdict
from typing import Iterable

from .types import RetrievalHit


def reciprocal_rank_fusion(
    dense_hits: Iterable[RetrievalHit],
    lexical_hits: Iterable[RetrievalHit],
    *,
    top_k: int = 20,
    constant: int = 60,
) -> tuple[RetrievalHit, ...]:
    by_chunk: dict[str, RetrievalHit] = {}
    scores: defaultdict[str, float] = defaultdict(float)
    dense_scores: dict[str, float] = {}
    lexical_scores: dict[str, float] = {}
    for hit in dense_hits:
        by_chunk[hit.chunk.chunk_id] = hit
        scores[hit.chunk.chunk_id] += 1.0 / (constant + hit.rank)
        dense_scores[hit.chunk.chunk_id] = hit.score
    for hit in lexical_hits:
        by_chunk[hit.chunk.chunk_id] = hit
        scores[hit.chunk.chunk_id] += 1.0 / (constant + hit.rank)
        lexical_scores[hit.chunk.chunk_id] = hit.score

    ranked = sorted(scores, key=lambda chunk_id: (-scores[chunk_id], chunk_id))[:top_k]
    return tuple(
        RetrievalHit(
            chunk=by_chunk[chunk_id].chunk,
            score=scores[chunk_id],
            rank=rank,
            dense_score=dense_scores.get(chunk_id),
            bm25_score=lexical_scores.get(chunk_id),
            rrf_score=scores[chunk_id],
        )
        for rank, chunk_id in enumerate(ranked, start=1)
    )
