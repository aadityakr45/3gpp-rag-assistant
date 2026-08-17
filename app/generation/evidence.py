"""Evidence sufficiency and domain gates."""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Iterable

from app.retrieval.types import RetrievalHit


TELECOM_TERMS = {
    "3gpp", "4g", "5g", "5gs", "amf", "smf", "upf", "nas", "rrc", "ngran",
    "ran", "pdu", "session", "guti", "n2", "n3", "nf", "sbi", "qos", "slice",
    "ts", "tr", "clause", "release", "registration", "handover", "cell",
}


@dataclass(frozen=True)
class EvidenceDecision:
    sufficient: bool
    score: float
    reason: str


def looks_in_domain(question: str) -> bool:
    words = {word.lower().strip(".,:;?!()") for word in question.split()}
    return bool(words & TELECOM_TERMS)


def _normalized_score(value: float | None) -> float:
    if value is None:
        return 0.0
    if 0.0 <= value <= 1.0:
        return value
    return 1.0 / (1.0 + math.exp(-value))


def assess_evidence(
    question: str,
    hits: Iterable[RetrievalHit],
    *,
    threshold: float = 0.35,
) -> EvidenceDecision:
    if not looks_in_domain(question):
        return EvidenceDecision(False, 0.0, "question appears outside the 3GPP domain")
    values = [_normalized_score(hit.reranker_score or hit.score) for hit in hits]
    if not values:
        return EvidenceDecision(False, 0.0, "no evidence was retrieved")
    score = max(values)
    if score < threshold:
        return EvidenceDecision(False, score, "retrieved evidence did not meet the relevance threshold")
    return EvidenceDecision(True, score, "evidence met the configured relevance threshold")
