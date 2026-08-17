"""Evaluation dataset schema; answers and source clauses remain human-authored."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class EvaluationQuestion:
    question_id: str
    question: str
    category: str
    expected_status: str
    gold_chunk_ids: tuple[str, ...] = ()
    gold_clauses: tuple[str, ...] = ()
    notes: str | None = None


def load_questions(path: Path) -> tuple[EvaluationQuestion, ...]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    rows = payload.get("questions", payload) if isinstance(payload, dict) else payload
    return tuple(EvaluationQuestion(**row) for row in rows)
