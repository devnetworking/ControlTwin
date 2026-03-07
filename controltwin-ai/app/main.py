from contextlib import asynccontextmanager
from fastapi import FastAPI

from app.api.router import api_router
from app.core.config import get_settings
from app.core.logging import setup_logging, get_logger


settings = get_settings()
setup_logging(settings.log_level)
logger = get_logger("controltwin-ai")


@asynccontextmanager
async def lifespan(_: FastAPI):
    logger.info("starting controltwin-ai service", extra={"event": "startup"})
    yield
    logger.info("stopping controltwin-ai service", extra={"event": "shutdown"})


app = FastAPI(
    title="ControlTwin AI",
    version="1.0.0",
    lifespan=lifespan,
)

app.include_router(api_router, prefix="/api/v1/ai")


@app.get("/health")
async def health():
    return {"status": "ok", "service": "controltwin-ai", "port": settings.controltwin_ai_port}
