"""JSON persistence for the dependency-light dense index."""

from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path

from app.models.domain import Chunk
from .dense import DenseIndex
from .embeddings import Embedder


def save_dense_index(index: DenseIndex, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "dimension": index.embedder.dimension,
        "chunks": [asdict(chunk) for chunk in index.chunks],
        "vectors": index.vectors,
    }
    path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")


def load_dense_index(path: Path, embedder: Embedder) -> DenseIndex:
    payload = json.loads(path.read_text(encoding="utf-8"))
    chunks = tuple(Chunk(**row) for row in payload["chunks"])
    index = DenseIndex.__new__(DenseIndex)
    index.chunks = chunks
    index.embedder = embedder
    index.vectors = payload["vectors"]
    return index
