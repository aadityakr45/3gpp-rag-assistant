"""Controlled ingestion endpoint."""

from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, HTTPException, Request

from app.ingestion.pipeline import ingest_corpus
from app.models.requests import IngestionRequest
from app.retrieval.indexing import build_indexes

router = APIRouter(prefix="/api/v1", tags=["ingestion"])


def _safe_input_path(request: Request, requested: str | None) -> Path:
    root: Path = request.app.state.settings.project_root
    configured = request.app.state.settings.corpus_input_dir
    path = (root / requested if requested and not Path(requested).is_absolute() else Path(requested)) if requested else configured
    resolved = path.resolve()
    if not resolved.is_relative_to(root):
        raise HTTPException(status_code=400, detail="input_dir must stay within the project root")
    return resolved


@router.post("/ingestion/run")
def run_ingestion(payload: IngestionRequest, request: Request) -> dict[str, object]:
    input_dir = _safe_input_path(request, payload.input_dir)
    try:
        result = ingest_corpus(
            input_dir,
            request.app.state.settings.processed_dir,
            request.app.state.settings.manifest_path,
            expected_release=payload.expected_release,
            strict_release=payload.strict_release,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail="ingestion failed") from exc
    output: dict[str, object] = {"status": "OK", **result.__dict__}
    if payload.build_indexes and result.chunk_count:
        try:
            output["indexing"] = build_indexes(
                request.app.state.settings.processed_dir / "chunks" / "all_chunks.jsonl",
                request.app.state.settings.processed_dir / "index",
                request.app.state.settings,
                allow_hash_fallback=payload.allow_hash_fallback,
            )
        except RuntimeError as exc:
            raise HTTPException(status_code=503, detail=str(exc)) from exc
    return output
