"""Idempotent corpus ingestion orchestration."""

from __future__ import annotations

import json
import logging
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path

from app.ingestion.chunker import chunk_sections
from app.ingestion.loader import discover_pdfs
from app.ingestion.metadata import parse_pdf_metadata
from app.ingestion.parser import PdfParserUnavailable, extract_document
from app.ingestion.structure import detect_sections
from app.models.domain import PdfMetadata
from app.core.security import sanitize_identifier

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class IngestionResult:
    manifest_path: str
    document_count: int
    processed_count: int
    skipped_count: int
    failed_count: int
    chunk_count: int
    warnings: tuple[str, ...] = ()


def _write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True),
        encoding="utf-8",
    )


def _metadata_dict(metadata: PdfMetadata) -> dict[str, object]:
    return asdict(metadata)


def ingest_corpus(
    input_dir: Path,
    processed_dir: Path,
    manifest_path: Path,
    *,
    expected_release: str | None = "18",
    strict_release: bool = False,
) -> IngestionResult:
    """Discover, parse, structure, and chunk PDFs without duplicating outputs."""

    pdf_paths = discover_pdfs(input_dir)
    processed_dir = processed_dir.resolve()
    manifest_path = manifest_path.resolve()
    extracted_dir = processed_dir / "extracted"
    structured_dir = processed_dir / "structured"
    chunks_dir = processed_dir / "chunks"

    documents: list[dict[str, object]] = []
    all_chunks: dict[str, dict[str, object]] = {}
    warnings: list[str] = []
    processed_count = skipped_count = failed_count = 0

    for pdf_path in pdf_paths:
        try:
            metadata = parse_pdf_metadata(pdf_path)
        except Exception as exc:  # metadata failures are recorded per document
            failed_count += 1
            documents.append(
                {
                    "filename": pdf_path.name,
                    "source_path": str(pdf_path.resolve()),
                    "processing_status": "FAILED_METADATA",
                    "processing_error": str(exc),
                }
            )
            continue

        record: dict[str, object] = _metadata_dict(metadata)
        record["processing_status"] = "DISCOVERED"
        document_id = sanitize_identifier(
            f"{metadata.specification or pdf_path.stem}-{metadata.checksum[:12]}"
        )
        record["document_id"] = document_id

        if expected_release and metadata.release != expected_release:
            message = (
                f"{metadata.filename}: release {metadata.release or 'unknown'} "
                f"does not match expected release {expected_release}"
            )
            warnings.append(message)
            record.setdefault("warnings", [])
            record["warnings"] = [*metadata.warnings, message]
            if strict_release:
                record["processing_status"] = "SKIPPED_RELEASE_MISMATCH"
                skipped_count += 1
                documents.append(record)
                continue

        try:
            document = extract_document(pdf_path, metadata)
            sections = detect_sections(document)
            chunks = chunk_sections(
                sections,
                specification=metadata.specification,
                specification_title=metadata.specification_title,
                release=metadata.release,
                version=metadata.version,
                source_document=metadata.filename,
                source_type=metadata.document_kind,
                document_checksum=metadata.checksum,
            )
            stem = sanitize_identifier(document_id)
            _write_json(
                extracted_dir / f"{stem}.json",
                {
                    "metadata": _metadata_dict(metadata),
                    "extraction_method": document.extraction_method,
                    "parser_version": document.parser_version,
                    "pages": [asdict(page) for page in document.pages],
                },
            )
            _write_json(
                structured_dir / f"{stem}.json",
                {
                    "metadata": _metadata_dict(metadata),
                    "sections": [asdict(section) for section in sections],
                },
            )
            chunk_rows = [asdict(chunk) for chunk in chunks]
            _write_json(chunks_dir / f"{stem}.json", chunk_rows)
            for chunk in chunks:
                all_chunks[chunk.chunk_id] = asdict(chunk)
            record["processing_status"] = "PROCESSED"
            record["chunk_count"] = len(chunks)
            processed_count += 1
        except PdfParserUnavailable as exc:
            failed_count += 1
            record["processing_status"] = "FAILED_PARSER_DEPENDENCY"
            record["processing_error"] = str(exc)
        except Exception as exc:  # controlled per-document failure
            failed_count += 1
            record["processing_status"] = "FAILED_PROCESSING"
            record["processing_error"] = str(exc)
            logger.exception("Document processing failed", extra={"document_id": document_id})
        documents.append(record)

    combined_path = chunks_dir / "all_chunks.jsonl"
    combined_path.parent.mkdir(parents=True, exist_ok=True)
    with combined_path.open("w", encoding="utf-8", newline="\n") as handle:
        for chunk_id in sorted(all_chunks):
            handle.write(json.dumps(all_chunks[chunk_id], ensure_ascii=False, sort_keys=True))
            handle.write("\n")

    manifest = {
        "corpus_name": "TeleRAG 3GPP corpus",
        "corpus_version": "0.1",
        "source_organization": "3GPP",
        "ingestion_timestamp": datetime.now(timezone.utc).isoformat(),
        "input_directory": str(input_dir.resolve()),
        "expected_release": expected_release,
        "strict_release": strict_release,
        "documents": documents,
        "summary": {
            "discovered": len(pdf_paths),
            "processed": processed_count,
            "skipped": skipped_count,
            "failed": failed_count,
            "chunks": len(all_chunks),
        },
        "warnings": warnings,
        "indexing": {
            "status": "NOT_BUILT",
            "next_step": "Build retrieval indexes after successful ingestion",
        },
    }
    _write_json(manifest_path, manifest)
    return IngestionResult(
        manifest_path=str(manifest_path),
        document_count=len(pdf_paths),
        processed_count=processed_count,
        skipped_count=skipped_count,
        failed_count=failed_count,
        chunk_count=len(all_chunks),
        warnings=tuple(warnings),
    )
