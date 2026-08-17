"""Composable hybrid retrieval service."""

from __future__ import annotations

import json
from pathlib import Path

from app.models.domain import Chunk
from .bm25 import BM25Index, MetadataFilter
from .dense import DenseIndex
from .embeddings import Embedder
from .hybrid import reciprocal_rank_fusion
from .reranker import CrossEncoderReranker
from .types import RetrievalHit


def load_chunks(path: Path) -> tuple[Chunk, ...]:
    rows = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                rows.append(Chunk(**json.loads(line)))
    return tuple(rows)


class HybridRetriever:
    def __init__(
        self,
        chunks: tuple[Chunk, ...],
        embedder: Embedder,
        reranker: CrossEncoderReranker,
        *,
        dense_index: DenseIndex | None = None,
        bm25_index: BM25Index | None = None,
    ) -> None:
        self.chunks = chunks
        self.bm25 = bm25_index or BM25Index(chunks)
        self.dense = dense_index or DenseIndex(chunks, embedder)
        self.reranker = reranker

    def search(
        self,
        query: str,
        *,
        specification: str | None = None,
        release: str | None = None,
        version: str | None = None,
        candidate_k: int = 20,
        evidence_k: int = 5,
    ) -> tuple[RetrievalHit, ...]:
        metadata_filter = MetadataFilter(specification, release, version)
        dense_hits = self.dense.search(query, candidate_k, metadata_filter)
        lexical_hits = self.bm25.search(query, candidate_k, metadata_filter)
        fused = reciprocal_rank_fusion(dense_hits, lexical_hits, top_k=candidate_k)
        return self.reranker.rerank(query, fused, evidence_k)
