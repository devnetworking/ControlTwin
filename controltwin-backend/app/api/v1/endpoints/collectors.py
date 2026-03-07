"""Collector endpoints."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.rbac import Permission, require_permission
from app.db.postgres import get_session
from app.models.models import Collector
from app.schemas.schemas import CollectorCreate, CollectorResponse

router = APIRouter(prefix="/collectors", tags=["collectors"])


@router.get("", response_model=list[CollectorResponse], dependencies=[Depends(require_permission(Permission.COLLECTOR_READ))])
async def list_collectors(session: AsyncSession = Depends(get_session)) -> list[Collector]:
    """List collectors."""
    result = await session.execute(select(Collector))
    return list(result.scalars().all())


@router.get(
    "/{collector_id}",
    response_model=CollectorResponse,
    dependencies=[Depends(require_permission(Permission.COLLECTOR_READ))],
)
async def get_collector(collector_id: uuid.UUID, session: AsyncSession = Depends(get_session)) -> Collector:
    """Get collector by id."""
    result = await session.execute(select(Collector).where(Collector.id == collector_id))
    collector = result.scalar_one_or_none()
    if not collector:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Collector not found")
    return collector


@router.post("", response_model=CollectorResponse, dependencies=[Depends(require_permission(Permission.COLLECTOR_MANAGE))])
async def create_collector(payload: CollectorCreate, session: AsyncSession = Depends(get_session)) -> Collector:
    """Create collector."""
    collector = Collector(
        site_id=payload.site_id,
        name=payload.name,
        protocol=payload.protocol,
        host=payload.host,
        port=payload.port,
        config=payload.config,
        poll_interval_ms=payload.poll_interval_ms,
        is_active=payload.is_active,
    )
    session.add(collector)
    await session.commit()
    await session.refresh(collector)
    return collector
