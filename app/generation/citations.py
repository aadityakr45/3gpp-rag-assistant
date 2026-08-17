"""Deterministic source-ID assignment and citation validation."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Iterable

from app.models.domain import Chunk
from app.retrieval.types import RetrievalHit


SOURCE_ID_RE = re.compile(r"\bSOURCE_(\d{2})\b")


@dataclass(frozen=True)
class EvidenceSource:
    source_id: str
    chunk: Chunk


def assign_source_ids(hits: Iterable[RetrievalHit]) -> tuple[EvidenceSource, ...]:
    return tuple(
        EvidenceSource(source_id=f"SOURCE_{index:02d}", chunk=hit.chunk)
        for index, hit in enumerate(hits, start=1)
    )


def validate_citations(
    citations: Iterable[str], sources: Iterable[EvidenceSource]
) -> tuple[str, ...]:
    allowed = {source.source_id for source in sources}
    normalized: list[str] = []
    for citation in citations:
        if not isinstance(citation, str) or not SOURCE_ID_RE.fullmatch(citation.strip()):
            raise ValueError(f"Malformed citation: {citation!r}")
        citation = citation.strip()
        if citation not in allowed:
            raise ValueError(f"Citation does not reference retrieved evidence: {citation}")
        if citation not in normalized:
            normalized.append(citation)
    return tuple(normalized)
