"""Compatibility shim for the original scaffold typo."""

from .parser import PdfParserUnavailable, extract_document

__all__ = ["PdfParserUnavailable", "extract_document"]
