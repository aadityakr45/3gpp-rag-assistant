"""Health endpoint."""

from __future__ import annotations

from fastapi import APIRouter, Request

router = APIRouter()


@router.get("/health")
def health(request: Request) -> dict[str, object]:
    service = getattr(request.app.state, "chat_service", None)
    return {
        "status": "ok",
        "retrieval_available": bool(service and service.retriever),
    }
