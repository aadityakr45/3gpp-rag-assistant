"""Input and trust-boundary helpers."""

from __future__ import annotations

import re


class InvalidRequest(ValueError):
    """Raised when a user-controlled request is invalid."""


def validate_question(question: str, max_length: int = 2000) -> str:
    if not isinstance(question, str):
        raise InvalidRequest("question must be a string")
    normalized = " ".join(question.split())
    if not normalized:
        raise InvalidRequest("question must not be empty")
    if len(normalized) > max_length:
        raise InvalidRequest(f"question exceeds the {max_length}-character limit")
    return normalized


def sanitize_identifier(value: str) -> str:
    """Make a stable filesystem/index identifier from trusted metadata."""

    cleaned = re.sub(r"[^A-Za-z0-9._-]+", "-", value).strip("-.")
    if not cleaned:
        raise InvalidRequest("identifier is empty after sanitization")
    return cleaned[:160]
