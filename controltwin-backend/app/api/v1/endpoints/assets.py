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


def _to_asset_response(asset: Asset) -> AssetResponse:
    return AssetResponse(
        id=asset.id,
        site_id=asset.site_id,
        parent_id=asset.parent_id,
        name=asset.name,
        tag=asset.tag,
        description=asset.description,
        asset_type=asset.asset_type,
        protocol=asset.protocol,
        ip_address=asset.ip_address,
        port=asset.port,
        vendor=asset.vendor,
        model=asset.model,
        firmware_version=asset.firmware_version,
        purdue_level=asset.purdue_level,
        criticality=asset.criticality,
        status=asset.status,
        metadata=asset.metadata_json or {},
        is_active=asset.is_active,
        last_seen=asset.last_seen,
        created_at=asset.created_at,
        updated_at=asset.updated_at,
    )


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
) -> list[AssetResponse]:
    """List assets with filters."""
    service = AssetService(session)
    assets = await service.list_assets(site_id, asset_type, status_value, criticality, protocol, page, size)
    return [_to_asset_response(asset) for asset in assets]


@router.get("/{asset_id}", response_model=AssetResponse, dependencies=[Depends(require_permission(Permission.ASSET_READ))])
async def get_asset(asset_id: uuid.UUID, session: AsyncSession = Depends(get_session)) -> AssetResponse:
    """Get asset by id."""
    service = AssetService(session)
    asset = await service.get_or_404(asset_id)
    return _to_asset_response(asset)


@router.post("", response_model=AssetResponse, dependencies=[Depends(require_permission(Permission.ASSET_CREATE))])
async def create_asset(payload: AssetCreate, session: AsyncSession = Depends(get_session)) -> AssetResponse:
    """Create asset with unique tag per site validation."""
    service = AssetService(session)
    asset = await service.create_asset(payload)
    return _to_asset_response(asset)


@router.patch("/{asset_id}", response_model=AssetResponse, dependencies=[Depends(require_permission(Permission.ASSET_UPDATE))])
async def update_asset(asset_id: uuid.UUID, payload: AssetUpdate, session: AsyncSession = Depends(get_session)) -> AssetResponse:
    """Patch existing asset."""
    service = AssetService(session)
    asset = await service.update_asset(asset_id, payload)
    return _to_asset_response(asset)


@router.delete("/{asset_id}", dependencies=[Depends(require_permission(Permission.ASSET_DELETE))])
async def delete_asset(asset_id: uuid.UUID, session: AsyncSession = Depends(get_session)) -> dict[str, str]:
    """Soft delete asset only."""
    service = AssetService(session)
    await service.delete_asset(asset_id)
    return {"detail": "Asset soft-deleted"}
