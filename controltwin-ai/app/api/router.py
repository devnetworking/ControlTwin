"""ControlTwin AI — API Router
Aggregates all AI service endpoints under /api/v1/ai/
"""

import os
import subprocess
import time
from fastapi import APIRouter
from app.api import twin_state, anomaly, predictive, remediation, simulation

START_TIME = time.monotonic()

ai_router = APIRouter(prefix="/ai", tags=["ControlTwin AI"])

ai_router.include_router(
    twin_state.router,
    prefix="/twin-state",
    tags=["Twin State Engine"],
)
ai_router.include_router(
    anomaly.router,
    prefix="/anomaly",
    tags=["Anomaly Detection"],
)
ai_router.include_router(
    predictive.router,
    prefix="/predictive",
    tags=["Predictive Maintenance"],
)
ai_router.include_router(
    remediation.router,
    prefix="/remediation",
    tags=["AI Remediation"],
)
ai_router.include_router(
    simulation.router,
    prefix="/simulation",
    tags=["Twin Simulation"],
)


def _check_tcp(host: str, port: int) -> bool:
    import socket

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(0.5)
    try:
        return sock.connect_ex((host, port)) == 0
    finally:
        sock.close()


def _ollama_models() -> list:
    try:
        result = subprocess.run(
            ["ollama", "list"],
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode != 0:
            return []
        lines = [line.strip() for line in result.stdout.splitlines() if line.strip()]
        if not lines:
            return []
        models = []
        for line in lines[1:]:
            parts = line.split()
            if parts:
                models.append(parts[0])
        return models
    except Exception:
        return []


@ai_router.get("/status")
async def ai_status():
    ollama_host = os.environ.get("OLLAMA_HOST", "127.0.0.1")
    ollama_port = int(os.environ.get("OLLAMA_PORT", "11434"))
    chroma_host = os.environ.get("CHROMA_HOST", "127.0.0.1")
    chroma_port = int(os.environ.get("CHROMA_PORT", "8000"))
    redis_host = os.environ.get("REDIS_HOST", "127.0.0.1")
    redis_port = int(os.environ.get("REDIS_PORT", "6379"))

    models = _ollama_models()
    components = {
        "ollama": _check_tcp(ollama_host, ollama_port),
        "chromadb": _check_tcp(chroma_host, chroma_port),
        "redis": _check_tcp(redis_host, redis_port),
        "ml_models_loaded": len(models) > 0,
    }

    return {
        "service": "controltwin-ai",
        "version": "1.0.0",
        "components": components,
        "models_available": models,
        "uptime_seconds": round(time.monotonic() - START_TIME, 3),
    }


router = ai_router
api_router = ai_router
