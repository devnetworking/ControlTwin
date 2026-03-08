"""Alert service for alert lifecycle management."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.models import Alert, AlertStatus
from app.schemas.schemas import AlertCreate


class AlertService:
    """Service handling alert operations."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def list_alerts(
        self,
        site_id: uuid.UUID | None = None,
        asset_id: uuid.UUID | None = None,
        severity: str | None = None,
        status_value: str | None = None,
        category: str | None = None,
        page: int = 1,
        size: int = 20,
    ) -> list[Alert]:
        """List alerts with filters."""
        filters = []
        if site_id:
            filters.append(Alert.site_id == site_id)
        if asset_id:
            filters.append(Alert.asset_id == asset_id)
        if severity:
            filters.append(Alert.severity == severity)
        if status_value:
            filters.append(Alert.status == status_value)
        if category:
            filters.append(Alert.category == category)

        stmt = select(Alert)
        if filters:
            stmt = stmt.where(and_(*filters))
        stmt = stmt.offset((page - 1) * size).limit(size).order_by(Alert.triggered_at.desc())
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_or_404(self, alert_id: uuid.UUID) -> Alert:
        """Get alert by id or raise 404."""
        result = await self.session.execute(select(Alert).where(Alert.id == alert_id))
        alert = result.scalar_one_or_none()
        if not alert:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Alert not found")
        return alert

    async def create_alert(self, payload: AlertCreate) -> Alert:
        """Create alert."""
        alert = Alert(
            asset_id=payload.asset_id,
            site_id=payload.site_id,
            title=payload.title,
            description=payload.description,
            severity=payload.severity,
            category=payload.category,
            mitre_technique_id=payload.mitre_technique_id,
            mitre_technique_name=payload.mitre_technique_name,
            status=AlertStatus.OPEN,
            triggered_at=datetime.now(timezone.utc),
            raw_data=payload.raw_data,
            metadata_json=payload.metadata,
        )
        self.session.add(alert)
        await self.session.commit()
        await self.session.refresh(alert)
        return alert

    async def acknowledge(self, alert_id: uuid.UUID, user_id: uuid.UUID) -> Alert:
        """Acknowledge an alert."""
        alert = await self.get_or_404(alert_id)
        alert.status = AlertStatus.ACKNOWLEDGED
        alert.acknowledged_at = datetime.now(timezone.utc)
        alert.acknowledged_by = user_id
        await self.session.commit()
        await self.session.refresh(alert)
        return alert

    async def resolve(self, alert_id: uuid.UUID, is_false_positive: bool = False) -> Alert:
        """Resolve an alert."""
        alert = await self.get_or_404(alert_id)
        alert.status = AlertStatus.FALSE_POSITIVE if is_false_positive else AlertStatus.RESOLVED
        alert.resolved_at = datetime.now(timezone.utc)
        await self.session.commit()
        await self.session.refresh(alert)
        return alert
