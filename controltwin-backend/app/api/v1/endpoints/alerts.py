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


def _to_alert_response(alert: Alert) -> AlertResponse:
    return AlertResponse(
        id=alert.id,
        asset_id=alert.asset_id,
        site_id=alert.site_id,
        title=alert.title,
        description=alert.description,
        severity=alert.severity,
        category=alert.category,
        mitre_technique_id=alert.mitre_technique_id,
        mitre_technique_name=alert.mitre_technique_name,
        raw_data=alert.raw_data or {},
        metadata=alert.metadata_json or {},
        status=alert.status,
        triggered_at=alert.triggered_at,
        acknowledged_at=alert.acknowledged_at,
        resolved_at=alert.resolved_at,
        acknowledged_by=alert.acknowledged_by,
    )


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
) -> list[AlertResponse]:
    """List alerts."""
    service = AlertService(session)
    alerts = await service.list_alerts(site_id, asset_id, severity, status_value, category, page, size)
    return [_to_alert_response(alert) for alert in alerts]


@router.get("/{alert_id}", response_model=AlertResponse, dependencies=[Depends(require_permission(Permission.ALERT_READ))])
async def get_alert(alert_id: uuid.UUID, session: AsyncSession = Depends(get_session)) -> AlertResponse:
    """Get alert by id."""
    service = AlertService(session)
    alert = await service.get_or_404(alert_id)
    return _to_alert_response(alert)


@router.post("", response_model=AlertResponse, dependencies=[Depends(require_permission(Permission.ALERT_MANAGE))])
async def create_alert(payload: AlertCreate, session: AsyncSession = Depends(get_session)) -> AlertResponse:
    """Create alert."""
    service = AlertService(session)
    alert = await service.create_alert(payload)
    return _to_alert_response(alert)


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
) -> AlertResponse:
    """Acknowledge alert."""
    service = AlertService(session)
    alert = await service.acknowledge(alert_id, current_user.id)
    return _to_alert_response(alert)


@router.post(
    "/{alert_id}/resolve",
    response_model=AlertResponse,
    dependencies=[Depends(require_permission(Permission.ALERT_MANAGE))],
)
async def resolve_alert(
    alert_id: uuid.UUID,
    payload: AlertResolveRequest,
    session: AsyncSession = Depends(get_session),
) -> AlertResponse:
    """Resolve alert."""
    service = AlertService(session)
    alert = await service.resolve(alert_id, is_false_positive=payload.is_false_positive)
    return _to_alert_response(alert)
