"""API router for ControlTwin AI endpoints."""

from __future__ import annotations

from typing import Any

import redis.asyncio as aioredis
import structlog
from chromadb import HttpClient
from fastapi import APIRouter
from pydantic import BaseModel, Field
import ollama

from app.anomaly.detector import AnomalyDetector
from app.core.config import get_settings
from app.remediation.engine import RemediationEngine
from app.twin_state.engine import DigitalTwinEngine

settings = get_settings()
logger = structlog.get_logger("controltwin-ai.api")

router = APIRouter()
twin_engine = DigitalTwinEngine()
anomaly_detector = AnomalyDetector()
remediation_engine = RemediationEngine()


class TwinSyncRequest(BaseModel):
    """Request body for twin synchronization."""

    asset_id: str = Field(..., min_length=1)
    datapoints: list[dict[str, Any]] = Field(default_factory=list)


class TwinStateResponse(BaseModel):
    """Response body for twin state retrieval."""

    asset_id: str
    state: dict[str, Any]


class AnomalyDetectRequest(BaseModel):
    """Request body for anomaly detection."""

    asset_id: str
    datapoints: list[dict[str, Any]]


class AnomalyDetectResponse(BaseModel):
    """Response body for anomaly detection."""

    score: float
    is_anomaly: bool
    confidence: float
    technique: str


class RemediationSuggestRequest(BaseModel):
    """Request body for remediation suggestions."""

    alert: dict[str, Any]


class RemediationSuggestResponse(BaseModel):
    """Response body for remediation suggestions."""

    steps: list[str]
    mitre_ref: str
    confidence: float
    llm_explanation: str


@router.post("/twin/sync")
async def sync_twin(request: TwinSyncRequest) -> dict[str, Any]:
    """Sync an asset twin state with incoming datapoints."""
    try:
        return await twin_engine.sync_asset(asset_id=request.asset_id, datapoints=request.datapoints)
    except Exception as exc:
        logger.error("sync_twin_failed", error=str(exc))
        return {"asset_id": request.asset_id, "synced_points": 0, "error": str(exc)}


@router.get("/twin/{asset_id}/state", response_model=TwinStateResponse)
async def get_twin_state(asset_id: str) -> TwinStateResponse:
    """Get current digital twin state for an asset."""
    state = await twin_engine.get_twin_state(asset_id)
    return TwinStateResponse(asset_id=asset_id, state=state.get("state", {}))


@router.post("/anomaly/detect", response_model=AnomalyDetectResponse)
async def detect_anomaly(request: AnomalyDetectRequest) -> AnomalyDetectResponse:
    """Run anomaly detection for a given asset and datapoints."""
    result = await anomaly_detector.detect(asset_id=request.asset_id, datapoints=request.datapoints)
    return AnomalyDetectResponse(
        score=result.score,
        is_anomaly=result.is_anomaly,
        confidence=result.confidence,
        technique=result.technique,
    )


@router.get("/anomaly/{asset_id}/history")
async def anomaly_history(asset_id: str) -> dict[str, Any]:
    """Return anomaly history stored in Redis for an asset."""
    try:
        redis_client = aioredis.from_url(settings.REDIS_URL, decode_responses=True)
        items = await redis_client.lrange(f"anomaly:history:{asset_id}", 0, 99)
        await redis_client.close()
        return {"asset_id": asset_id, "history": items}
    except Exception as exc:
        return {"asset_id": asset_id, "history": [], "error": str(exc)}


@router.post("/remediation/suggest", response_model=RemediationSuggestResponse)
async def suggest_remediation(request: RemediationSuggestRequest) -> RemediationSuggestResponse:
    """Generate AI remediation suggestions for an alert."""
    suggestion = await remediation_engine.suggest(request.alert)
    return RemediationSuggestResponse(
        steps=suggestion.steps,
        mitre_ref=suggestion.mitre_ref,
        confidence=suggestion.confidence,
        llm_explanation=suggestion.llm_explanation,
    )


@router.get("/status")
async def status() -> dict[str, Any]:
    """Health status check for Redis, ChromaDB, and Ollama."""
    health = {"redis": False, "chromadb": False, "ollama": False}
    try:
        redis_client = aioredis.from_url(settings.REDIS_URL, decode_responses=True)
        await redis_client.ping()
        await redis_client.close()
        health["redis"] = True
    except Exception:
        health["redis"] = False

    try:
        chroma_client = HttpClient(host="localhost", port=8010)
        chroma_client.heartbeat()
        health["chromadb"] = True
    except Exception:
        health["chromadb"] = False

    try:
        ollama.list()
        health["ollama"] = True
    except Exception:
        health["ollama"] = False

    return {"status": "green" if all(health.values()) else "degraded", "components": health}


api_router = router
