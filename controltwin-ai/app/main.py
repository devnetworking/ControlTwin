"""Main FastAPI application entrypoint for the ControlTwin AI microservice."""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncIterator

import redis.asyncio as aioredis
import structlog
from chromadb import HttpClient
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import ollama

from app.api.router import api_router
from app.core.config import get_settings

settings = get_settings()
structlog.configure()
logger = structlog.get_logger("controltwin-ai")


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    """Initialize external service clients at startup and close resources on shutdown."""
    redis_client: aioredis.Redis | None = None
    chroma_client: HttpClient | None = None

    try:
        redis_client = aioredis.from_url(settings.REDIS_URL, decode_responses=True)
        await redis_client.ping()
        logger.info("redis_connected", url=settings.REDIS_URL)

        chroma_client = HttpClient(host="localhost", port=8010)
        chroma_client.heartbeat()
        logger.info("chromadb_connected", url=settings.CHROMADB_URL)

        ollama.list()
        logger.info("ollama_healthy", url=settings.OLLAMA_URL, model=settings.MODEL_PRIMARY)

        app.state.redis = redis_client
        app.state.chroma = chroma_client
        logger.info("ai_service_startup_complete")
        yield
    except Exception as exc:
        logger.error("ai_service_startup_failed", error=str(exc))
        raise
    finally:
        if redis_client is not None:
            await redis_client.close()
        logger.info("ai_service_shutdown_complete")


app = FastAPI(
    title="ControlTwin AI Service",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:8000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api/v1/ai")
