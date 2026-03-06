"""FastAPI application entrypoint with lifespan hooks."""

from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.v1.router import api_router
from app.core.config import settings
from app.core.logging import setup_logging
from app.db.postgres import init_db
from app.services.kafka_service import KafkaProducerService

kafka_service = KafkaProducerService()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize and shutdown platform services."""
    setup_logging()
    await init_db()
    await kafka_service.start()
    app.state.kafka = kafka_service
    yield
    await kafka_service.stop()


app = FastAPI(title=settings.APP_NAME, debug=settings.APP_DEBUG, lifespan=lifespan)
app.include_router(api_router, prefix=settings.API_V1_PREFIX)
