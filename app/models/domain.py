"""Dependency-light domain models used across ingestion and retrieval."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class PdfMetadata:
    source_path: str
    filename: str
    checksum: str
    pdf_version: str | None
    specification: str | None
    document_kind: str | None
    specification_title: str | None
    raw_title: str | None
    release: str | None
    version: str | None
    page_count: int | None
    creator: str | None
    producer: str | None
    creation_date: str | None
    modification_date: str | None
    keywords: tuple[str, ...] = ()
    warnings: tuple[str, ...] = ()


@dataclass(frozen=True)
class PageText:
    page_number: int
    text: str
    blocks: tuple[str, ...] = ()


@dataclass(frozen=True)
class DocumentText:
    metadata: PdfMetadata
    pages: tuple[PageText, ...]
    extraction_method: str
    parser_version: str


@dataclass(frozen=True)
class Section:
    clause: str | None
    title: str
    level: int
    page_start: int
    page_end: int
    text_blocks: tuple[str, ...]
    parent_clause: str | None = None


@dataclass(frozen=True)
class Chunk:
    chunk_id: str
    specification: str
    specification_title: str
    release: str
    version: str
    clause: str | None
    section_title: str
    page_start: int
    page_end: int
    source_document: str
    source_type: str
    text: str
    content_hash: str
    document_checksum: str
    parent_clause: str | None = None
    subsection: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
