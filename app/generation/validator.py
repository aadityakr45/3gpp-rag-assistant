"""Validation of structured provider responses."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class GeneratedAnswer:
    status: str
    answer: str
    citations: tuple[str, ...]


def parse_generated_answer(payload: str | dict[str, Any]) -> GeneratedAnswer:
    value: Any = json.loads(payload) if isinstance(payload, str) else payload
    if not isinstance(value, dict):
        raise ValueError("Provider output must be a JSON object")
    status = value.get("status")
    answer = value.get("answer")
    citations = value.get("citations", [])
    # Some Gemini models honor the JSON schema but omit the status field when
    # the answer is clearly grounded. Infer only this narrow, safe case; source
    # IDs are still validated against the retrieved evidence downstream.
    if status is None and isinstance(answer, str) and answer.strip() and isinstance(citations, list):
        status = "ANSWERED"
    if status not in {"ANSWERED", "ABSTAINED"}:
        raise ValueError("status must be ANSWERED or ABSTAINED")
    if not isinstance(answer, str):
        raise ValueError("answer must be a string")
    if not isinstance(citations, list) or not all(isinstance(item, str) for item in citations):
        raise ValueError("citations must be a list of strings")
    return GeneratedAnswer(status, answer, tuple(citations))
