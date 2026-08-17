"""Cross-encoder reranking with a transparent lexical fallback."""

from __future__ import annotations

from typing import Iterable

from .bm25 import tokenize
from .types import RetrievalHit


class CrossEncoderReranker:
    def __init__(self, model_name: str | None = None) -> None:
        self.model_name = model_name
        self._model = None
        if model_name:
            try:
                from sentence_transformers import CrossEncoder  # type: ignore[import-not-found]

                self._model = CrossEncoder(model_name)
            except (ImportError, OSError):
                # Retrieval remains usable locally; observability can report the fallback.
                self._model = None

    @property
    def mode(self) -> str:
        return "cross-encoder" if self._model is not None else "lexical-fallback"

    def rerank(self, query: str, hits: Iterable[RetrievalHit], top_k: int = 5) -> tuple[RetrievalHit, ...]:
        candidates = list(hits)
        if not candidates:
            return ()
        if self._model is not None:
            scores = self._model.predict([(query, hit.chunk.text) for hit in candidates])
            ranked = sorted(
                zip(candidates, (float(score) for score in scores)),
                key=lambda item: (-item[1], item[0].chunk.chunk_id),
            )
        else:
            query_terms = set(tokenize(query))
            ranked = []
            for hit in candidates:
                terms = set(tokenize(hit.chunk.text))
                overlap = len(query_terms & terms) / max(len(query_terms), 1)
                ranked.append((hit, overlap))
            ranked.sort(key=lambda item: (-item[1], item[0].chunk.chunk_id))
        return tuple(
            RetrievalHit(
                chunk=hit.chunk,
                score=score,
                rank=rank,
                dense_score=hit.dense_score,
                bm25_score=hit.bm25_score,
                rrf_score=hit.rrf_score,
                reranker_score=score,
            )
            for rank, (hit, score) in enumerate(ranked[:top_k], start=1)
        )
