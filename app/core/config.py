"""Environment-backed configuration.

The module deliberately uses only the standard library so ingestion metadata and
unit tests can run before optional ML/API dependencies are installed.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


def _env_int(name: str, default: int, minimum: int = 1) -> int:
    value = os.getenv(name)
    if value is None or not value.strip():
        return default
    try:
        parsed = int(value)
    except ValueError as exc:
        raise ValueError(f"{name} must be an integer") from exc
    if parsed < minimum:
        raise ValueError(f"{name} must be >= {minimum}")
    return parsed


def _env_float(name: str, default: float, minimum: float = 0.0) -> float:
    value = os.getenv(name)
    if value is None or not value.strip():
        return default
    try:
        parsed = float(value)
    except ValueError as exc:
        raise ValueError(f"{name} must be a number") from exc
    if parsed < minimum:
        raise ValueError(f"{name} must be >= {minimum}")
    return parsed


def _env_bool(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    normalized = value.strip().lower()
    if normalized in {"1", "true", "yes", "on"}:
        return True
    if normalized in {"0", "false", "no", "off"}:
        return False
    raise ValueError(f"{name} must be a boolean")


@dataclass(frozen=True)
class Settings:
    """Application settings with safe local-development defaults."""

    project_root: Path
    corpus_input_dir: Path
    processed_dir: Path
    manifest_path: Path
    llm_provider: str
    llm_api_key: str | None
    llm_model: str
    embedding_model: str
    vector_store_path: Path
    reranker_model: str
    top_k: int
    rerank_top_k: int
    evidence_threshold: float
    max_query_length: int
    max_context_chars: int
    allow_hash_fallback: bool

    @classmethod
    def from_environment(cls, project_root: Path | None = None) -> "Settings":
        root = (project_root or Path(__file__).resolve().parents[2]).resolve()
        try:
            from dotenv import load_dotenv

            load_dotenv(root / ".env", override=False)
        except ImportError:
            pass
        processed = root / os.getenv("PROCESSED_DIR", "data/processed")
        configured_api_key = os.getenv("LLM_API_KEY") or os.getenv("GEMINI_API_KEY")
        return cls(
            project_root=root,
            corpus_input_dir=root / os.getenv(
                "CORPUS_INPUT_DIR", "data/raw/3gpp/release-18"
            ),
            processed_dir=processed,
            manifest_path=root / os.getenv(
                "CORPUS_MANIFEST_PATH", "data/corpus_manifest.json"
            ),
            llm_provider=os.getenv(
                "LLM_PROVIDER", "gemini" if configured_api_key else "none"
            ),
            llm_api_key=configured_api_key,
            llm_model=os.getenv("LLM_MODEL", "gemini-2.5-flash-lite"),
            embedding_model=os.getenv(
                "EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2"
            ),
            vector_store_path=root
            / os.getenv("VECTOR_STORE_PATH", "data/processed/index/vector.npz"),
            reranker_model=os.getenv(
                "RERANKER_MODEL", "cross-encoder/ms-marco-MiniLM-L-6-v2"
            ),
            top_k=_env_int("TOP_K", 20),
            rerank_top_k=_env_int("RERANK_TOP_K", 5),
            evidence_threshold=_env_float("EVIDENCE_THRESHOLD", 0.35),
            max_query_length=_env_int("MAX_QUERY_LENGTH", 2000),
            max_context_chars=_env_int("MAX_CONTEXT_CHARS", 50000),
            allow_hash_fallback=_env_bool("ALLOW_HASH_FALLBACK", False),
        )


settings = Settings.from_environment()
