"""Small deterministic BM25 implementation for exact telecom terminology."""

from __future__ import annotations

import math
import re
from collections import Counter
from dataclasses import dataclass
from typing import Iterable

from app.models.domain import Chunk
from .types import RetrievalHit


TOKEN_RE = re.compile(r"[A-Za-z0-9]+(?:[._-][A-Za-z0-9]+)*")


def tokenize(text: str) -> list[str]:
    return [token.lower() for token in TOKEN_RE.findall(text)]


@dataclass(frozen=True)
class MetadataFilter:
    specification: str | None = None
    release: str | None = None
    version: str | None = None

    def matches(self, chunk: Chunk) -> bool:
        return all(
            expected is None or actual == expected
            for expected, actual in (
                (self.specification, chunk.specification),
                (self.release, chunk.release),
                (self.version, chunk.version),
            )
        )


class BM25Index:
    def __init__(self, chunks: Iterable[Chunk], k1: float = 1.5, b: float = 0.75) -> None:
        self.chunks = tuple(chunks)
        self.k1 = k1
        self.b = b
        self._tokens = [tokenize(chunk.text) for chunk in self.chunks]
        self._frequencies = [Counter(tokens) for tokens in self._tokens]
        self._document_frequency: Counter[str] = Counter()
        for frequencies in self._frequencies:
            self._document_frequency.update(frequencies.keys())
        self._average_length = (
            sum(len(tokens) for tokens in self._tokens) / len(self._tokens)
            if self._tokens
            else 0.0
        )

    def search(
        self,
        query: str,
        top_k: int = 20,
        metadata_filter: MetadataFilter | None = None,
    ) -> tuple[RetrievalHit, ...]:
        if top_k < 1:
            return ()
        query_tokens = tokenize(query)
        if not query_tokens or not self.chunks:
            return ()
        scores: list[tuple[float, Chunk]] = []
        total_docs = len(self.chunks)
        for chunk, frequencies, tokens in zip(self.chunks, self._frequencies, self._tokens):
            if metadata_filter and not metadata_filter.matches(chunk):
                continue
            length = len(tokens)
            score = 0.0
            for term in query_tokens:
                frequency = frequencies.get(term, 0)
                if not frequency:
                    continue
                df = self._document_frequency.get(term, 0)
                idf = math.log(1 + (total_docs - df + 0.5) / (df + 0.5))
                denominator = frequency + self.k1 * (
                    1 - self.b + self.b * length / (self._average_length or 1.0)
                )
                score += idf * frequency * (self.k1 + 1) / denominator
            scores.append((score, chunk))
        scores.sort(key=lambda item: (-item[0], item[1].chunk_id))
        return tuple(
            RetrievalHit(chunk=chunk, score=score, rank=rank, bm25_score=score)
            for rank, (score, chunk) in enumerate(scores[:top_k], start=1)
        )
