"""Safe discovery of local PDF corpus files."""

from __future__ import annotations

from pathlib import Path


class CorpusPathError(ValueError):
    """Raised when a configured corpus path is invalid."""


def discover_pdfs(input_dir: Path) -> tuple[Path, ...]:
    input_dir = input_dir.resolve()
    if not input_dir.exists():
        raise CorpusPathError(f"Corpus directory does not exist: {input_dir}")
    if not input_dir.is_dir():
        raise CorpusPathError(f"Corpus path is not a directory: {input_dir}")
    pdfs = tuple(sorted(p for p in input_dir.rglob("*.pdf") if p.is_file()))
    if not pdfs:
        raise CorpusPathError(f"No PDF files found under: {input_dir}")
    return pdfs
