from app.ingestion.chunker import chunk_sections
from app.models.domain import Section


def test_chunking_preserves_clause_and_provenance() -> None:
    sections = (
        Section(
            clause="5.3.2",
            title="Registration Management",
            level=2,
            page_start=100,
            page_end=101,
            text_blocks=(
                "The AMF performs registration management for the UE.",
                "The procedure includes authentication and security context handling.",
            ),
            parent_clause="5.3",
        ),
    )
    chunks = chunk_sections(
        sections,
        specification="TS 23.501",
        specification_title="System architecture for the 5G System (5GS)",
        release="18",
        version="18.10.0",
        source_document="TS-23.501.pdf",
        source_type="TS",
        document_checksum="abc123",
        target_words=100,
    )
    assert len(chunks) == 1
    chunk = chunks[0]
    assert chunk.chunk_id.startswith("TS-23-501-r18-v18-10-0-c5-3-2-")
    assert chunk.clause == "5.3.2"
    assert chunk.page_start == 100
    assert chunk.page_end == 101
    assert chunk.document_checksum == "abc123"
