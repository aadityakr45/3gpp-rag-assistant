"""Corpus discovery, parsing, metadata extraction, and chunking."""

from .pipeline import IngestionResult, ingest_corpus

__all__ = ["IngestionResult", "ingest_corpus"]
