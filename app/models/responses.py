"""API response contracts."""

from __future__ import annotations

try:
    from pydantic import BaseModel, ConfigDict, Field
except ImportError:  # pragma: no cover
    BaseModel = object  # type: ignore[assignment,misc]


if BaseModel is not object:

    class CitationResponse(BaseModel):
        model_config = ConfigDict(extra="forbid")

        source_id: str
        specification: str
        release: str
        version: str
        clause: str | None
        page_start: int
        page_end: int
        source_document: str
        text: str | None = None


    class GroundingResponse(BaseModel):
        score: float = Field(ge=0.0, le=1.0)
        verified: bool
        unsupported_claims: list[str] = Field(default_factory=list)


    class RetrievalResponse(BaseModel):
        candidate_count: int = Field(ge=0)
        evidence_count: int = Field(ge=0)


    class ChatResponse(BaseModel):
        model_config = ConfigDict(extra="forbid")

        status: str
        answer: str
        citations: list[CitationResponse]
        grounding: GroundingResponse
        retrieval: RetrievalResponse
