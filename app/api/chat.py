"""Chat endpoint and grounded answer orchestration."""

from __future__ import annotations

import logging
from dataclasses import dataclass

from fastapi import APIRouter, Request

from app.core.security import validate_question
from app.generation.citations import EvidenceSource, assign_source_ids, validate_citations
from app.generation.evidence import assess_evidence
from app.generation.generator import AbstainingGenerator
from app.generation.grounding import validate_grounding
from app.models.domain import Chunk
from app.models.requests import ChatRequest
from app.models.responses import (
    ChatResponse,
    CitationResponse,
    GroundingResponse,
    RetrievalResponse,
)
from app.retrieval.service import HybridRetriever


ABSTENTION = "I could not find sufficient evidence in the indexed 3GPP documentation to answer this reliably."
router = APIRouter(prefix="/api/v1", tags=["chat"])
logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ChatOutcome:
    status: str
    answer: str
    sources: tuple[EvidenceSource, ...]
    grounding_score: float
    verified: bool
    unsupported_claims: tuple[str, ...]
    candidate_count: int
    evidence_count: int


class ChatService:
    def __init__(self, retriever: HybridRetriever | None = None, generator=None) -> None:
        self.retriever = retriever
        self.generator = generator or AbstainingGenerator()

    def answer(self, request: ChatRequest) -> ChatOutcome:
        question = validate_question(request.question)
        if self.retriever is None:
            return self._abstain(0, 0)
        hits = self.retriever.search(
            question,
            specification=request.specification,
            release=request.release,
        )
        decision = assess_evidence(question, hits)
        if not decision.sufficient:
            return self._abstain(len(hits), 0)
        sources = assign_source_ids(hits)
        evidence = tuple((source.source_id, source.chunk) for source in sources)
        try:
            generated = self.generator.generate(question, evidence).generated
        except Exception:
            logger.warning("Generation provider failed", extra={"error_category": "provider_error"})
            return self._abstain(len(hits), len(sources))
        if generated.status != "ANSWERED":
            return self._abstain(len(hits), len(sources))
        try:
            cited = validate_citations(generated.citations, sources)
        except ValueError:
            return self._abstain(len(hits), len(sources))
        cited_sources = tuple(source for source in sources if source.source_id in cited)
        grounding = validate_grounding(generated.answer, cited_sources)
        if not grounding.grounded:
            return ChatOutcome(
                "ABSTAINED", ABSTENTION, cited_sources, grounding.score, False,
                grounding.unsupported_claims, len(hits), len(sources)
            )
        return ChatOutcome(
            "ANSWERED", generated.answer, cited_sources, grounding.score, True,
            (), len(hits), len(sources)
        )

    @staticmethod
    def _abstain(candidate_count: int, evidence_count: int) -> ChatOutcome:
        return ChatOutcome(
            "ABSTAINED", ABSTENTION, (), 0.0, False, (), candidate_count, evidence_count
        )


@router.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest, http_request: Request) -> ChatResponse:
    outcome = http_request.app.state.chat_service.answer(request)
    citations = [
        CitationResponse(
            source_id=source.source_id,
            specification=source.chunk.specification,
            release=source.chunk.release,
            version=source.chunk.version,
            clause=source.chunk.clause,
            page_start=source.chunk.page_start,
            page_end=source.chunk.page_end,
            source_document=source.chunk.source_document,
            text=source.chunk.text,
        )
        for source in outcome.sources
    ]
    return ChatResponse(
        status=outcome.status,
        answer=outcome.answer,
        citations=citations,
        grounding=GroundingResponse(
            score=outcome.grounding_score,
            verified=outcome.verified,
            unsupported_claims=list(outcome.unsupported_claims),
        ),
        retrieval=RetrievalResponse(
            candidate_count=outcome.candidate_count,
            evidence_count=outcome.evidence_count,
        ),
    )
