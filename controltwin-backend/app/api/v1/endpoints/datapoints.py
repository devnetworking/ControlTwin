"""DataPoint endpoints."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.rbac import Permission, require_permission
from app.db.influxdb import InfluxRepository
from app.db.postgres import get_session
from app.models.models import DataPoint
from app.schemas.schemas import DataPointCreate, DataPointQueryRequest, DataPointResponse

router = APIRouter(prefix="/datapoints", tags=["datapoints"])


@router.get("", response_model=list[DataPointResponse], dependencies=[Depends(require_permission(Permission.DATAPOINT_READ))])
async def list_datapoints(asset_id: uuid.UUID | None = None, session: AsyncSession = Depends(get_session)) -> list[DataPoint]:
    """List datapoints by optional asset filter."""
    stmt = select(DataPoint)
    if asset_id:
        stmt = stmt.where(DataPoint.asset_id == asset_id)
    result = await session.execute(stmt)
    return list(result.scalars().all())


@router.post("", response_model=DataPointResponse, dependencies=[Depends(require_permission(Permission.DATAPOINT_WRITE))])
async def create_datapoint(payload: DataPointCreate, session: AsyncSession = Depends(get_session)) -> DataPoint:
    """Create datapoint with enforced read-only design."""
    datapoint = DataPoint(
        asset_id=payload.asset_id,
        name=payload.name,
        tag=payload.tag,
        data_type=payload.data_type,
        unit=payload.unit,
        engineering_low=payload.engineering_low,
        engineering_high=payload.engineering_high,
        alarm_low_low=payload.alarm_low_low,
        alarm_low=payload.alarm_low,
        alarm_high=payload.alarm_high,
        alarm_high_high=payload.alarm_high_high,
        sample_interval_ms=payload.sample_interval_ms,
        is_writable=False,
        metadata_json=payload.metadata,
    )
    session.add(datapoint)
    await session.commit()
    await session.refresh(datapoint)
    return datapoint


@router.post("/query", dependencies=[Depends(require_permission(Permission.DATAPOINT_READ))])
async def query_datapoints(payload: DataPointQueryRequest) -> dict[str, list[dict]]:
    """Query datapoint timeseries from InfluxDB."""
    influx = InfluxRepository()
    try:
        records = influx.query_measurements(
            bucket=influx.history_bucket,
            data_point_ids=[str(dp_id) for dp_id in payload.data_point_ids],
            start=payload.start,
            stop=payload.stop,
            aggregate_window=payload.aggregate_window,
            aggregate_fn=payload.aggregate_fn,
        )
        return {"records": records}
    finally:
        influx.close()


@router.get("/{datapoint_id}/latest", dependencies=[Depends(require_permission(Permission.DATAPOINT_READ))])
async def latest_datapoint(datapoint_id: uuid.UUID) -> dict:
    """Get latest datapoint value from InfluxDB."""
    influx = InfluxRepository()
    try:
        latest = influx.get_last_value(influx.realtime_bucket, str(datapoint_id))
        return {"latest": latest}
    finally:
        influx.close()
