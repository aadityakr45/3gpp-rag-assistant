"""Deterministic grounding checks over answer sentences and cited evidence."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Iterable

from app.generation.citations import EvidenceSource
from app.retrieval.bm25 import tokenize


STOPWORDS = {
    "a", "an", "and", "are", "as", "at", "be", "by", "for", "from",
    "in", "is", "it", "of", "on", "or", "that", "the", "this", "to",
    "was", "with", "what", "which", "how", "does", "do",
}


@dataclass(frozen=True)
class GroundingResult:
    grounded: bool
    score: float
    unsupported_claims: tuple[str, ...] = ()
    citation_errors: tuple[str, ...] = ()


def _meaningful_terms(text: str) -> set[str]:
    return {term for term in tokenize(text) if term not in STOPWORDS and len(term) > 1}


def validate_grounding(
    answer: str,
    cited_sources: Iterable[EvidenceSource],
    *,
    minimum_overlap: float = 0.15,
) -> GroundingResult:
    sources = tuple(cited_sources)
    if not answer.strip() or not sources:
        return GroundingResult(False, 0.0, (answer.strip() or "empty answer",))
    evidence_terms = _meaningful_terms(" ".join(source.chunk.text for source in sources))
    claims = [claim.strip() for claim in re.split(r"(?<=[.!?])\s+", answer) if claim.strip()]
    unsupported: list[str] = []
    overlaps: list[float] = []
    for claim in claims:
        terms = _meaningful_terms(claim)
        if not terms:
            continue
        overlap = len(terms & evidence_terms) / len(terms)
        overlaps.append(overlap)
        if overlap < minimum_overlap:
            unsupported.append(claim)
    score = sum(overlaps) / len(overlaps) if overlaps else 0.0
    return GroundingResult(not unsupported and bool(overlaps), score, tuple(unsupported))
