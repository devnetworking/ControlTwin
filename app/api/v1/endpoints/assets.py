"""Asset endpoints."""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.rbac import Permission, require_permission
from app.db.postgres import get_session
from app.models.models import Asset
from app.schemas.schemas import AssetCreate, AssetResponse, AssetUpdate
from app.services.asset_service import AssetService

router = APIRouter(prefix="/assets", tags=["assets"])


@router.get("", response_model=list[AssetResponse], dependencies=[Depends(require_permission(Permission.ASSET_READ))])
async def list_assets(
    site_id: uuid.UUID | None = None,
    asset_type: str | None = None,
    status_value: str | None = Query(default=None, alias="status"),
    criticality: str | None = None,
    protocol: str | None = None,
    page: int = 1,
    size: int = 20,
    session: AsyncSession = Depends(get_session),
) -> list[Asset]:
    """List assets with filters."""
    service = AssetService(session)
    return await service.list_assets(site_id, asset_type, status_value, criticality, protocol, page, size)


@router.get("/{asset_id}", response_model=AssetResponse, dependencies=[Depends(require_permission(Permission.ASSET_READ))])
async def get_asset(asset_id: uuid.UUID, session: AsyncSession = Depends(get_session)) -> Asset:
    """Get asset by id."""
    service = AssetService(session)
    return await service.get_or_404(asset_id)


@router.post("", response_model=AssetResponse, dependencies=[Depends(require_permission(Permission.ASSET_CREATE))])
async def create_asset(payload: AssetCreate, session: AsyncSession = Depends(get_session)) -> Asset:
    """Create asset with unique tag per site validation."""
    service = AssetService(session)
    return await service.create_asset(payload)


@router.patch("/{asset_id}", response_model=AssetResponse, dependencies=[Depends(require_permission(Permission.ASSET_UPDATE))])
async def update_asset(asset_id: uuid.UUID, payload: AssetUpdate, session: AsyncSession = Depends(get_session)) -> Asset:
    """Patch existing asset."""
    service = AssetService(session)
    return await service.update_asset(asset_id, payload)


@router.delete("/{asset_id}", dependencies=[Depends(require_permission(Permission.ASSET_DELETE))])
async def delete_asset(asset_id: uuid.UUID, session: AsyncSession = Depends(get_session)) -> dict[str, str]:
    """Soft delete asset only."""
    service = AssetService(session)
    await service.delete_asset(asset_id)
    return {"detail": "Asset soft-deleted"}
