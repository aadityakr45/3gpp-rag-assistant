"""Structure-aware chunking that keeps clause and page provenance."""

from __future__ import annotations

import hashlib
import re

from app.models.domain import Chunk, Section


def _slug(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9]+", "-", value).strip("-") or "front"


def _word_count(text: str) -> int:
    return len(text.split())


def _split_oversized(text: str, target_words: int) -> list[str]:
    sentences = re.split(r"(?<=[.!?])\s+", text.strip())
    pieces: list[str] = []
    current: list[str] = []
    for sentence in sentences:
        if not sentence:
            continue
        if current and _word_count(" ".join(current + [sentence])) > target_words:
            pieces.append(" ".join(current).strip())
            current = []
        if _word_count(sentence) > target_words:
            words = sentence.split()
            for start in range(0, len(words), target_words):
                pieces.append(" ".join(words[start : start + target_words]))
        else:
            current.append(sentence)
    if current:
        pieces.append(" ".join(current).strip())
    return [piece for piece in pieces if piece]


def chunk_sections(
    sections: tuple[Section, ...],
    *,
    specification: str | None,
    specification_title: str | None,
    release: str | None,
    version: str | None,
    source_document: str,
    source_type: str | None,
    document_checksum: str,
    target_words: int = 450,
) -> tuple[Chunk, ...]:
    """Build chunks at paragraph/section boundaries before splitting sentences."""

    required = {
        "specification": specification,
        "specification_title": specification_title,
        "release": release,
        "version": version,
    }
    missing = [name for name, value in required.items() if not value]
    if missing:
        raise ValueError(f"Cannot create provenance-safe chunks; missing {', '.join(missing)}")

    kind = source_type or ("3GPP_TS" if specification.startswith("TS ") else "3GPP_TR")
    if kind in {"TS", "TR"}:
        kind = f"3GPP_{kind}"
    chunks: list[Chunk] = []
    ordinal = 1
    for section in sections:
        paragraphs: list[str] = []
        for block in section.text_blocks:
            paragraphs.extend(_split_oversized(block, target_words))
        current: list[str] = []
        for paragraph in paragraphs:
            proposed = "\n\n".join(current + [paragraph])
            if current and _word_count(proposed) > target_words:
                chunks.append(
                    _make_chunk(
                        section,
                        "\n\n".join(current),
                        ordinal,
                        specification=specification,
                        specification_title=specification_title,
                        release=release,
                        version=version,
                        source_document=source_document,
                        source_type=kind,
                        document_checksum=document_checksum,
                    )
                )
                ordinal += 1
                current = []
            current.append(paragraph)
        if current:
            chunks.append(
                _make_chunk(
                    section,
                    "\n\n".join(current),
                    ordinal,
                    specification=specification,
                    specification_title=specification_title,
                    release=release,
                    version=version,
                    source_document=source_document,
                    source_type=kind,
                    document_checksum=document_checksum,
                )
            )
            ordinal += 1
    return tuple(chunks)


def _make_chunk(
    section: Section,
    text: str,
    ordinal: int,
    *,
    specification: str,
    specification_title: str,
    release: str,
    version: str,
    source_document: str,
    source_type: str,
    document_checksum: str,
) -> Chunk:
    content_hash = hashlib.sha256(text.encode("utf-8")).hexdigest()
    clause = section.clause or "front"
    chunk_id = (
        f"{_slug(specification)}-r{_slug(release)}-v{_slug(version)}-"
        f"c{_slug(clause)}-{ordinal:04d}"
    )
    return Chunk(
        chunk_id=chunk_id,
        specification=specification,
        specification_title=specification_title,
        release=release,
        version=version,
        clause=section.clause,
        section_title=section.title,
        page_start=section.page_start,
        page_end=section.page_end,
        source_document=source_document,
        source_type=source_type,
        text=text,
        content_hash=content_hash,
        document_checksum=document_checksum,
        parent_clause=section.parent_clause,
        subsection=section.title if section.level > 1 else None,
        metadata={"parser_version": "pymupdf-blocks-v1"},
    )
