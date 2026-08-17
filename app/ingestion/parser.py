"""Page-preserving PDF text extraction.

PyMuPDF is imported lazily so metadata-only inspection and pure unit tests do
not require native PDF wheels. Production ingestion fails explicitly if it is
not installed instead of silently dropping document text.
"""

from __future__ import annotations

from pathlib import Path

from app.ingestion.metadata import parse_pdf_metadata
from app.models.domain import DocumentText, PageText, PdfMetadata


class PdfParserUnavailable(RuntimeError):
    """Raised when the configured PDF extraction dependency is unavailable."""


def extract_document(path: Path, metadata: PdfMetadata | None = None) -> DocumentText:
    metadata = metadata or parse_pdf_metadata(path)
    try:
        import pymupdf  # type: ignore[import-not-found]
    except ImportError:
        try:
            import fitz as pymupdf  # type: ignore[import-not-found]
        except ImportError as exc:  # pragma: no cover - environment-dependent
            raise PdfParserUnavailable(
                "PyMuPDF is required for text extraction; install requirements.txt"
            ) from exc

    pages: list[PageText] = []
    with pymupdf.open(str(path)) as document:
        for page_index, page in enumerate(document, start=1):
            blocks: list[str] = []
            for block in page.get_text("blocks", sort=True):
                if len(block) < 5:
                    continue
                text = " ".join(str(block[4]).split())
                if text:
                    blocks.append(text)
            pages.append(
                PageText(
                    page_number=page_index,
                    text="\n".join(blocks),
                    blocks=tuple(blocks),
                )
            )

    return DocumentText(
        metadata=metadata,
        pages=tuple(pages),
        extraction_method="pymupdf.blocks",
        parser_version="pymupdf-blocks-v1",
    )
