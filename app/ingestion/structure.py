"""Clause and section detection for 3GPP page text."""

from __future__ import annotations

import re

from app.models.domain import DocumentText, Section


CLAUSE_HEADING_RE = re.compile(r"^((?:\d+\.)*\d+)(?:\s+)([^\n]{2,220})$")


def _is_heading(line: str) -> tuple[str, str] | None:
    line = " ".join(line.split()).strip()
    match = CLAUSE_HEADING_RE.match(line)
    if not match:
        return None
    clause, title = match.groups()
    if title.endswith((".", ";", ":")) and len(title.split()) > 12:
        return None
    return clause, title.strip()


def detect_sections(document: DocumentText) -> tuple[Section, ...]:
    sections: list[Section] = []
    current_clause: str | None = None
    current_title = document.metadata.specification_title or "Document front matter"
    current_level = 0
    current_start = 1
    current_end = 1
    current_blocks: list[str] = []

    def flush() -> None:
        if not current_blocks:
            return
        parent = current_clause.rsplit(".", 1)[0] if current_clause and "." in current_clause else None
        sections.append(
            Section(
                clause=current_clause,
                title=current_title,
                level=current_level,
                page_start=current_start,
                page_end=current_end,
                text_blocks=tuple(current_blocks),
                parent_clause=parent,
            )
        )

    for page in document.pages:
        for block in page.blocks or ((page.text,) if page.text else ()):
            lines = [line.strip() for line in block.splitlines() if line.strip()]
            for line in lines:
                heading = _is_heading(line)
                if heading:
                    flush()
                    current_clause, current_title = heading
                    current_level = current_clause.count(".") + 1
                    current_start = page.page_number
                    current_end = page.page_number
                    current_blocks = []
                else:
                    current_blocks.append(line)
                    current_end = page.page_number
    flush()

    if not sections:
        text = tuple(page.text for page in document.pages if page.text)
        if text:
            sections.append(
                Section(
                    clause=None,
                    title=document.metadata.specification_title or "Document",
                    level=0,
                    page_start=1,
                    page_end=len(document.pages),
                    text_blocks=text,
                )
            )
    return tuple(sections)
