"""Alert endpoints."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user
from app.auth.rbac import Permission, require_permission
from app.db.postgres import get_session
from app.models.models import Alert, User
from app.schemas.schemas import AlertAcknowledgeRequest, AlertCreate, AlertResolveRequest, AlertResponse
from app.services.alert_service import AlertService

router = APIRouter(prefix="/alerts", tags=["alerts"])


@router.get("", response_model=list[AlertResponse], dependencies=[Depends(require_permission(Permission.ALERT_READ))])
async def list_alerts(
    site_id: uuid.UUID | None = None,
    asset_id: uuid.UUID | None = None,
    severity: str | None = None,
    status_value: str | None = Query(default=None, alias="status"),
    category: str | None = None,
    page: int = 1,
    size: int = 20,
    session: AsyncSession = Depends(get_session),
) -> list[Alert]:
    """List alerts."""
    service = AlertService(session)
    return await service.list_alerts(site_id, asset_id, severity, status_value, category, page, size)


@router.get("/{alert_id}", response_model=AlertResponse, dependencies=[Depends(require_permission(Permission.ALERT_READ))])
async def get_alert(alert_id: uuid.UUID, session: AsyncSession = Depends(get_session)) -> Alert:
    """Get alert by id."""
    service = AlertService(session)
    return await service.get_or_404(alert_id)


@router.post("", response_model=AlertResponse, dependencies=[Depends(require_permission(Permission.ALERT_MANAGE))])
async def create_alert(payload: AlertCreate, session: AsyncSession = Depends(get_session)) -> Alert:
    """Create alert."""
    service = AlertService(session)
    return await service.create_alert(payload)


@router.post(
    "/{alert_id}/acknowledge",
    response_model=AlertResponse,
    dependencies=[Depends(require_permission(Permission.ALERT_ACKNOWLEDGE))],
)
async def acknowledge_alert(
    alert_id: uuid.UUID,
    _: AlertAcknowledgeRequest,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> Alert:
    """Acknowledge alert."""
    service = AlertService(session)
    return await service.acknowledge(alert_id, current_user.id)


@router.post(
    "/{alert_id}/resolve",
    response_model=AlertResponse,
    dependencies=[Depends(require_permission(Permission.ALERT_MANAGE))],
)
async def resolve_alert(
    alert_id: uuid.UUID,
    payload: AlertResolveRequest,
    session: AsyncSession = Depends(get_session),
) -> Alert:
    """Resolve alert."""
    service = AlertService(session)
    return await service.resolve(alert_id, is_false_positive=payload.is_false_positive)
