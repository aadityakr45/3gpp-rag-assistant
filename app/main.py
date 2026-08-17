"""FastAPI application factory."""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.chat import ChatService
from app.api.chat import router as chat_router
from app.api.documents import router as documents_router
from app.api.health import router as health_router
from app.api.ingestion import router as ingestion_router
from app.core.config import Settings
from app.core.logging import configure_logging
from app.generation.generator import AbstainingGenerator, ProviderGenerator
from app.generation.providers import GeminiProvider
from app.retrieval.indexing import load_retriever


def create_app(settings: Settings | None = None) -> FastAPI:
    configure_logging()
    application = FastAPI(title="TeleRAG", version="0.1.0")
    application.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:5173"],
        allow_credentials=False,
        allow_methods=["GET", "POST"],
        allow_headers=["Content-Type"],
    )
    application.state.settings = settings or Settings.from_environment()
    active_settings = application.state.settings
    retriever = None
    try:
        retriever = load_retriever(
            active_settings,
            allow_hash_fallback=active_settings.allow_hash_fallback,
        )
    except (FileNotFoundError, RuntimeError, ValueError):
        # The API stays healthy before ingestion; chat will abstain safely.
        retriever = None
    generator = AbstainingGenerator()
    if active_settings.llm_provider.lower() == "gemini" and active_settings.llm_api_key:
        try:
            generator = ProviderGenerator(
                GeminiProvider(active_settings.llm_api_key, active_settings.llm_model),
                "gemini",
            )
        except (RuntimeError, ValueError):
            generator = AbstainingGenerator()
    application.state.chat_service = ChatService(retriever, generator)
    application.include_router(health_router)
    application.include_router(chat_router)
    application.include_router(ingestion_router)
    application.include_router(documents_router)
    return application


app = create_app()
