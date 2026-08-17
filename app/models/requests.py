"""API request contracts."""

from __future__ import annotations

try:
    from pydantic import BaseModel, ConfigDict, Field, field_validator
except ImportError:  # pragma: no cover - gives a useful import-time message later
    BaseModel = object  # type: ignore[assignment,misc]

    class _MissingPydantic:
        def __init__(self, *_: object, **__: object) -> None:
            raise RuntimeError("Install project dependencies before starting the API")

    ConfigDict = Field = field_validator = _MissingPydantic  # type: ignore[assignment]


if BaseModel is not object:

    class ChatRequest(BaseModel):
        model_config = ConfigDict(extra="forbid")

        question: str = Field(min_length=1, max_length=2000)
        specification: str | None = Field(default=None, max_length=32)
        release: str | None = Field(default=None, max_length=8)

        @field_validator("question")
        @classmethod
        def normalize_question(cls, value: str) -> str:
            normalized = " ".join(value.split())
            if not normalized:
                raise ValueError("question must not be empty")
            return normalized


    class IngestionRequest(BaseModel):
        model_config = ConfigDict(extra="forbid")

        input_dir: str | None = None
        expected_release: str | None = Field(default="18", max_length=8)
        strict_release: bool = False
        build_indexes: bool = False
        allow_hash_fallback: bool = False
