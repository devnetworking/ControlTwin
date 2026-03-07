"""Health check endpoints."""

from __future__ import annotations

from fastapi import APIRouter

from app.db.influxdb import InfluxRepository
from app.db.postgres import check_db_health
from app.schemas.schemas import HealthComponent, HealthResponse

router = APIRouter(prefix="/health", tags=["health"])


@router.get("", response_model=HealthResponse)
async def health() -> HealthResponse:
    """Check health of PostgreSQL and InfluxDB."""
    pg_ok, pg_detail = await check_db_health()

    influx = InfluxRepository()
    try:
        influx_ok, influx_detail = influx.check_health()
    finally:
        influx.close()

    overall = "healthy" if pg_ok and influx_ok else "degraded"
    return HealthResponse(
        status=overall,
        components={
            "postgresql": HealthComponent(status="healthy" if pg_ok else "degraded", detail=pg_detail),
            "influxdb": HealthComponent(status="healthy" if influx_ok else "degraded", detail=influx_detail),
        },
    )
