"""Build and load local retrieval indexes from the canonical chunk JSONL."""

from __future__ import annotations

import json
from pathlib import Path

from app.core.config import Settings
from .bm25 import BM25Index
from .dense import DenseIndex
from .embeddings import HashEmbedder, SentenceTransformerEmbedder
from .reranker import CrossEncoderReranker
from .service import HybridRetriever, load_chunks
from .vector_store import load_dense_index, save_dense_index


def build_indexes(
    chunks_path: Path,
    index_dir: Path,
    settings: Settings,
    *,
    allow_hash_fallback: bool = False,
) -> dict[str, object]:
    chunks = load_chunks(chunks_path)
    if not chunks:
        raise ValueError("Cannot build indexes from an empty chunk set")
    try:
        embedder = SentenceTransformerEmbedder(settings.embedding_model)
        embedding_backend = settings.embedding_model
    except (ImportError, OSError, RuntimeError):
        if not allow_hash_fallback:
            raise RuntimeError(
                "Configured embedding model is unavailable; pass allow_hash_fallback only for local tests"
            )
        embedder = HashEmbedder()
        embedding_backend = "hash-fallback-test-only"
    dense_index = DenseIndex(chunks, embedder)
    index_dir.mkdir(parents=True, exist_ok=True)
    vector_path = index_dir / "vector.json"
    save_dense_index(dense_index, vector_path)
    lexical_path = index_dir / "bm25.json"
    lexical_path.write_text(
        json.dumps({"chunks_path": str(chunks_path.resolve()), "count": len(chunks)}),
        encoding="utf-8",
    )
    return {
        "chunk_count": len(chunks),
        "embedding_backend": embedding_backend,
        "vector_index": str(vector_path),
        "bm25_index": str(lexical_path),
    }


def load_retriever(settings: Settings, *, allow_hash_fallback: bool = False) -> HybridRetriever:
    chunks_path = settings.processed_dir / "chunks" / "all_chunks.jsonl"
    if not chunks_path.exists():
        raise FileNotFoundError(f"Chunk index is unavailable: {chunks_path}")
    chunks = load_chunks(chunks_path)
    if not chunks:
        raise ValueError("Chunk index is empty")
    try:
        embedder = SentenceTransformerEmbedder(settings.embedding_model)
    except (ImportError, OSError, RuntimeError):
        if not allow_hash_fallback:
            raise RuntimeError("Configured embedding model is unavailable")
        embedder = HashEmbedder()
    reranker = CrossEncoderReranker(settings.reranker_model)
    vector_path = settings.processed_dir / "index" / "vector.json"
    dense_index = None
    if vector_path.exists():
        try:
            dense_index = load_dense_index(vector_path, embedder)
        except (KeyError, TypeError, ValueError, json.JSONDecodeError):
            dense_index = None
    return HybridRetriever(chunks, embedder, reranker, dense_index=dense_index)
