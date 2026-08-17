"""Corpus manifest inspection endpoints."""

from __future__ import annotations

import json
from pathlib import Path

from fastapi import APIRouter, HTTPException, Request

router = APIRouter(prefix="/api/v1/documents", tags=["documents"])


def _manifest(request: Request) -> dict[str, object]:
    path: Path = request.app.state.settings.manifest_path
    if not path.exists():
        return {"documents": [], "summary": {"discovered": 0}}
    return json.loads(path.read_text(encoding="utf-8"))


@router.get("")
def list_documents(request: Request) -> dict[str, object]:
    manifest = _manifest(request)
    return {"documents": manifest.get("documents", []), "summary": manifest.get("summary", {})}


@router.get("/{document_id}")
def get_document(document_id: str, request: Request) -> dict[str, object]:
    manifest = _manifest(request)
    for document in manifest.get("documents", []):
        if isinstance(document, dict) and document.get("document_id") == document_id:
            return document
    raise HTTPException(status_code=404, detail="document not found")
