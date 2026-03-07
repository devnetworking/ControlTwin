"""Asset service for CRUD operations with soft-delete semantics."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.models import Asset
from app.schemas.schemas import AssetCreate, AssetUpdate


class AssetService:
    """Service for asset operations."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def list_assets(
        self,
        site_id: uuid.UUID | None = None,
        asset_type: str | None = None,
        status_value: str | None = None,
        criticality: str | None = None,
        protocol: str | None = None,
        page: int = 1,
        size: int = 20,
    ) -> list[Asset]:
        """List assets with filters and pagination."""
        filters = [Asset.is_active.is_(True)]
        if site_id:
            filters.append(Asset.site_id == site_id)
        if asset_type:
            filters.append(Asset.asset_type == asset_type)
        if status_value:
            filters.append(Asset.status == status_value)
        if criticality:
            filters.append(Asset.criticality == criticality)
        if protocol:
            filters.append(Asset.protocol == protocol)

        stmt = select(Asset).where(and_(*filters)).offset((page - 1) * size).limit(size)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_or_404(self, asset_id: uuid.UUID) -> Asset:
        """Get asset or raise 404."""
        result = await self.session.execute(select(Asset).where(Asset.id == asset_id, Asset.is_active.is_(True)))
        asset = result.scalar_one_or_none()
        if not asset:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Asset not found")
        return asset

    async def create_asset(self, payload: AssetCreate) -> Asset:
        """Create asset with unique site+tag validation."""
        duplicate = await self.session.execute(
            select(Asset).where(
                Asset.site_id == payload.site_id,
                Asset.tag == payload.tag,
                Asset.is_active.is_(True),
            )
        )
        if duplicate.scalar_one_or_none():
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Asset tag already exists in site")

        asset = Asset(
            site_id=payload.site_id,
            parent_id=payload.parent_id,
            name=payload.name,
            tag=payload.tag,
            description=payload.description,
            asset_type=payload.asset_type,
            protocol=payload.protocol,
            ip_address=payload.ip_address,
            port=payload.port,
            vendor=payload.vendor,
            model=payload.model,
            firmware_version=payload.firmware_version,
            purdue_level=payload.purdue_level,
            criticality=payload.criticality,
            status=payload.status,
            metadata_json=payload.metadata,
            is_active=True,
        )
        self.session.add(asset)
        await self.session.commit()
        await self.session.refresh(asset)
        return asset

    async def update_asset(self, asset_id: uuid.UUID, payload: AssetUpdate) -> Asset:
        """Update mutable fields of an asset."""
        asset = await self.get_or_404(asset_id)
        data = payload.model_dump(exclude_unset=True)
        if "metadata" in data:
            data["metadata_json"] = data.pop("metadata")
        for key, value in data.items():
            setattr(asset, key, value)
        asset.updated_at = datetime.now(timezone.utc)
        await self.session.commit()
        await self.session.refresh(asset)
        return asset

    async def delete_asset(self, asset_id: uuid.UUID) -> None:
        """Soft delete asset only."""
        asset = await self.get_or_404(asset_id)
        asset.is_active = False
        asset.updated_at = datetime.now(timezone.utc)
        await self.session.commit()
