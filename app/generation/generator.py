"""Provider abstraction for grounded generation."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from app.generation.prompts import build_grounded_prompt
from app.generation.validator import GeneratedAnswer, parse_generated_answer
from app.models.domain import Chunk


class LLMProvider(Protocol):
    def complete(self, prompt: str) -> str: ...


@dataclass(frozen=True)
class GenerationResult:
    generated: GeneratedAnswer
    provider: str


class AbstainingGenerator:
    """Safe default when no external provider is configured."""

    def generate(self, question: str, evidence: tuple[tuple[str, Chunk], ...]) -> GenerationResult:
        if not evidence:
            answer = "I could not find sufficient evidence in the indexed 3GPP documentation to answer this reliably."
        else:
            answer = "Answer generation is not configured for this environment."
        return GenerationResult(GeneratedAnswer("ABSTAINED", answer, ()), "none")


class ProviderGenerator:
    def __init__(self, provider: LLMProvider, provider_name: str) -> None:
        self.provider = provider
        self.provider_name = provider_name

    def generate(self, question: str, evidence: tuple[tuple[str, Chunk], ...]) -> GenerationResult:
        evidence_text = "\n\n".join(
            f"{source_id}: {chunk.text}" for source_id, chunk in evidence
        )
        raw = self.provider.complete(build_grounded_prompt(question, evidence_text))
        return GenerationResult(parse_generated_answer(raw), self.provider_name)
