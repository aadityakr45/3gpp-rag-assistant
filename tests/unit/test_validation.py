import pytest

from app.generation.citations import assign_source_ids, validate_citations
from app.generation.grounding import validate_grounding
from app.models.domain import Chunk
from app.retrieval.types import RetrievalHit


def _hit(text: str) -> RetrievalHit:
    chunk = Chunk(
        chunk_id="chunk-1",
        specification="TS 23.501",
        specification_title="5GS architecture",
        release="18",
        version="18.0.0",
        clause="5.3.2",
        section_title="Registration",
        page_start=10,
        page_end=10,
        source_document="test.pdf",
        source_type="3GPP_TS",
        text=text,
        content_hash="hash",
        document_checksum="checksum",
    )
    return RetrievalHit(chunk, 0.9, 1, reranker_score=0.9)


def test_nonexistent_citation_is_rejected() -> None:
    sources = assign_source_ids([_hit("The AMF handles registration.")])
    with pytest.raises(ValueError):
        validate_citations(["SOURCE_99"], sources)


def test_grounding_rejects_unrelated_claim() -> None:
    sources = assign_source_ids([_hit("The AMF handles registration.")])
    result = validate_grounding("The AMF handles registration. The weather is sunny.", sources)
    assert not result.grounded
    assert result.unsupported_claims
