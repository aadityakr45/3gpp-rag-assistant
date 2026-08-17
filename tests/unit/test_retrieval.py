from app.models.domain import Chunk
from app.retrieval.bm25 import BM25Index
from app.retrieval.dense import DenseIndex
from app.retrieval.embeddings import HashEmbedder
from app.retrieval.hybrid import reciprocal_rank_fusion


def _chunk(identifier: str, text: str) -> Chunk:
    return Chunk(
        chunk_id=identifier,
        specification="TS 23.501",
        specification_title="5GS architecture",
        release="18",
        version="18.0.0",
        clause="5.3.2",
        section_title="Registration",
        page_start=1,
        page_end=1,
        source_document="test.pdf",
        source_type="3GPP_TS",
        text=text,
        content_hash=identifier,
        document_checksum="checksum",
    )


def test_bm25_prefers_exact_telecom_terms() -> None:
    chunks = (
        _chunk("amf", "The AMF handles registration management."),
        _chunk("upf", "The UPF handles user plane forwarding."),
    )
    hits = BM25Index(chunks).search("AMF registration", top_k=1)
    assert hits[0].chunk.chunk_id == "amf"


def test_dense_and_rrf_return_stable_results() -> None:
    chunks = (
        _chunk("amf", "The AMF handles registration management."),
        _chunk("upf", "The UPF handles user plane forwarding."),
    )
    dense = DenseIndex(chunks, HashEmbedder(64)).search("AMF registration", top_k=2)
    lexical = BM25Index(chunks).search("AMF registration", top_k=2)
    fused = reciprocal_rank_fusion(dense, lexical, top_k=2)
    assert len(fused) == 2
    assert fused[0].chunk.chunk_id == "amf"
